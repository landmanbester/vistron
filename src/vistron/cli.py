"""
Vistron CLI - Command-line interface for the Vistron visualization server.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from vistron.server import create_app
from vistron.config import VistronConfig

console = Console()


def print_banner():
    """Print the Vistron banner."""
    banner = Text("🔭 VISTRON", style="bold blue")
    subtitle = Text("Ray-Powered N-Dimensional Data Animator", style="dim")
    panel = Panel.fit(
        f"{banner}\n{subtitle}",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


@click.group(invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    help="Show version information",
)
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """
    Vistron: High-performance visualization for multi-dimensional datasets.
    
    A Ray-powered web application for interactive visualization and animation
    of N-dimensional xarray datasets, particularly designed for radio astronomy
    data cubes.
    """
    if version:
        from vistron import __version__
        click.echo(f"Vistron version {__version__}")
        return
    
    if ctx.invoked_subcommand is None:
        print_banner()
        click.echo("\nUse 'vistron --help' for available commands.")


@main.command()
@click.argument(
    "zarr_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind the server to",
    show_default=True,
)
@click.option(
    "--port",
    default=8000,
    type=click.IntRange(1, 65535),
    help="Port to bind the server to",
    show_default=True,
)
@click.option(
    "--workers",
    default=1,
    type=click.IntRange(1, 16),
    help="Number of worker processes",
    show_default=True,
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["critical", "error", "warning", "info", "debug", "trace"]),
    help="Log level",
    show_default=True,
)
@click.option(
    "--access-log/--no-access-log",
    default=True,
    help="Enable/disable access logging",
)
@click.option(
    "--ray-address",
    help="Ray cluster address (default: start local cluster)",
)
@click.option(
    "--ray-dashboard-port",
    default=8265,
    type=click.IntRange(1, 65535),
    help="Ray dashboard port",
    show_default=True,
)
@click.option(
    "--max-workers",
    default=None,
    type=click.IntRange(1, 1000),
    help="Maximum number of Ray workers",
)
@click.option(
    "--memory-limit",
    help="Memory limit for Ray workers (e.g., '4GB', '500MB')",
)
def serve(
    zarr_path: Path,
    host: str,
    port: int,
    workers: int,
    reload: bool,
    log_level: str,
    access_log: bool,
    ray_address: Optional[str],
    ray_dashboard_port: int,
    max_workers: Optional[int],
    memory_limit: Optional[str],
) -> None:
    """
    Start the Vistron visualization server.
    
    ZARR_PATH: Path to the zarr dataset to visualize
    
    Examples:
    
        # Basic usage
        vistron serve /path/to/dataset.zarr
        
        # Custom host and port
        vistron serve /path/to/dataset.zarr --host 127.0.0.1 --port 9000
        
        # Development mode with auto-reload
        vistron serve /path/to/dataset.zarr --reload --log-level debug
        
        # Connect to existing Ray cluster
        vistron serve /path/to/dataset.zarr --ray-address ray://head-node:10001
        
        # Limit Ray resources
        vistron serve /path/to/dataset.zarr --max-workers 8 --memory-limit 16GB
    """
    print_banner()
    
    # Validate zarr path
    if not zarr_path.exists():
        console.print(f"❌ Error: Zarr dataset not found at {zarr_path}", style="red")
        sys.exit(1)
    
    # Create configuration
    config = VistronConfig(
        zarr_path=zarr_path,
        ray_address=ray_address,
        ray_dashboard_port=ray_dashboard_port,
        max_workers=max_workers,
        memory_limit=memory_limit,
    )
    
    # Display configuration
    console.print("\n📊 Configuration:", style="bold")
    console.print(f"  Dataset: {zarr_path}")
    console.print(f"  Server: http://{host}:{port}")
    console.print(f"  Ray Dashboard: http://localhost:{ray_dashboard_port}")
    if ray_address:
        console.print(f"  Ray Cluster: {ray_address}")
    else:
        console.print("  Ray Cluster: Local")
    
    # SSH tunnel hint
    if host == "0.0.0.0" and not _is_local_machine():
        console.print(
            f"\n💡 Tip: Access remotely via SSH tunnel:",
            style="dim yellow"
        )
        console.print(
            f"  ssh -L {port}:localhost:{port} user@your-server",
            style="dim"
        )
    
    console.print(f"\n🚀 Starting server...\n")
    
    # Create the FastAPI app with configuration
    app = create_app(config)
    
    # Start the server
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=reload,
            log_level=log_level,
            access_log=access_log,
            server_header=False,
            date_header=False,
        )
    except KeyboardInterrupt:
        console.print("\n👋 Server stopped by user", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Server error: {e}", style="red")
        sys.exit(1)


@main.command()
@click.argument(
    "zarr_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
)
@click.option(
    "--detailed",
    is_flag=True,
    help="Show detailed information about the dataset",
)
def info(zarr_path: Path, detailed: bool) -> None:
    """
    Display information about a zarr dataset.
    
    ZARR_PATH: Path to the zarr dataset to inspect
    """
    import xarray as xr
    
    try:
        console.print(f"📊 Inspecting dataset: {zarr_path}")
        
        # Load dataset metadata
        ds = xr.open_zarr(zarr_path, chunks=None)
        
        # Basic information
        console.print(f"\n📏 Dimensions: {list(ds.dims.keys())}")
        console.print(f"📐 Shape: {[ds.dims[dim] for dim in ds.dims.keys()]}")
        console.print(f"🗂️  Data variables: {list(ds.data_vars.keys())}")
        
        # Memory usage estimate
        total_size = sum(var.nbytes for var in ds.data_vars.values())
        console.print(f"💾 Estimated size: {_format_bytes(total_size)}")
        
        if detailed:
            console.print("\n📋 Detailed Information:")
            
            # Coordinates
            console.print("\n🎯 Coordinates:")
            for name, coord in ds.coords.items():
                coord_type = "numeric" if coord.dtype.kind in "biufc" else "non-numeric"
                console.print(f"  {name}: {coord.shape} ({coord.dtype}, {coord_type})")
                if coord_type == "numeric" and coord.size > 0:
                    console.print(f"    Range: {float(coord.min())} to {float(coord.max())}")
            
            # Data variables
            console.print("\n📊 Data Variables:")
            for name, var in ds.data_vars.items():
                console.print(f"  {name}: {var.shape} ({var.dtype})")
                console.print(f"    Size: {_format_bytes(var.nbytes)}")
                if var.dtype.kind in "biufc":  # numeric
                    try:
                        min_val = float(var.min().compute())
                        max_val = float(var.max().compute())
                        console.print(f"    Range: {min_val} to {max_val}")
                    except Exception:
                        console.print("    Range: Unable to compute")
        
        # Recommendations
        console.print("\n💡 Recommendations:")
        max_dim_size = max(ds.dims.values())
        if max_dim_size > 2000:
            console.print("  • Consider using downsampling for better performance")
        
        numeric_dims = [
            name for name, coord in ds.coords.items()
            if coord.dtype.kind in "biufc"
        ]
        if len(numeric_dims) >= 3:
            console.print(f"  • {len(numeric_dims)} numeric dimensions available for animation")
        elif len(numeric_dims) < 2:
            console.print("  ⚠️  Limited numeric dimensions - animation may be restricted")
        
        ds.close()
        
    except Exception as e:
        console.print(f"❌ Error reading dataset: {e}", style="red")
        sys.exit(1)


@main.command()
def version() -> None:
    """Show version information."""
    from vistron import __version__
    
    console.print(f"Vistron version {__version__}")
    
    # Show dependency versions
    try:
        import ray
        import xarray as xr
        import zarr
        import fastapi
        import numpy as np
        
        console.print("\n📦 Dependencies:")
        console.print(f"  Ray: {ray.__version__}")
        console.print(f"  Xarray: {xr.__version__}")
        console.print(f"  Zarr: {zarr.__version__}")
        console.print(f"  FastAPI: {fastapi.__version__}")
        console.print(f"  NumPy: {np.__version__}")
        
    except ImportError as e:
        console.print(f"⚠️  Could not check dependency versions: {e}", style="yellow")


def _is_local_machine() -> bool:
    """Check if we're running on a local machine."""
    return any(
        indicator in os.environ.get("SSH_CONNECTION", "")
        for indicator in ["127.0.0.1", "localhost"]
    ) or "SSH_CLIENT" not in os.environ


def _format_bytes(bytes_size: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


if __name__ == "__main__":
    main()