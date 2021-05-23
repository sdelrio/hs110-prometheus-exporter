#######################################################
# BASE IMAGE
#######################################################
ARG BASE_IMAGE=python
ARG BASE_IMAGE_TAG=3.8-alpine3.13

FROM $BASE_IMAGE:$BASE_IMAGE_TAG as base

# Set python env
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ARG USER_ID=1000
ARG USER_NAME=app
ARG GROUP_ID=1000
ARG GROUP_NAME=app

# Create user
RUN addgroup -S -g $GROUP_ID $GROUP_NAME && \
    adduser -S -G $GROUP_NAME -u $USER_ID $USER_NAME

#######################################################
# BUILDER IMAGE
#######################################################
FROM base as build

COPY requirements.alpine .
RUN cat requirements.alpine | xargs apk add --no-cache

COPY requirements.txt /tmp/requirements.txt
# Install runtime dependencies iinto /usr/local/lib/python3.x/site-packages
RUN pip install \
        --no-cache-dir \
        -r /tmp/requirements.txt

#######################################################
# TESTS IMAGE
#######################################################

FROM build as test

ARG USER_ID=1000
ARG USER_NAME=app
ARG GROUP_ID=1000
ARG GROUP_NAME=app

# Copy pip libs
COPY --from=build  /usr/local/lib /usr/local/lib

WORKDIR /workdir
COPY requirements.txt \
     requirements-dev.txt \
     tox.ini \
     .pylintrc \
     mypy.ini \
     hs110exporter.py \
     test_hs110exporter.py \
     ./
RUN pip install \
        --no-cache-dir \
        -r requirements-dev.txt

ENTRYPOINT ["tox", "-e", "coverage,py3"]

#######################################################
# RUN IMAGE
#######################################################
FROM base as run

ARG USER_ID=1000
ARG USER_NAME=app
ARG GROUP_ID=1000
ARG GROUP_NAME=app

# Get pip installed packages from build image
COPY --from=build  /usr/local/lib /usr/local/lib
COPY hs110exporter.py /usr/local/bin/hs110exporter.py

USER $USER_NAME

ENV LISTENPORT 8110
ENV FREQUENCY 1


EXPOSE 8110

USER root
COPY entrypoint.sh /entrypoint.sh
USER $USER_NAME

ENTRYPOINT ["/entrypoint.sh"]

