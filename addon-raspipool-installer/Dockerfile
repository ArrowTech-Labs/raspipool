ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache \
        curl \
        tar \
        rsync \
        jq \
    && pip install --no-cache-dir aiohttp==3.9.5

WORKDIR /app

COPY rootfs/app/ /app/

RUN chmod a+x /app/run.sh /app/install.sh

CMD ["/app/run.sh"]
