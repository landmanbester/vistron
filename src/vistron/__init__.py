"""
Vistron: Ray-Powered N-Dimensional Data Animator

A high-performance visualization tool for multi-dimensional xarray datasets,
particularly designed for radio astronomy data cubes.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from vistron.config import VistronConfig
from vistron.server import create_app

__all__ = [
    "VistronConfig",
    "create_app",
    "__version__",
]