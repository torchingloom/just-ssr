#!/bin/bash
###########

sh -c "/docker/nginx-reload.sh &"
exec "$@"