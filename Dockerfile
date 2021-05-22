ARG BASE_IMAGE=jfloff/alpine-python
ARG BASE_IMAGE_TAG=3.8-slim
ARG RUSH_BASE_IMAGE=rustagainshell/rash
ARG RUSH_BASE_IMAGE_TAG=1.0.0

#######################################################
# BUILDER IMAGE
#######################################################
FROM $BASE_IMAGE:$BASE_IMAGE_TAG as build

RUN apk add --no-cache alpine-sdk
RUN mkdir /pip_install
WORKDIR /pip_install
COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --install-option="--prefix=/pip_install" -r /tmp/requirements.txt

#######################################################
# TESTS IMAGE
#######################################################

FROM build as test

RUN cp -r /pip_install /root/.local \
    && \
    pip install \
        tox \
    && \
    mkdir -p /workdir

WORKDIR /workdir
COPY requirements.txt \
    tox.ini \
    .pylintrc \
    mypy.ini \
    hs110exporter.py \
    test_hs110exporter.py \
    ./

ENTRYPOINT ["tox", "-e", "coverage,py3"]

#######################################################
# RASH IMAGE
#######################################################

FROM $RUSH_BASE_IMAGE:$RUSH_BASE_IMAGE_TAG AS rash

#######################################################
# RUN IMAGE
#######################################################
FROM $BASE_IMAGE:$BASE_IMAGE_TAG as run
COPY --from=rash /bin/rash /bin
COPY --from=build /pip_install /root/.local

WORKDIR /usr/local/bin

ENV LISTENPORT 8110
ENV FREQUENCY 1
ENV VERSION 0.99

COPY hs110exporter.py entrypoint.rh ./
RUN chmod +x entrypoint.rh

EXPOSE 8110

ENTRYPOINT ["/usr/local/bin/entrypoint.rh"]

