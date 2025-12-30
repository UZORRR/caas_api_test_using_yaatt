TEST_BASE_IMAGE=iamuzorr/yaatt:latest
ROOT_DIR=$(shell pwd)

.SILENT:
.PHONY: help

## Prints this help screen
help:
	printf "Available targets\n\n"
	awk '/^[a-zA-Z\-\_0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "%-15s %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

## Pull test image
build:
	docker pull $(TEST_BASE_IMAGE)

## Run all tests
test: 
	docker run --env-file $(ROOT_DIR)/.env -v $(ROOT_DIR)/tests:/app/tests -t $(TEST_BASE_IMAGE)

generate:
	docker run -v $(ROOT_DIR)/tests:/app/tests -t $(TEST_BASE_IMAGE) bun run generate
