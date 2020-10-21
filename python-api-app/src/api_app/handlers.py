import typing
import datetime

from fastapi import APIRouter, Request
from fastapi.responses import UJSONResponse

from cache_app.contrib.cache.fastapi.router import CachedRoute, setup_app_cache_check

if typing.TYPE_CHECKING:
    from api_app.app import Application

router = APIRouter(route_class=CachedRoute)


def setup(app: 'Application') -> None:
    setup_app_cache_check(app)
    app.include_router(router, prefix='/api')


def get_tags_for_handler(handler_number: int) -> typing.List[str]:
    return [f'tag-{handler_number}.{_}' for _ in range(1, 21)]


@router.get('/handler{handler_number}')
async def handler(handler_number: int, request: Request):
    tags_versions = await request.app.cache.get_or_create_tags_versions(get_tags_for_handler(handler_number))
    content = {
        'handler_number': handler_number,
        'when': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cache-tags': tags_versions.as_sorted_dict(),
    }
    response = UJSONResponse(content=content)
    response.cache_tags = tags_versions
    return response
