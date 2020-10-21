from typing import TYPE_CHECKING

import fastapi
import pydantic

from cache_app.contrib.cache.fastapi import setup as setup_cache
from cache_app.handlers import setup as setup_handlers

if TYPE_CHECKING:
    from cache_app.contrib.cache.fastapi import Cache


class AppConfig(pydantic.BaseSettings):
    api_name: str = str(__name__)
    redis_cache_url: str
    nginx_prerender_cache_key_secret: str
    nginx_prerender_internal_url: str


class Application(fastapi.FastAPI):
    config: AppConfig
    cache: 'Cache'


def get_application() -> Application:
    app = Application()
    app.config = AppConfig()
    setup_cache(app, app.config.redis_cache_url)
    setup_handlers(app)
    return app
