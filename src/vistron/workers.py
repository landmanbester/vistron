"""
Ray workers for dataset processing.
"""

import logging
from typing import Dict, List, Any

import numpy as np
import ray
import xarray as xr

logger = logging.getLogger(__name__)


@ray.remote
class DatasetWorker:
    """Ray actor for handling dataset operations."""
    
    def __init__(self, zarr_path: str):
        self.dataset = None
        self.zarr_path = zarr_path
        self.load_dataset()
    
    def load_dataset(self):
        """Load the zarr dataset."""
        try:
            self.dataset = xr.open_zarr(self.zarr_path, chunks='auto')
            logger.info(f"Ray worker loaded dataset from {self.zarr_path}")
            return True
        except Exception as e:
            logger.error(f"Ray worker failed to load dataset: {e}")
            return False
    
    def _get_coord_info(self, coord):
        """Extract coordinate information with graceful handling of non-numeric types."""
        coord_info = {
            'values': coord.values.tolist() if coord.size < 1000 else coord.values[::max(1, coord.size//100)].tolist(),
            'size': int(coord.size),
            'dtype': str(coord.dtype),
            'is_numeric': False
        }
        
        # Try to determine if coordinate is numeric and get min/max
        try:
            # Check if the coordinate is numeric
            if np.issubdtype(coord.dtype, np.number):
                coord_info['is_numeric'] = True
                coord_info['min'] = float(coord.min().values)
                coord_info['max'] = float(coord.max().values)
            else:
                # Non-numeric coordinate (strings, datetime, etc.)
                coord_info['is_numeric'] = False
                coord_info['min'] = None
                coord_info['max'] = None
                # For string coordinates, provide some sample values
                if coord.size > 0:
                    sample_size = min(5, coord.size)
                    coord_info['sample_values'] = coord.values[:sample_size].tolist()
                    
        except (ValueError, TypeError) as e:
            # Fallback for any problematic coordinates
            logger.warning(f"Could not process coordinate {coord.name}: {e}")
            coord_info['is_numeric'] = False
            coord_info['min'] = None
            coord_info['max'] = None
            coord_info['sample_values'] = ["<unable to read>"]
            
        return coord_info
    
    def get_dataset_info(self):
        """Extract dataset metadata."""
        if self.dataset is None:
            return None
            
        return {
            'dimensions': list(self.dataset.dims.keys()),
            'dimension_sizes': {dim: int(size) for dim, size in self.dataset.dims.items()},
            'data_vars': list(self.dataset.data_vars.keys()),
            'coords': {name: self._get_coord_info(coord) for name, coord in self.dataset.coords.items()},
            'shape': [int(self.dataset.dims[dim]) for dim in self.dataset.dims.keys()],
            'data_var_info': {var: {
                'dtype': str(self.dataset[var].dtype),
                'shape': list(self.dataset[var].shape)
            } for var in self.dataset.data_vars.keys()}
        }
    
    def get_data_slice(self, data_var: str, selection: Dict, downsample_factor: int = 1):
        """Get a data slice with optional downsampling."""
        if self.dataset is None:
            raise ValueError("Dataset not loaded")
        
        try:
            # Get the data slice
            data_slice = self.dataset[data_var].isel(selection)
            
            # Apply downsampling if requested
            if downsample_factor > 1:
                # Downsample each displayed dimension
                new_selection = {}
                for dim, sel in selection.items():
                    if isinstance(sel, slice) and sel == slice(None):
                        # This is a displayed dimension, downsample it
                        dim_size = self.dataset.dims[dim]
                        new_selection[dim] = slice(0, dim_size, downsample_factor)
                    else:
                        new_selection[dim] = sel
                
                data_slice = self.dataset[data_var].isel(new_selection)
            
            # Convert to numpy and handle NaN values
            data_array = data_slice.values
            data_array = np.nan_to_num(data_array, nan=0.0)
            
            return data_array
            
        except Exception as e:
            logger.error(f"Error getting data slice: {e}")
            raise
    
    def get_coordinates(self, axis_names: List[str], downsample_factor: int = 1):
        """Get coordinate values for specified axes."""
        coords = {}
        for axis in axis_names:
            if axis in self.dataset.coords:
                coord_values = self.dataset.coords[axis].values
                if downsample_factor > 1:
                    coord_values = coord_values[::downsample_factor]
                coords[axis] = coord_values.tolist()
        return coords


@ray.remote
def process_animation_frame(
    worker_ref, 
    data_var: str, 
    selection: Dict, 
    animate_axis: str, 
    frame_index: int, 
    downsample_factor: int = 1
) -> Dict:
    """Process a single animation frame."""
    try:
        # Update selection for this frame
        frame_selection = selection.copy()
        frame_selection[animate_axis] = frame_index
        
        # Get data slice
        data_array = ray.get(worker_ref.get_data_slice.remote(
            data_var, frame_selection, downsample_factor
        ))
        
        # Get coordinate value for this frame
        coords = ray.get(worker_ref.get_coordinates.remote([animate_axis]))
        animate_value = coords[animate_axis][frame_index] if downsample_factor == 1 else coords[animate_axis][frame_index // downsample_factor]
        
        return {
            "type": "frame",
            "frame_index": frame_index,
            "data": data_array.tolist(),
            "animate_axis_value": float(animate_value),
            "downsample_factor": downsample_factor
        }
        
    except Exception as e:
        logger.error(f"Error processing frame {frame_index}: {e}")
        return {"error": f"Frame processing error: {str(e)}"}