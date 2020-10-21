# JUST SSR CACHE

## CLONE

## START

```shell
docker-compose -f docker/docker-compose.yml up --force-recreate --build
```

## RENEW TAGS

```shell
docker-compose -f docker/docker-compose.yml exec python-cache-app python-cache-app tag renew tag-1.9 tag-1.11
```

## DELETE TAGS

```shell
docker-compose -f docker/docker-compose.yml exec python-cache-app python-cache-app tag delete tag-1.9 tag-1.10
```