import pytest
from vistron.utils import (
    calculate_optimal_downsample,
    get_downsample_options,
    format_bytes
)


def test_calculate_optimal_downsample():
    """Test downsample calculation."""
    # Small shape should return 1
    assert calculate_optimal_downsample((100, 100)) == 1
    
    # Large shape should return > 1
    assert calculate_optimal_downsample((2000, 2000)) > 1


def test_get_downsample_options():
    """Test downsample options generation."""
    options = get_downsample_options(1000)
    assert len(options) > 1
    assert options[0]["factor"] == 1
    assert options[0]["label"] == "Full Resolution"


def test_format_bytes():
    """Test byte formatting."""
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024**2) == "1.0 MB"
    assert format_bytes(1024**3) == "1.0 GB"