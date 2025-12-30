# POC - CaaS API Test

API tests for CaaS written to be run using [iamuzorr/yaatt](https://hub.docker.com/r/iamuzorr/yaatt)

## Requirement
* Create an .env file in the root directory.
* Add variables `CAAS_BASE_URL` and `CAAS_API_KEY`

## Usage
#### Pull base image (one-time only)
```sh
make build
```

#### Run tests
```sh
make test
```
#### Generate new test file
```sh
make generate
```

## What now?
I'd love get some feedback.

- Did you try to write a new tests? How did you find it? What did you like? What did you hate?
- What about Postman would you miss if you replaced it with this?
- etc.