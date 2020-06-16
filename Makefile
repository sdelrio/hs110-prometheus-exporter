IMGNAME=sdelrio/hs110-exporter

.PHONY: all build-images build-test-images test-images push-images update-version

IMAGE_NAME ?= sdelrio/hs110-exporter
IMAGE_TAG ?= latest
IMAGE_TEST_TAG ?= test
IMAGE_PREFIX ?= docker.pkg.github.com
GPR_TEST_TAG ?= build-cache-tests-no-buildkit
GPR_TAG ?= build-cache-no-buildkit

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

build-images-gpr:	## Build images with Github Package Registry
build-images-gpr:
	@for DOCKERFILE in $(DOCKERFILES);do \
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Pulling cache image $(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TAG)$${TAG_SUFFIX}"; \
		docker pull $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG) || true ; \
		echo "--> Building $(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TAG)$${TAG_SUFFIX}"; \
		docker build \
			-t $(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TAG)$${TAG_SUFFIX} \
			--cache-from=$(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TAG)$${TAG_SUFFIX} \
			--progress=plain -f $$DOCKERFILE \
			. || exit -1 ;\
		echo "----> Build finished" ; \
		docker push $(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TAG)$${TAG_SUFFIX} || true ; \
		echo "----> Cache push finished" ; \
		docker tag \
			$(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TAG)$${TAG_SUFFIX} \
			$(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX} || exit 2 \
		echo "----> Dockerhub tag image finished" ; \
	done; \


build-test-image:	## Build 1 image to run tests
build-test-image:
	@echo "--> Building test image $(IMAGE_NAME):$(IMAGE_TEST_TAG)"; \
	docker build --target=test --progress=plain -f Dockerfile \
		-t $(IMAGE_NAME):$(IMAGE_TEST_TAG) \
		. || exit -2 ;\

build-test-image-gpr:	## Build 1 image to run testswith Github Package Registry as cache
build-test-image-gpr:
	@echo "--> Building test image $(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TEST_TAG)"; \
	docker pull $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG) || true ; \
	echo "----> pull finished" ; \
	docker build \
		-t $(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TEST_TAG) \
		--cache-from=$(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TEST_TAG) \
		--target=test --progress=plain -f Dockerfile . || exit -2; \
	echo "----> build finished" ; \
	docker push $(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TEST_TAG) || true ; \
	echo "----> cache push finished" ; \

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

test-image-gpr:	## Tests with the Dockerfile image
test-image-gpr: build-test-image-gpr
	@echo "--> Testing $(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TEST_TAG)"; \
	docker run --rm -t \
		$(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TEST_TAG)

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
		docker push $(IMAGE_NAME):$(IMAGE_TAG)$${TAG_SUFFIX} ; \
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
		sed -i "0,/^VERSION .*$$/{s//VERSION = $(FILE_VERSION)/}" hs110exporter.py; \
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
