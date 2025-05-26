"""
FastAPI server implementation for Vistron.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import ray
import xarray as xr
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from vistron.config import VistronConfig
from vistron.workers import DatasetWorker, process_animation_frame
from vistron.utils import calculate_optimal_downsample, get_downsample_options
from vistron.websocket import ConnectionManager

import asyncio
import json
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
dataset_worker = None
dataset_info = None
config = None


def create_app(app_config: VistronConfig) -> FastAPI:
    """Create and configure the FastAPI application."""
    global config
    config = app_config
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global dataset_worker, dataset_info
        
        # Startup
        logger.info(f"Attempting to load dataset from: {config.zarr_path}")
        dataset_worker, dataset_info = await load_dataset(config)
        yield
        
        # Shutdown
        if ray.is_initialized():
            ray.shutdown()
            logger.info("Ray shutdown complete")
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Vistron",
        description="Ray-Powered N-Dimensional Data Animator",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # Add routes
    add_routes(app)
    
    return app


async def load_dataset(config: VistronConfig) -> Tuple[Any, Optional[Dict]]:
    """Initialize Ray and load the dataset."""
    try:
        # Initialize Ray if not already done
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True, **config.ray_init_kwargs)
            logger.info("Ray initialized successfully")
        
        # Create dataset worker
        worker = DatasetWorker.remote(str(config.zarr_path))
        
        # Get dataset info
        info = ray.get(worker.get_dataset_info.remote())
        
        if info is None:
            logger.error("Failed to load dataset")
            return None, None
        
        logger.info(f"Dataset loaded successfully!")
        logger.info(f"Dimensions: {info['dimensions']}")
        logger.info(f"Shape: {info['shape']}")
        logger.info(f"Data variables: {info['data_vars']}")
        
        return worker, info
        
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        return None, None


def add_routes(app: FastAPI):
    """Add all routes to the FastAPI app."""
    
    manager = ConnectionManager()
    
    @app.get("/")
    async def get_index():
        """Serve the main HTML interface."""
        html_path = Path(__file__).parent / "templates" / "index.html"
        if html_path.exists():
            return HTMLResponse(content=html_path.read_text(), media_type="text/html")
        else:
            return HTMLResponse(
                content="<h1>Vistron Server</h1><p>Template not found. Please check installation.</p>",
                media_type="text/html"
            )
    
    @app.get("/dataset-info")
    async def get_dataset_info():
        """Return metadata about the loaded dataset."""
        if dataset_info is None:
            return {"error": "No dataset loaded"}
        
        # Add downsampling options for each dimension
        enhanced_info = dataset_info.copy()
        enhanced_info['downsample_options'] = {}
        
        for dim, size in dataset_info['dimension_sizes'].items():
            enhanced_info['downsample_options'][dim] = get_downsample_options(size)
        
        return enhanced_info
    
    @app.get("/data-slice")
    async def get_data_slice(
        data_var: str,
        axis1: str,
        axis2: str,
        other_indices: str = "{}",
        downsample_factor: int = Query(1, ge=1, le=16, description="Downsampling factor for performance"),
        auto_downsample: bool = Query(False, description="Automatically calculate optimal downsampling")
    ):
        """Get a 2D slice of the data for visualization with optional downsampling."""
        if dataset_worker is None:
            return {"error": "No dataset loaded"}
        
        try:
            other_idx = json.loads(other_indices)
            
            # Create selection dictionary
            selection = {}
            display_shape = []
            
            for dim in dataset_info['dimensions']:
                if dim == axis1:
                    selection[dim] = slice(None)
                    display_shape.append(dataset_info['dimension_sizes'][dim])
                elif dim == axis2:
                    selection[dim] = slice(None)
                    display_shape.append(dataset_info['dimension_sizes'][dim])
                elif dim in other_idx:
                    selection[dim] = other_idx[dim]
                else:
                    selection[dim] = 0
            
            # Auto-calculate downsampling if requested
            if auto_downsample:
                downsample_factor = calculate_optimal_downsample(
                    tuple(display_shape), 
                    config.default_downsample_threshold
                )
                logger.info(f"Auto-calculated downsample factor: {downsample_factor}")
            
            # Get the data slice using Ray
            data_array = ray.get(dataset_worker.get_data_slice.remote(
                data_var, selection, downsample_factor
            ))
            
            # Get coordinate values
            coords = ray.get(dataset_worker.get_coordinates.remote(
                [axis1, axis2], downsample_factor
            ))
            
            return {
                "data": data_array.tolist(),
                "coord1": coords.get(axis1, []),
                "coord2": coords.get(axis2, []),
                "axis1": axis1,
                "axis2": axis2,
                "shape": data_array.shape,
                "min_val": float(np.min(data_array)),
                "max_val": float(np.max(data_array)),
                "downsample_factor": downsample_factor,
                "original_shape": display_shape
            }
            
        except Exception as e:
            logger.error(f"Error in get_data_slice: {e}")
            return {"error": f"Error getting data slice: {str(e)}"}
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message["type"] == "animate":
                    await animate_data(websocket, message["params"], manager)
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(websocket)


async def animate_data(websocket: WebSocket, params: Dict[str, Any], manager: ConnectionManager):
    """Stream animation frames via WebSocket using Ray for parallel processing."""
    if dataset_worker is None:
        await manager.send_personal_message(
            json.dumps({"error": "No dataset loaded"}), websocket
        )
        return
    
    try:
        data_var = params["data_var"]
        axis1 = params["axis1"]
        axis2 = params["axis2"]
        animate_axis = params["animate_axis"]
        other_indices = params.get("other_indices", {})
        fps = params.get("fps", config.default_fps)
        downsample_factor = params.get("downsample_factor", 1)
        batch_size = min(params.get("batch_size", 4), config.max_batch_size)
        
        # Create base selection
        selection = {}
        for dim in dataset_info['dimensions']:
            if dim == axis1:
                selection[dim] = slice(None)
            elif dim == axis2:
                selection[dim] = slice(None)
            elif dim == animate_axis:
                selection[dim] = 0  # Will be updated per frame
            elif dim in other_indices:
                selection[dim] = other_indices[dim]
            else:
                selection[dim] = 0
        
        # Get animation axis size
        axis_size = dataset_info['dimension_sizes'][animate_axis]
        total_frames = axis_size // downsample_factor if downsample_factor > 1 else axis_size
        
        # Send animation start message
        await manager.send_personal_message(
            json.dumps({
                "type": "animation_start",
                "total_frames": total_frames,
                "downsample_factor": downsample_factor
            }), 
            websocket
        )
        
        # Process frames in batches for better performance
        for batch_start in range(0, axis_size, batch_size):
            batch_end = min(batch_start + batch_size, axis_size)
            frame_indices = list(range(batch_start, batch_end, downsample_factor))
            
            # Process batch in parallel using Ray
            frame_futures = []
            for frame_idx in frame_indices:
                future = process_animation_frame.remote(
                    dataset_worker, data_var, selection, animate_axis, 
                    frame_idx, downsample_factor
                )
                frame_futures.append((frame_idx, future))
            
            # Get results and send frames
            for frame_idx, future in frame_futures:
                try:
                    frame_data = ray.get(future)
                    if "error" in frame_data:
                        await manager.send_personal_message(
                            json.dumps(frame_data), websocket
                        )
                        return
                    
                    frame_data["total_frames"] = total_frames
                    await manager.send_personal_message(
                        json.dumps(frame_data), websocket
                    )
                    
                    # Control frame rate
                    await asyncio.sleep(1.0 / fps)
                    
                except Exception as e:
                    logger.error(f"Error processing frame {frame_idx}: {e}")
                    await manager.send_personal_message(
                        json.dumps({"error": f"Frame {frame_idx} error: {str(e)}"}),
                        websocket
                    )
        
        # Send animation complete message
        await manager.send_personal_message(
            json.dumps({"type": "animation_complete"}), websocket
        )
        
    except Exception as e:
        logger.error(f"Animation error: {e}")
        await manager.send_personal_message(
            json.dumps({"error": f"Animation error: {str(e)}"}), websocket
        )