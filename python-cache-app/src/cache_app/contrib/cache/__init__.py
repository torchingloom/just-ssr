import typing
import hashlib
import pickle
from dataclasses import dataclass
from collections import OrderedDict


class CacheTagCollectionException(Exception):
    pass


@dataclass
class CacheTagVersion:
    tag_name: str
    version: typing.Union[str, bytes]

    def __post_init__(self) -> None:
        if isinstance(self.version, bytes):
            self.version = self.version.decode()


@dataclass
class CacheTagCollection:
    tags_versions: typing.Optional[typing.List[CacheTagVersion]] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CacheTagCollection):
            raise CacheTagCollectionException('bad instance')
        return self.tags_versions == other.tags_versions

    def __add__(self, other: 'CacheTagCollection') -> 'CacheTagCollection':
        return CacheTagCollection((self.tags_versions or []) + (other.tags_versions or []))

    def __bool__(self) -> bool:
        return bool(self.tags_versions)

    def as_sorted_dict(self) -> OrderedDict:
        if not self.tags_versions:
            return OrderedDict()
        return OrderedDict(sorted((tag.tag_name, tag.version) for tag in self.tags_versions))

    @property
    def names(self) -> typing.Optional[typing.List[str]]:
        if not self.tags_versions:
            return None
        return [tag.tag_name for tag in self.tags_versions]

    @property
    def tags_hash(self):
        pickled = pickle.dumps(self.as_sorted_dict())
        return '%s.%s' % (hashlib.md5(pickled).hexdigest(), hashlib.sha1(pickled).hexdigest())


class Cache:
    @classmethod
    def get_cache_key_by_url(cls, url: str, prefix: typing.Optional[str] = '') -> str:
        url_encoded = url.encode()
        key = 'url-tags:%s.%s' % (hashlib.md5(url_encoded).hexdigest(), hashlib.sha1(url_encoded).hexdigest())
        if prefix:
            key = '%s:%s' % (prefix, key)
        return key

    @classmethod
    def get_prerender_cache_key_by_url(cls, url: str, prefix: typing.Optional[str] = '') -> str:
        return 'prerender-' + cls.get_cache_key_by_url(url, prefix)

    @classmethod
    def get_prerender_cache_key_sec(cls, key: str, salt: typing.Optional[str]) -> str:
        return hashlib.md5(f'{key}.{salt}'.encode()).hexdigest()

    @classmethod
    def check_prerender_cache_key_sec(
            cls,
            secret: typing.Optional[str],
            key: typing.Optional[str],
            salt: typing.Optional[str]
    ) -> typing.Optional[bool]:
        if not key or not secret:
            return None
        return secret == cls.get_prerender_cache_key_sec(key, salt)
