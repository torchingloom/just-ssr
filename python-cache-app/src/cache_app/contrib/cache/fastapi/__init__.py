import typing
import time
import aioredis
import pickle

from fastapi import FastAPI

from cache_app.contrib.cache import CacheTagVersion, CacheTagCollection, Cache as CacheBase


class Cache(CacheBase):
    redis: aioredis.Redis

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def get_or_create_tags_versions(self, tags_names: typing.List[str]) -> CacheTagCollection:
        now = str(time.time()).encode()
        exists = await self.redis.mget(*tags_names)
        tags_versions = {tag: exists[i] or now for i, tag in enumerate(tags_names)}
        if now in tags_versions.values():
            await self.redis.mset({k: v for k, v in tags_versions.items() if v == now})
        return CacheTagCollection([CacheTagVersion(k, v) for k, v in tags_versions.items()])

    async def check_tags_versions(self, tag_collection: CacheTagCollection) -> bool:
        if not tag_collection:
            return False
        return tag_collection == await self.get_tags_versions_by_names(tag_collection.names)

    async def renew_tags_versions(self, tags_names: typing.List[str]) -> CacheTagCollection:
        now = str(time.time()).encode()
        tags_versions = {tag: now for i, tag in enumerate(tags_names)}
        if now in tags_versions.values():
            await self.redis.mset({k: v for k, v in tags_versions.items() if v == now})
        return CacheTagCollection([CacheTagVersion(k, v) for k, v in tags_versions.items()])

    async def delete_tags_versions(self, tags_names: typing.List[str]) -> CacheTagCollection:
        await self.redis.delete(*tags_names)
        return CacheTagCollection()

    async def add_key_to_prerender_key(self, prerender_cache_key: str, *keys) -> None:
        await self.redis.sadd(prerender_cache_key, *keys)

    async def get_prerender_key_keys(self, prerender_cache_key: str) -> typing.List[str]:
        return list(map(lambda x: x.decode(), await self.redis.smembers(prerender_cache_key)))

    async def delete_prerender_key_keys(self, prerender_cache_key: str) -> None:
        await self.redis.delete(prerender_cache_key)

    async def set_key_tags_versions(self, key: str, tags_collection: CacheTagCollection) -> None:
        await self.redis.set(key, pickle.dumps(tags_collection))

    async def get_key_tags_versions(self, key: str) -> CacheTagCollection:
        redis_data = await self.redis.get(key)
        if not redis_data:
            return CacheTagCollection()
        return pickle.loads(redis_data)

    async def get_tags_versions_by_names(self, tags_names: typing.List[str]) -> CacheTagCollection:
        redis_data = await self.redis.mget(*tags_names)
        if not redis_data:
            return CacheTagCollection()
        return CacheTagCollection(
            list(CacheTagVersion(tags_names[i], value) for i, value in enumerate(redis_data))
        )


def setup(app: FastAPI, redis_url: str) -> None:
    @app.on_event('startup')
    async def on_startup() -> None:
        redis = await aioredis.create_redis(redis_url)
        app.cache = Cache(redis)

    @app.on_event('shutdown')
    async def on_shutdown() -> None:
        app.cache.redis.close()
