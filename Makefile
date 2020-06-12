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
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Building $(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX}"; \
		docker build --progress=plain -f $$DOCKERFILE \
			-t $(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX}\
			. || exit -1 ;\
	done; \

build-test-image:	## build images
build-test-image:
	@echo "--> Building test image $(IMAGE_NAME):$(IMAGE_TEST_TAG)"; \
	docker build --target=test --progress=plain -f Dockerfile \
		-t $(IMAGE_NAME):$(IMAGE_TEST_TAG) \
		. || exit -2 ;\

build-test-images:	## build images
build-test-images:
	@for DOCKERFILE in $(DOCKERFILES);do \
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Building test image $(IMAGE_NAME):$(IMAGE_TEST_TAG)$${TAG_SUFFIX}"; \
		docker build --target=test --progress=plain -f $$DOCKERFILE \
			-t $(IMAGE_NAME):$(IMAGE_TEST_TAG)$${TAG_SUFFIX} \
			. || exit -2 ;\
	done; \

test-image:	## test with the Dockerfile image
test-image: build-test-image
	@echo "--> Testing $(IMAGE_NAME):$(IMAGE_TAG)"; \
	docker run --rm -t \
		$(IMAGE_NAME):$(IMAGE_TEST_TAG); \

test-images:	## test with docker images
test-images: build-test-images
	@for DOCKERFILE in $(DOCKERFILES);do \
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Testing $(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX}"; \
		docker run --rm -t \
			$(IMAGE_NAME):$(IMAGE_TEST_TAG)$${TAG_SUFFIX}; \
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

qemu-arm-linux:	## Prepare qemu on linux to run arm 
qemu-arm-linux:
	@docker run --rm --privileged multiarch/qemu-user-static:register --reset
