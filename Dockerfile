FROM python:alpine

LABEL org.opencontainers.image.source="https://github.com/highvolt-dev/tmo-monitor"

RUN apk add git iputils-ping

RUN adduser -D -h /monitor monitor

COPY docker/entrypoint.sh /

COPY . /tmo-monitor
WORKDIR /tmo-monitor
RUN pip3 install .

ENTRYPOINT [ "/entrypoint.sh" ]
