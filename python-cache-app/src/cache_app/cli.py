import os
import click
import typing
import uvicorn
import requests
import ujson as json
from starlette.config import Config

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
        'port': config('PYTHON_CACHE_APP_PORT', cast=int, default=8000),
        'log_level': 'debug' if debug else 'warning',
        'proxy_headers': True,
    }
    if debug:
        uvicorn_kwargs.update({
            'reload': True,
        })
    uvicorn.run('cache_app.asgi:app', **uvicorn_kwargs)


@cli.group()
def tag():
    pass


@tag.command()
@click.argument('names', nargs=-1)
def renew(names: typing.Optional[typing.List[str]] = None):
    if not names:
        return
    print(_tags_op('renew', names))


@tag.command()
@click.argument('names', nargs=-1)
def delete(names: typing.Optional[typing.List[str]] = None):
    if not names:
        return
    print(_tags_op('delete', names))


def _tags_op(op_name: str, tags_names: typing.List[str]) -> str:
    return json.dumps(
        requests.post(
            'http://nginx/__tags_cache_ops__',
            json={
                'op_name': op_name,
                'tags_names': tags_names,
            }
        ).json(),
        indent=4
    )


if __name__ == '__main__':
    cli()
