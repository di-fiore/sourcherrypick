IMAGE_NAME := sourcherrypick
IMAGE_VERSION := latest

.DEFAULT_GOAL := help
.PHONY: help build demolish

help:  ## Print Make usage information
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

build: ## Build docker container image with data pre-loaded
	docker build --progress plain -t ${IMAGE_NAME}:${IMAGE_VERSION} .

demolish:  ## Remove docker container image
	docker image rm ${IMAGE_NAME}:${IMAGE_VERSION} && docker system prune
