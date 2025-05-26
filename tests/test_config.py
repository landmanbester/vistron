import pytest
from pathlib import Path
from vistron.config import VistronConfig


def test_config_creation(tmp_path):
    """Test creating a valid configuration."""
    zarr_path = tmp_path / "test.zarr"
    zarr_path.mkdir()
    
    config = VistronConfig(zarr_path=zarr_path)
    assert config.zarr_path == zarr_path
    assert config.ray_dashboard_port == 8265


def test_config_invalid_zarr():
    """Test configuration with invalid zarr path."""
    with pytest.raises(ValueError, match="Zarr dataset not found"):
        VistronConfig(zarr_path=Path("/nonexistent"))


def test_ray_init_kwargs():
    """Test Ray initialization kwargs generation."""
    zarr_path = Path(".")  # Use current directory for test
    
    config = VistronConfig(
        zarr_path=zarr_path,
        max_workers=4,
        memory_limit="8GB"
    )
    
    kwargs = config.ray_init_kwargs
    assert "num_cpus" in kwargs
    assert kwargs["num_cpus"] == 4