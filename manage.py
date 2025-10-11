#!/usr/bin/env python3
"""
Django-style management script for Galleria.

Entry point for all command-line operations.
"""
import click
from src.command.find_samples import find_samples
from src.command.upload_photos import upload_photos


@click.group()
def cli():
    """Galleria photo gallery management commands."""
    pass


# Register commands
cli.add_command(find_samples, name="find-samples")
cli.add_command(upload_photos, name="upload-photos")


if __name__ == "__main__":
    cli()