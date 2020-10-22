import typing

import fastapi

from cache_app.contrib.cache.fastapi import Cache

if typing.TYPE_CHECKING:
    from cache_app.app import Application, AppConfig

router = fastapi.APIRouter()


def setup(app: 'Application') -> None:
    app.include_router(router)


@router.get('/')
@router.get('/{url}')
async def handler(request: fastapi.Request) -> fastapi.Response:
    config: 'AppConfig' = request.app.config
    cache: Cache = request.app.cache
    prerender_internal_url = config.nginx_prerender_internal_url
    url_with_args = f'{request.path_params.get("url", "")}?{request.query_params}'
    prerender_url = f'{prerender_internal_url}{url_with_args}'
    prerender_cache_key_secret = config.nginx_prerender_cache_key_secret
    prerender_cache_key = cache.get_prerender_cache_key_by_url(str(request.url))
    is_prerender_cache_valid = await cache.check_prerender_key_keys_hashes(prerender_cache_key)
    headers = {
        'x-accel-redirect': prerender_url,
        'x-prerender-cache-url': str(request.url),
        'x-prerender-cache-key': prerender_cache_key,
        'x-prerender-cache-key-sec': cache.get_prerender_cache_key_sec(prerender_cache_key, prerender_cache_key_secret),
    }
    if not is_prerender_cache_valid:
        await cache.delete_prerender_key_keys_hashes(prerender_cache_key)
        headers.update({
            'x-prerender-cache-invalid': 'yes',
        })
    return fastapi.Response(headers=headers)


@router.post('/__tags_cache_ops__')
async def tags_ops_handler(request: fastapi.Request) -> dict:
    op_name = (await request.json()).get('op_name')
    if op_name not in ['renew', 'delete']:
        return {'error': 'bad op_name'}
    op = getattr(request.app.cache, f'{op_name}_tags_versions')
    return {
        'op_name': op_name,
        'tags': (await op((await request.json()).get('tags_names'))).as_sorted_dict(),
    }
