# Contributing

Contributions are encouraged! Please use the issue page to submit feature requests or bug reports. Issues with attached PRs will be given priority and have a much higher likelihood of acceptance. Please also open an issue and associate it with any submitted PRs. That said, the aim is to keep this library as lightweight as possible. Only features with broad-based use cases will be considered.

We are actively seeking additional maintainers. If you're interested, please [contact me](https://github.com/bckohan).

## Installation

### Install Just

We provide a platform independent justfile with recipes for all the development tasks. You should [install just](https://just.systems/man/en/installation.html) if it is not on your system already.

[django-routines](https://pypi.python.org/pypi/django-routines) uses [uv](https://docs.astral.sh/uv) for environment, package, and dependency management. ``just setup`` will install the necessary build tooling if you do not already have it:

 ```bash
just setup
```

Setup also may take a python version:

```bash
just setup 3.12
```

If you already have uv and python installed running install will just install the development dependencies:

 ```bash
just install
```

## Documentation


`django-routines` documentation is generated using [Sphinx](https://www.sphinx-doc.org) with the [furo](https://github.com/pradyunsg/furo) theme. Any new feature PRs must provide updated documentation for the features added. To build the docs run doc8 to check for formatting issues then run Sphinx:

```bash
just install-docs # install the doc dependencies
just docs  # builds docs
just check-docs  # lint the docs
just check-docs-links  # check for broken links in the docs
```

Run the docs with auto rebuild using:

```bash
just docs-live
```

## Static Analysis

`django-routines` uses [ruff](https://docs.astral.sh/ruff/) for Python linting, header import standardization and code formatting. [mypy](http://mypy-lang.org/) and [pyright](https://github.com/microsoft/pyright) are used for static type checking. Before any PR is accepted the following must be run, and static analysis tools should not produce any errors or warnings. Disabling certain errors or warnings where justified is acceptable:


To fix formatting and linting problems that are fixable run:

```bash
just fix
```

To run all static analysis without automated fixing you can run:

```bash
just check
```

To format source files you can run:

```bash
just format
```

## Running Tests

`django-routines` is set up to use [pytest](https://docs.pytest.org/en/stable/) to run unit tests. All the tests are housed in `tests/test_*.py`. Before a PR is accepted, all tests must be passing and the code coverage must be at 100%. A small number of exempted error handling branches are acceptable.

To run the full suite:

```bash
just test
```

To run a single test, or group of tests in a class:

```bash
just test <path_to_tests_file>::ClassName::FunctionName
```

For instance, to run all of the dictionary config tests in test_dict, and then just the test_command test from the dictionary tests you would do:

```bash
just test tests/test_dict.py
just test tests/test_dict.py::SettingsAsDictTests::test_command
```


## Issuing Releases

The release workflow is triggered by tag creation. You must have [git tag signing enabled](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits). Our justfile has a release shortcut:

```bash
just release x.x.x
```

## Just Recipes

```bash
build                        # build docs and package
build-docs                   # build the docs
build-docs-html              # build html documentation
build-docs-pdf               # build pdf documentation
check                        # run all static checks
check-docs                   # lint the documentation
check-docs-links             # check the documentation links for broken links
check-format                 # check if the code needs formatting
check-lint                   # lint the code
check-package                # run package checks
check-readme                 # check that the readme renders
check-types                  # run static type checking
clean                        # remove all non repository artifacts
clean-docs                   # remove doc build artifacts
clean-env                    # remove the virtual environment
clean-git-ignored            # remove all git ignored files
clean_manage *COMMAND
coverage                     # generate the test coverage report
docs                         # build and open the documentation
docs-live                    # serve the documentation, with auto-reload
fetch-refs LIB               # fetch the intersphinx references for the given package
fix                          # fix formatting, linting issues and import sorting
format                       # format the code and sort imports
install *OPTS="--all-extras" # update and install development dependencies
install-docs                 # install documentation dependencies
install-precommit            # install git pre-commit hooks
install_uv                   # install the uv package manager
lint                         # sort the imports and fix linting issues
manage *COMMAND              # run the django admin
open-docs                    # open the html documentation
precommit                    # run the pre-commit checks
release VERSION              # issue a relase for the given semver string (e.g. 2.1.0)
run +ARGS                    # run the command in the virtual environment
runserver                    # run the development server
setup python="python"        # setup the venv, pre-commit hooks
sort-imports                 # sort the python imports
test *TESTS                  # run tests
test-all                     # run all tests
test-lock +PACKAGES          # lock to specific python and versions of given dependencies
validate_version VERSION     # validate the given version string against the lib version
```
