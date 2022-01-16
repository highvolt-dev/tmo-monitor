FROM python:alpine

LABEL org.opencontainers.image.source="https://github.com/highvolt-dev/tmo-monitor"

RUN apk add iputils git

RUN adduser -D -h /monitor monitor

COPY entrypoint.sh /

COPY ../ /tmo-monitor
RUN cd tmo-monitor && \
    pip3 install -r requirements.txt

ENTRYPOINT [ "/entrypoint.sh" ]
