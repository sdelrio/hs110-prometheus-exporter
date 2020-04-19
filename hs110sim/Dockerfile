ARG BASE_IMAGE=jfloff/alpine-python
ARG BASE_IMAGE_TAG=3.7-slim

#######################################################
# BUILDER IMAGE
#######################################################
FROM $BASE_IMAGE:$BASE_IMAGE_TAG as build

WORKDIR /usr/local/bin

COPY hs110sim.py ./
RUN chmod +x hs110sim.py

EXPOSE 9999

ENTRYPOINT ["python", "/usr/local/bin/hs110sim.py"]

