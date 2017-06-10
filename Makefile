IMGNAME=sdelrio/hs110-exporter
VERSION=:$(TAG)
TESTIP=192.168.1.53
.PHONY: all build run

all: build run

build:
			@docker build -t $(IMGNAME)$(VERSION) --rm . && echo Buildname: $(IMAGENAME):$(VERSION)
			@docker build -t $(IMGNAME)-arm$(VERSION) --rm -f Dockerfile.arm . && echo Buildname: $(IMAGENAME):$(VERSION)

run:
			docker run --rm -ti -p 8110:8110 $(IMGNAME)$(VERSION)

runarm:
			docker run --rm -ti -p 8110:8110 $(IMGNAME)-arm$(VERSION)
