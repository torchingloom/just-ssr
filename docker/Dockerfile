FROM openresty/openresty:buster-fat as nginx
ENV TERM=xterm PYTHONUNBUFFERED=1 LANG=C.UTF-8 WORKDIR=/app/ TZ=Europe/Moscow
WORKDIR $WORKDIR
RUN \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get update \
    && apt-get install -y --no-install-recommends apt-utils \
    && apt-get install -y inotify-tools
ADD docker/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
ADD docker /docker
RUN chmod -R +x /docker
ADD front-app/* $WORKDIR
ENTRYPOINT ["/docker/nginx-entrypoint.sh"]
CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"]

FROM node:14.13.1-buster as prerenderer
ENV TERM=xterm PYTHONUNBUFFERED=1 LANG=C.UTF-8 WORKDIR=/app/ TZ=Europe/Moscow
WORKDIR $WORKDIR
RUN \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone
RUN \
    apt-get update \
    && apt-get install -y \
        curl \
        libgbm1 \
        xvfb \
        fonts-liberation \
        libappindicator3-1 \
        libxss1 \
        xdg-utils \
        libasound2 \
        libnspr4 \
        libnss3 \
    && curl -sLO https://dl-ssl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb \
    && rm -f google-chrome-stable_current_amd64.deb \
    && curl -sLO https://github.com/prerender/prerender/archive/master.tar.gz \
    && tar -zxf master* \
    && mv prerender*/* $WORKDIR \
    && npm ci \
    && npm i prerender-memory-cache \
    && npm i -g nodemon \
    && apt-get clean autoclean \
    && apt-get autoremove --yes \
    && rm -rf /var/lib/{apt,dpkg,cache,log}/
ADD js-prerenderer/* $WORKDIR
CMD nodemon prerender-server.js

FROM python:3.9 as python-api-app
ENV TERM=xterm PYTHONUNBUFFERED=1 LANG=C.UTF-8 WORKDIR=/app/ TZ=Europe/Moscow CACHE_APP=/cache-app/
WORKDIR $WORKDIR
RUN \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone
RUN pip install --upgrade pip setuptools pipenv

ADD python-api-app/Pipfile* $WORKDIR
ADD python-cache-app/Pipfile* $CACHE_APP
ADD docker /docker
RUN pipenv install --system --clear
RUN \
    cd $CACHE_APP \
    && pipenv install --system --clear
ADD python-api-app $WORKDIR
RUN mypy $WORKDIR
RUN pip install -e .
ADD python-cache-app $CACHE_APP
RUN mypy $CACHE_APP
RUN \
    cd $CACHE_APP \
    && pip install -e .
CMD python-api-app serve --debug

FROM python:3.9 as python-cache-app
ENV TERM=xterm PYTHONUNBUFFERED=1 LANG=C.UTF-8 WORKDIR=/app/ TZ=Europe/Moscow
WORKDIR $WORKDIR
RUN \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone
RUN pip install --upgrade pip setuptools pipenv
ADD python-cache-app/Pipfile* ./
RUN pipenv install --system --clear
ADD docker /docker
ADD python-cache-app $WORKDIR
RUN mypy $WORKDIR
RUN pip install -e .
CMD python-cache-app serve --debug
