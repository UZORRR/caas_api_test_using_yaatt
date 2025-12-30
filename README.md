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

ℹ️ These runs the tests in your tests folder.

#### Generate new test file

```sh
make generate
```

ℹ️ You can also create a new file in the `./tests` folder manually.

## Task
Please try to do the following.

#### Task 1: Review the existing test files
* Have a quick breeze through to the files in the `./tests` folder and their content to familiarise yourself with the format.

#### Task 2: Add a New Test

* Create a new test file in the `./tests` directory.
* Add at least one request, and one assertion.
* Run the tests and confirm your new test is executed.
* Review the output.

#### Task 3: Make a Test Fail (on purpose)

* Modify an existing test so that one assertion fails
* Run the tests again
* Review the output and error message

## Feedback #prettypls ❤️❤️❤️

#### Getting Started & First Run

* Was it obvious how to run the tests?
* Did anything unexpected happen on your first run?
* Did the output clearly show what was happening?

#### Writing & Modifying Tests

* How did you approach adding a new test (copying an example, starting from scratch, used `make generate` command etc.)?
* Was the test file structure easy to understand?
* Did the test file read clearly once written?
* Was there anything you wanted to test but couldn’t express easily?

#### Failures & Debugging

* When a test failed, did you immediately understand why?
* Was the failure message actionable?
* Did the output clearly show expected vs actual values?
* Did you ever feel unsure whether a failure was caused by your test or the tool?

#### Workflow & Comparison

* Where would this tool fit into your workflow (local dev, CI, pre-merge checks, etc.)?
* In what situations would you still reach for Postman?
* In what situations would you prefer this tool instead?

#### Overall Impression

* What frustrated you the most?
* What pleasantly surprised you?
* Would you use this tool again?
* Would you recommend it to a teammate? Why or why not?
* What's the first thing you would improve?
* If you were explaining this tool to a teammate in one sentence, what would you say?