import click
from src.services.dev_server import DevServer


@click.command()
@click.option('--port', default=8000, help='Port to serve on', type=int)
@click.option('--reload', is_flag=True, help='Enable hot reload')
def serve(port, reload):
    """Start development server with hot reload"""
    click.echo(f"Starting development server on port {port}")
    if reload:
        click.echo("Hot reload enabled")
    
    server = DevServer(
        port=port, 
        directory="prod/site",
        reload=reload
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        click.echo("\nShutting down development server")