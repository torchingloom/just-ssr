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
        return bool(tag_collection == await self.get_tags_versions_by_names(tag_collection.names))

    async def renew_tags_versions(self, tags_names: typing.List[str]) -> CacheTagCollection:
        now = str(time.time()).encode()
        tags_versions = {tag: now for i, tag in enumerate(tags_names)}
        if now in tags_versions.values():
            await self.redis.mset({k: v for k, v in tags_versions.items() if v == now})
        return CacheTagCollection([CacheTagVersion(k, v) for k, v in tags_versions.items()])

    async def delete_tags_versions(self, tags_names: typing.List[str]) -> CacheTagCollection:
        await self.redis.delete(*tags_names)
        return CacheTagCollection()

    async def add_key_hash_to_prerender_key(
            self,
            prerender_cache_key: str,
            key: str,
            tag_collection: CacheTagCollection
    ) -> None:
        value = f'{key}={tag_collection.tags_hash}'
        await self.redis.sadd(prerender_cache_key, value)

    async def get_prerender_key_keys_hashes(self, prerender_cache_key: str) -> typing.Dict[str, str]:
        return {
            row[0]: row[1]
            for row in [
                row.decode().split('=')
                for row in await self.redis.smembers(prerender_cache_key)
            ]
        }

    async def check_prerender_key_keys_hashes(self, prerender_cache_key: str) -> bool:
        all_tags = CacheTagCollection()
        for key, hash_value in (await self.get_prerender_key_keys_hashes(prerender_cache_key)).items():
            key_tags = await self.get_key_tags_versions(key)
            if key_tags.tags_hash != hash_value:
                return False
            all_tags += key_tags
        if not (await self.check_tags_versions(all_tags)):
            return False
        return True

    async def delete_prerender_key_keys_hashes(self, prerender_cache_key: str) -> None:
        await self.redis.delete(prerender_cache_key)

    async def set_key_tags_versions(self, key: str, tag_collection: CacheTagCollection) -> None:
        await self.redis.set(key, pickle.dumps(tag_collection))

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
        setattr(app, 'cache', Cache(redis))

    @app.on_event('shutdown')
    async def on_shutdown() -> None:
        getattr(app, 'cache').redis.close()
