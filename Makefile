IMGNAME=sdelrio/hs110-exporter
VERSION = $(shell cat VERSION)

.PHONY: all build-images build-test-images test-images push-images update-version

IMAGE_NAME ?= sdelrio/hs110-exporter
IMAGE_TAG ?= latest
IMAGE_TEST_TAG ?= test

VERSION ?= master
DOCKERFILES ?= $(shell find . -maxdepth 1 -name 'Dockerfile*')

.DEFAULT: help
help:	## Show this help menu.
	@echo "Usage: make [TARGET ...]"
	@echo ""
	@egrep -h "#[#]" $(MAKEFILE_LIST) | sed -e 's/\\$$//' | awk 'BEGIN {FS = "[:=].*?#[#] "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

build-images:	## build images
build-images:
	@for DOCKERFILE in $(DOCKERFILES);do \
		echo "--> Building $(IMAGE_NAME):$(IMAGE_TAG) -> $$DOCKERFILE"; \
		docker build --progress=plain -f $$DOCKERFILE \
			-t $(IMAGE_NAME):$(IMAGE_TAG)`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'` \
			. || exit -1 ;\
	done; \

build-test-images:	## build images
build-test-images:
	@for DOCKERFILE in $(DOCKERFILES);do \
		echo "--> Building test image $(IMAGE_NAME):$(IMAGE_TEST_TAG)"; \
		docker build --target=test --progress=plain -f $$DOCKERFILE \
			-t $(IMAGE_NAME):$(IMAGE_TEST_TAG)`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'` \
			. || exit -2 ;\
	done; \

test-images:	## test with docker images
test-images: build-test-images
	@for DOCKERFILE in $(DOCKERFILES);do \
		echo "--> Testing $(IMAGE_NAME):$(IMAGE_TAG)"; \
		docker run --rm -t \
			$(IMAGE_NAME):$(IMAGE_TEST_TAG)`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
	done;

publish-images:	## publish docker images
publish-images: build-images
	@for DOCKERFILE in $(DOCKERFILES);do \
		echo docker push $(IMAGE_NAME):$(IMAGE_TAG)`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'` ; \
	done; \

update-version: ## update version from VERSION file in all Dockerfiles
update-version:
	@for DOCKERFILE in $(DOCKERFILES);do \
		sed -i "0,/^ENV\ \VERSION .*$$/{s//ENV VERSION $(VERSION)/}" $${DOCKERFILE}; \
	done;
	@echo updated to version "$(VERSION)" Dockerfiles

build:	## local development build
build:
	@pip install -r requirements.txt;
	@pip install tox

test: ## Test coverage with tox
test: 
	@tox -e coverage,py37
