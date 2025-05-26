import pytest
from click.testing import CliRunner
from pathlib import Path
from vistron.cli import main


def test_version():
    """Test version command."""
    runner = CliRunner()
    result = runner.invoke(main, ['version'])
    assert result.exit_code == 0
    assert 'Vistron version' in result.output


def test_help():
    """Test help command."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'Vistron' in result.output
    assert 'serve' in result.output
    assert 'info' in result.output


def test_serve_missing_zarr():
    """Test serve command with missing zarr file."""
    runner = CliRunner()
    result = runner.invoke(main, ['serve', '/nonexistent/path.zarr'])
    assert result.exit_code == 1
