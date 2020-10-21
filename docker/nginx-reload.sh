#!/bin/bash
###########

while true; do
  inotifywait -q -e create -e modify -e delete -e move /usr/local/openresty/nginx/conf/nginx.conf /etc/nginx/conf.d
  nginx -t
  if [ $? -eq 0 ]; then
    echo "Detected Nginx Configuration Change"
    echo "Executing: nginx -s reload"
    nginx -s reload
  fi
done
