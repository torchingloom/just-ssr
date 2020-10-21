# JUST SSR CACHE

## CLONE

## START

```shell
docker-compose -f docker/docker-compose.yml up --force-recreate --build
```

## RENEW TAGS

```shell
docker-compose -f docker/docker-compose.yml python-api-app tag renew tag-1 tag-2
```

## DELETE TAGS

```shell
docker-compose -f docker/docker-compose.yml python-api-app tag delete tag-1 tag-2
```