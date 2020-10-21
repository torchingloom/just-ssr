import os
import click
import site
import uvicorn
from starlette.config import Config

IS_IN_DOCKER = os.getenv('IS_IN_DOCKER')

config = Config('/docker/.env', os.environ)


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--debug', is_flag=True)
def serve(debug: bool) -> None:
    uvicorn_kwargs = {
        'loop': 'uvloop',
        'host': '0.0.0.0',
        'port': config('PYTHON_API_APP_PORT', cast=int, default=8000),
        'log_level': 'debug' if debug else 'warning',
        'proxy_headers': True,
        'reload_dirs': site.getsitepackages() + ['/cache-app', os.getenv('WORKDIR')],
    }
    if debug:
        uvicorn_kwargs.update({
            'reload': True,
        })
    uvicorn.run('api_app.asgi:app', **uvicorn_kwargs)


if __name__ == '__main__':
    cli()
