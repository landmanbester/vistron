"""
Utility functions for Vistron.
"""

from functools import lru_cache
from typing import Dict, List, Tuple


def calculate_optimal_downsample(shape: Tuple[int, ...], target_size: int = 500) -> int:
    """Calculate optimal downsampling factor to keep data under target size."""
    max_dim = max(shape)
    if max_dim <= target_size:
        return 1
    return max(1, max_dim // target_size)


@lru_cache(maxsize=32)
def get_downsample_options(dim_size: int) -> List[Dict]:
    """Get available downsampling options for a dimension."""
    options = [{"factor": 1, "label": "Full Resolution", "size": dim_size}]
    
    for factor in [2, 4, 8, 16]:
        if dim_size // factor >= 10:  # Don't go below 10 points
            new_size = dim_size // factor
            options.append({
                "factor": factor, 
                "label": f"1/{factor} Resolution", 
                "size": new_size
            })
    
    return options


def format_bytes(bytes_size: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def validate_zarr_dataset(zarr_path) -> bool:
    """Validate that a path contains a readable zarr dataset."""
    try:
        import xarray as xr
        ds = xr.open_zarr(zarr_path, chunks=None)
        ds.close()
        return True
    except Exception:
        return False