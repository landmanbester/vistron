# 🔭 Vistron

**Ray-Powered N-Dimensional Data Animator**

A high-performance visualization tool for multi-dimensional xarray datasets, particularly designed for radio astronomy data cubes. Built for the [Africanus](https://github.com/ratt-ru/africanus) ecosystem.

## Features

- 🚀 **Ray-powered performance**: Distributed processing for large datasets
- 📊 **Multi-dimensional support**: Visualize N-dimensional xarray/zarr datasets  
- 🎬 **Interactive animation**: Animate through any dimension with real-time controls
- ⚡ **Adaptive resolution**: Automatic downsampling for optimal performance
- 🌐 **Web-based interface**: Access via browser with SSH tunneling support
- 🔧 **Click CLI**: Professional command-line interface

## Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/yourusername/vistron.git
cd vistron
pip install -e .

# Or install from PyPI (when published)
pip install vistron
```

### Basic Usage

```bash
# Start server with your dataset
vistron serve /path/to/your/dataset.zarr

# Get dataset information
vistron info /path/to/your/dataset.zarr

# Advanced usage with custom settings
vistron serve /path/to/dataset.zarr \
  --host 0.0.0.0 \
  --port 8000 \
  --max-workers 8 \
  --memory-limit 16GB
```

### Remote Access

If running on a remote server, set up SSH port forwarding:

```bash
ssh -L 8000:localhost:8000 user@your-server
```

Then open `http://localhost:8000` in your browser.

## CLI Reference

### `vistron serve`

Start the visualization server.

**Arguments:**
- `ZARR_PATH`: Path to the zarr dataset to visualize

**Options:**
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 8000) 
- `--workers`: Number of worker processes (default: 1)
- `--reload`: Enable auto-reload for development
- `--log-level`: Set logging level
- `--ray-address`: Connect to existing Ray cluster
- `--max-workers`: Maximum Ray workers
- `--memory-limit`: Memory limit for Ray workers

### `vistron info`

Display dataset information.

**Arguments:**
- `ZARR_PATH`: Path to the zarr dataset

**Options:**
- `--detailed`: Show detailed coordinate and variable information

### `vistron version`

Show version and dependency information.

## Dataset Requirements

Vistron works with:
- **Zarr datasets** opened via xarray
- **Multi-dimensional arrays** with named coordinates
- **Mixed coordinate types** (numeric and non-numeric)
- **Large datasets** (tested with TB-scale radio astronomy cubes)

### Coordinate Support

- **Numeric coordinates**: Full support for visualization and animation
- **Non-numeric coordinates**: Basic support with dropdown selection
- **Mixed datasets**: Automatic detection and appropriate controls

## Web Interface

The web interface provides:

1. **Data Selection**: Choose variables and axes to visualize
2. **Performance Controls**: Auto-optimization and manual downsampling
3. **Animation Controls**: Frame rate, batch size, and axis selection
4. **Dimension Controls**: Set fixed values for non-displayed dimensions

### Performance Features

- **Auto-downsampling**: Automatically reduces resolution for better performance
- **Batch processing**: Processes animation frames in parallel batches
- **Adaptive streaming**: Streams data at appropriate resolution
- **Progress tracking**: Real-time progress and performance indicators

## Development

### Package Structure

```
src/vistron/
├── __init__.py          # Package initialization
├── cli.py               # Click-based command line interface
├── config.py            # Configuration management
├── server.py            # FastAPI server implementation
├── workers.py           # Ray workers for data processing
├── websocket.py         # WebSocket connection management
├── utils.py             # Utility functions
└── templates/
    └── index.html       # Web interface template
```

### Development Setup

```bash
# Clone and install in development mode
git clone https://github.com/yourusername/vistron.git
cd vistron
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vistron

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Run integration tests only
```

## Configuration

Create a `pyproject.toml` file to customize build and tool settings. The package uses:

- **Build**: setuptools with setuptools-scm
- **Code formatting**: black + isort
- **Linting**: flake8 + mypy
- **Testing**: pytest with coverage

## Performance Tips

1. **Use auto-downsampling** for initial exploration
2. **Adjust batch size** based on available memory
3. **Connect to Ray cluster** for distributed processing
4. **Monitor Ray dashboard** at `http://localhost:8265`
5. **Use numeric coordinates** for best animation performance

## Radio Astronomy Integration

Designed for the Africanus ecosystem:

- **Compatible with pfb-imaging** output cubes
- **Supports MeerKAT/SKA data formats**
- **Handles STOKES, TIME, FREQ dimensions**
- **Works with QuartiCal calibrated data**

## Troubleshooting

### Common Issues

**"No dataset loaded" error:**
- Check zarr path is correct and accessible
- Verify dataset is valid zarr format
- Check file permissions

**Performance issues:**
- Enable auto-downsampling
- Reduce batch size
- Check Ray worker memory limits

**WebSocket connection failures:**
- Check firewall settings
- Verify SSH tunnel configuration
- Check server logs for errors

### Getting Help

- Check the [documentation](https://vistron.readthedocs.io)
- Report issues on [GitHub](https://github.com/yourusername/vistron/issues)
- Join discussions in the Africanus community

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use Vistron in your research, please cite:

```bibtex
@software{vistron,
  title={Vistron: Ray-Powered N-Dimensional Data Animator},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/vistron}
}
```

## Related Projects

- [Africanus](https://github.com/ratt-ru/africanus) - Radio astronomy processing framework
- [pfb-imaging](https://github.com/ratt-ru/pfb-imaging) - Advanced radio interferometric imaging
- [QuartiCal](https://github.com/ratt-ru/QuartiCal) - Scalable calibration software
- [Stimela2](https://github.com/ratt-ru/stimela2) - Containerized workflow framework