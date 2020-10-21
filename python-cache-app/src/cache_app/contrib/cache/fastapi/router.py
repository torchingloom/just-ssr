import copy
import typing
import json
import copy
from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.routing import APIRoute
from fastapi.requests import Request
from fastapi.responses import Response

from cache_app.contrib.cache import CacheTagCollection
from cache_app.contrib.cache.fastapi import Cache


class CachedRouteException(Exception):
    pass


class RequestCacheHelper:
    _cache: Cache
    request: Request
    is_cache_enabled: bool = False
    is_cache_prerender_enabled: bool = False
    is_cache_location: bool = False
    is_prerender_cache_key_sec_valid: bool = False
    prerender_cache_key: str = ''
    prerender_cache_key_sec: str = ''
    prerender_cache_url: str = ''
    cache_key: str = ''

    def __init__(self, request: Request):
        self.request = request
        self._cache = request.app.cache
        self.is_cache_enabled = True
        self.is_cache_location = bool(self.request.headers.get('x-is-cache-location'))
        self.prerender_cache_url = request.headers.get('x-prerender-cache-url')
        self.prerender_cache_key = request.headers.get('x-prerender-cache-key')
        self.prerender_cache_key_sec = request.headers.get('x-prerender-cache-key-sec')
        self.is_prerender_cache_key_sec_valid = request.app.cache.check_prerender_cache_key_sec(
            self.prerender_cache_key_sec,
            self.prerender_cache_key,
            request.app.config.nginx_prerender_cache_key_secret,
        )
        self.cache_key = request.app.cache.get_cache_key_by_url(str(request.url))
        if self.is_cache_location:
            self.cache_key = request.headers.get('x-cache-key')
        if self.is_prerender_cache_key_sec_valid:
            self.is_cache_prerender_enabled = True

    async def is_cache_tags_versions_valid(self) -> bool:
        cached_tags = await self.cache_tags_get()
        return await self._cache.check_tags_versions(cached_tags)

    async def cache_tags_get(self) -> CacheTagCollection:
        return await self._cache.get_url_tags_versions(self.cache_key)

    async def cache_tags_set(self, tags_collection: CacheTagCollection) -> None:
        await self._cache.set_url_tags_versions(self.cache_key, tags_collection)
        if self.is_cache_prerender_enabled:
            await self._cache.add_key_to_prerender_key(self.prerender_cache_key, self.cache_key)


class CachedRoute(APIRoute):
    def get_route_handler(self) -> typing.Callable:
        orig_handler = super().get_route_handler()

        async def handler(request: Request) -> Response:
            helper = RequestCacheHelper(request)
            if helper.is_cache_enabled and not helper.is_cache_location:
                cache_location_url = request.app.config.nginx_api_cache_internal_url
                cache_url = f'{cache_location_url}{request.url.path}?{request.url.query}'
                headers = {
                    'x-accel-redirect': cache_url,
                    'x-cache-key': helper.cache_key,
                }
                is_cache_valid = await helper.is_cache_tags_versions_valid()
                if not is_cache_valid:
                    headers.update({
                        'x-cache-invalid': 'yes',
                    })
                if helper.is_cache_prerender_enabled:
                    headers.update({
                        'x-prerender-cache-url': helper.prerender_cache_url,
                        'x-prerender-cache-key': helper.prerender_cache_key,
                        'x-prerender-cache-key-sec': helper.prerender_cache_key_sec,
                    })
                return Response(headers=headers)
            response: Response = await orig_handler(request)
            cache_tags = getattr(response, 'cache_tags', None)
            if cache_tags:
                await helper.cache_tags_set(cache_tags)
            return response

        return handler


def setup_app_cache_check(app: FastAPI, raise_exception: bool = True) -> None:
    @app.on_event('startup')
    async def on_startup() -> None:
        if not isinstance(getattr(app, 'cache', None), Cache):
            msg = 'App cache is not installed'
            if raise_exception:
                raise CachedRouteException('App cache is not installed')
            logger.critical(msg)
