ARG BASE_IMAGE=jfloff/alpine-python
ARG BASE_IMAGE_TAG=3.7-slim

#######################################################
# BUILDER IMAGE
#######################################################
FROM $BASE_IMAGE:$BASE_IMAGE_TAG as build

RUN mkdir /pip_install
WORKDIR /pip_install
COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --install-option="--prefix=/pip_install" -r /tmp/requirements.txt

#######################################################
# RUN IMAGE
#######################################################
FROM $BASE_IMAGE:$BASE_IMAGE_TAG as run
COPY --from=build /pip_install /usr/local/lib/pyenv/versions/3.7.3

WORKDIR /usr/local/bin

ENV LISTENPORT 8110
ENV HS110IP 192.168.1.53
ENV FREQUENCY 1
ENV VERSION 0.97

COPY hs110exporter.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8110

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

