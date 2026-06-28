BASE_IMAGE=iamuzorr/yaatt:latest
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
	docker pull $(BASE_IMAGE)

## Run all tests
test:
	$(ROOT_DIR)/scripts/run-tests.sh

## Run a single test file (e.g. make test-one FILE=2025_12_30T16_54_22Z_test.yml)
test-one:
	@test -n "$(FILE)" || (echo "Usage: make test-one FILE=<filename>.yml" && exit 1)
	$(ROOT_DIR)/scripts/run-test-one.sh "$(FILE)"

generate:
	docker run -v $(ROOT_DIR)/tests:/app/tests -t $(BASE_IMAGE) bun run generate
