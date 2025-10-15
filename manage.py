#!/usr/bin/env python3
"""
Django-style management script for Galleria.

Entry point for all command-line operations.
"""
import click
from src.command.find_samples import find_samples
from src.command.upload_photos import upload_photos
from src.command.process_photos import process_photos
from src.command.build import build
from src.command.serve import serve
from src.command.collection_stats import collection_stats
from src.command.deploy import deploy


@click.group()
def cli():
    """Galleria photo gallery management commands."""
    pass


# Register commands
cli.add_command(find_samples, name="find-samples")
cli.add_command(upload_photos, name="upload-photos")
cli.add_command(process_photos, name="process-photos")
cli.add_command(build, name="build")
cli.add_command(serve, name="serve")
cli.add_command(collection_stats, name="collection-stats")
cli.add_command(deploy, name="deploy")


if __name__ == "__main__":
    cli()