"""
Configuration management for Vistron.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class VistronConfig:
    """Configuration for the Vistron application."""
    
    # Dataset configuration
    zarr_path: Path
    
    # Ray configuration
    ray_address: Optional[str] = None
    ray_dashboard_port: int = 8265
    max_workers: Optional[int] = None
    memory_limit: Optional[str] = None
    
    # Performance configuration
    default_downsample_threshold: int = 500
    max_batch_size: int = 16
    default_fps: int = 10
    
    # Server configuration
    websocket_timeout: int = 300  # seconds
    max_frame_size: int = 100 * 1024 * 1024  # 100MB
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.zarr_path.exists():
            raise ValueError(f"Zarr dataset not found: {self.zarr_path}")
        
        if self.ray_dashboard_port < 1 or self.ray_dashboard_port > 65535:
            raise ValueError(f"Invalid Ray dashboard port: {self.ray_dashboard_port}")
        
        if self.max_workers is not None and self.max_workers < 1:
            raise ValueError(f"Invalid max_workers: {self.max_workers}")
    
    @property
    def ray_init_kwargs(self) -> dict:
        """Get Ray initialization kwargs from config."""
        kwargs = {}
        
        if self.ray_address:
            kwargs["address"] = self.ray_address
        else:
            # Local cluster configuration
            kwargs["dashboard_port"] = self.ray_dashboard_port
            
            if self.max_workers:
                kwargs["num_cpus"] = self.max_workers
            
            if self.memory_limit:
                kwargs["object_store_memory"] = self._parse_memory_limit(self.memory_limit)
        
        return kwargs
    
    def _parse_memory_limit(self, memory_str: str) -> int:
        """Parse memory limit string to bytes."""
        memory_str = memory_str.upper().strip()
        
        if memory_str.endswith("GB"):
            return int(float(memory_str[:-2]) * 1024**3)
        elif memory_str.endswith("MB"):
            return int(float(memory_str[:-2]) * 1024**2)
        elif memory_str.endswith("KB"):
            return int(float(memory_str[:-2]) * 1024)
        elif memory_str.endswith("B"):
            return int(memory_str[:-1])
        else:
            # Assume bytes if no unit
            return int(memory_str)