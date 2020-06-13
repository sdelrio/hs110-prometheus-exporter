IMGNAME=sdelrio/hs110-exporter

.PHONY: all build-images build-test-images test-images push-images update-version

IMAGE_NAME ?= sdelrio/hs110-exporter
IMAGE_TAG ?= latest
IMAGE_TEST_TAG ?= test
IMAGE_PREFIX ?= docker.pkg.github.com

VERSION ?= master
FILE_VERSION = $(shell cat VERSION)
DOCKERFILES ?= $(shell find . -maxdepth 1 -name 'Dockerfile*')

.DEFAULT: help
help:	## Show this help menu.
	@echo "Usage: make [TARGET ...]"
	@echo ""
	@egrep -h "#[#]" $(MAKEFILE_LIST) | sed -e 's/\\$$//' | awk 'BEGIN {FS = "[:=].*?#[#] "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

build-images:	## Build images
build-images:
	@for DOCKERFILE in $(DOCKERFILES);do \
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Building $(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX}"; \
		docker build --progress=plain -f $$DOCKERFILE \
			-t $(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX}\
			. || exit -1 ;\
	done; \

build-test-image:	## Build 1 image to run tests
build-test-image:
	@echo "--> Building test image $(IMAGE_NAME):$(IMAGE_TEST_TAG)"; \
	docker build --target=test --progress=plain -f Dockerfile \
		-t $(IMAGE_NAME):$(IMAGE_TEST_TAG) \
		. || exit -2 ;\

build-test-images:	## Build all images and to run tests
build-test-images:
	@for DOCKERFILE in $(DOCKERFILES);do \
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Building test image $(IMAGE_NAME):$(IMAGE_TEST_TAG)$${TAG_SUFFIX}"; \
		docker build --target=test --progress=plain -f $$DOCKERFILE \
			-t $(IMAGE_NAME):$(IMAGE_TEST_TAG)$${TAG_SUFFIX} \
			. || exit -2 ;\
	done; \

test-image:	## Tests with the Dockerfile image
test-image: build-test-image
	@echo "--> Testing $(IMAGE_NAME):$(IMAGE_TAG)"; \
	docker run --rm -t \
		$(IMAGE_NAME):$(IMAGE_TEST_TAG); \

test-images:	## Tests with all docker images
test-images: build-test-images
	@for DOCKERFILE in $(DOCKERFILES);do \
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Testing $(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX}"; \
		docker run --rm -t \
			$(IMAGE_NAME):$(IMAGE_TEST_TAG)$${TAG_SUFFIX}; \
	done;

publish-images:	## Publish docker images
publish-images: build-images
	@for DOCKERFILE in $(DOCKERFILES);do \
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Publishing $(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX}"; \
		echo docker push $(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX} ; \
	done; \

publish-images-gh:	## Publish docker images Git Hub packages
publish-images-gh: build-images
	@for DOCKERFILE in $(DOCKERFILES);do \
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Publishing $(IMAGE_PREFIX)/$(IMAGE_NAME)/$(IMAGE_TAG)$${TAG_SUFFIX}:$${GITHUB_RUN_NUMBER}"; \
		docker tag \
			$(IMAGE_NAME):$(IMAGE_TEST_TAG)$${TAG_SUFFIX} \
			$(IMAGE_PREFIX)/$(IMAGE_NAME):$(IMAGE_TAG)/$${TAG_SUFFIX}:$${GITHUB_RUN_NUMBER} ; \
		docker push $(IMAGE_PREFIX)/$(IMAGE_NAME):$(IMAGE_TAG)/$${TAG_SUFFIX}:$${GITHUB_RUN_NUMBER} ; \
	done; \

update-version: ## Update version from VERSION file in all Dockerfiles
update-version:
	@for DOCKERFILE in $(DOCKERFILES);do \
		sed -i "0,/^ENV\ \VERSION .*$$/{s//ENV VERSION $(FILE_VERSION)/}" $${DOCKERFILE}; \
	done;
	@echo updated to version "$(FILE_VERSION)" Dockerfiles

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
