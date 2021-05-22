IMGNAME=sdelrio/hs110-exporter

.PHONY: all build-images build-test-images test-images push-images update-version

IMAGE_NAME ?= sdelrio/hs110-exporter
IMAGE_TAG ?= $(shell git rev-parse --short HEAD)
IMAGE_TEST_TAG ?= test
IMAGE_PREFIX ?= docker.pkg.github.com
GPR_TEST_TAG ?= build-cache-tests-no-buildkit
GPR_TAG ?= build-cache-no-buildkit
GITHUB_REPOSITORY ?= sdelrio/hs110-prometheus-exporter

VERSION ?= master
BUILDX_VERSION ?= 0.5.1
PLATFORM ?= linux/amd64,linux/arm/v7,linux/arm64
FILE_VERSION = $(shell cat VERSION)
DOCKERFILES ?= $(shell find . -maxdepth 1 -name 'Dockerfile*')

.DEFAULT: help
help:	## Show this help menu.
	@echo "Usage: make [TARGET ...]"
	@echo ""
	@egrep -h "#[#]" $(MAKEFILE_LIST) | sed -e 's/\\$$//' | awk 'BEGIN {FS = "[:=].*?#[#] "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

get-tag:	## Get tag used in build
	@echo -n ${IMAGE_TAG}

build-image:	## Build image locally
	$(info Make: Building container image x86_x64: $(IMAGE_NAME):${IMAGE_TAG})
	docker build \
		--progress=plain \
		--tag $(IMAGE_NAME):$(IMAGE_TAG) \
		.

build-images:	## Build images
build-images:
	$(info Make: Building container images: $(IMAGE_NAME):${IMAGE_TAG})
	docker buildx build \
		--platform $(PLATFORM) \
		--progress=plain \
		--tag $(IMAGE_NAME):$(IMAGE_TAG) \
		.

# https://collabnix.com/building-arm-based-docker-images-on-docker-desktop-made-possible-using-buildx/
# https://github.com/marketplace/actions/build-and-push-docker-images
# https://www.docker.com/blog/multi-arch-build-and-images-the-simple-way/
build-push:	## Build images and push 
	$(info Make: Building and push container images: $(IMAGE_NAME):${IMAGE_TAG})
	docker buildx build \
		--platform $(PLATFORM) \
		--progress=plain \
		--cache-from=$(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TAG)$${TAG_SUFFIX} \
		--tag $(IMAGE_NAME):$(IMAGE_TAG) \
		--push \
		.

	
build-images-gpr:	## Build images with Github Package Registry
build-images-gpr:
	@for DOCKERFILE in $(DOCKERFILES);do \
        export TAG_SUFFIX=`echo $${DOCKERFILE} | sed 's/\.\/Dockerfile//' | tr '.' '-'`; \
		echo "--> Pulling cache image $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TAG)$${TAG_SUFFIX}"; \
		docker pull $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG) || true ; \
		echo "--> Building $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TAG)$${TAG_SUFFIX}"; \
		docker build \
			-t $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TAG)$${TAG_SUFFIX} \
			--target=build \
			--cache-from=$(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TAG)$${TAG_SUFFIX} \
			--progress=plain -f $$DOCKERFILE \
			. || exit -1 ;\
		echo "----> Builder finished" ; \
		docker push $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TAG)$${TAG_SUFFIX} || true ; \
		echo "----> Cache push finished" ; \
		docker build \
			-t $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TAG)$${TAG_SUFFIX} \
			--cache-from=$(IMAGE_PREFIX)/$$GITHUB_REPOSITORY/$(GPR_TAG)$${TAG_SUFFIX} \
			--progress=plain -f $$DOCKERFILE \
			. || exit -1 ;\
		echo "----> Run Build finished" ; \
		docker tag \
			$(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TAG)$${TAG_SUFFIX} \
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
	@echo "--> Building test image $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG)"; \
	docker pull $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG) || true ; \
	echo "----> pull finished" ; \
	docker build \
		-t $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG) \
		--cache-from=$(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG) \
		--target=test --progress=plain -f Dockerfile . || exit -2; \
	echo "----> build finished" ; \
	docker push $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG) || true ; \
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
	@echo "--> Testing $(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG)"; \
	docker run --rm -t \
		$(IMAGE_PREFIX)/$(GITHUB_REPOSITORY)/$(GPR_TEST_TAG)

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
	@tox -e coverage,py3

qemu-arm-linux:	## Prepare qemu on linux to run arm
qemu-arm-linux:
	@sudo apt-get install -yqemu binfmt-support qemu-user-static
	@docker run --rm --privileged multiarch/qemu-user-static:register --reset

buildx:	## Install buildx
	@mkdir -p ~/.docker/cli-plugins
	@wget https://github.com/docker/buildx/releases/download/v$(BUILDX_VERSION)/buildx-v$(BUILDX_VERSION).linux-amd64 \
		-O ~/.docker/cli-plugins/docker-buildx
	@chmod a+x ~/.docker/cli-plugins/docker-buildx

kaniko:	## Build image with kaniko
	@echo Kaniko "$(IMAGE_NAME):$(IMAGE_TAG)"
	docker run \
	-v "$$HOME"/.docker/config.json:/kaniko/.docker/config.json \
	-v $(shell pwd):/workspace \
	gcr.io/kaniko-project/executor:latest \
	--no-push \
	--dockerfile /workspace/Dockerfile \
	--destination "$(IMAGE_NAME):$(IMAGE_TAG)" \
	--context dir:///workspace/
