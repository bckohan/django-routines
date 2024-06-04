[Poetry]: https://python-poetry.org/
[mypy]: http://mypy-lang.org/
[django-pytest]: https://pytest-django.readthedocs.io/en/latest/
[pytest]: https://docs.pytest.org/en/stable/
[Sphinx]: https://www.sphinx-doc.org/en/master/
[readthedocs]: https://readthedocs.org/
[me]: https://github.com/bckohan
[black]: https://black.readthedocs.io/en/stable/
[pyright]: https://github.com/microsoft/pyright
[ruff]: https://docs.astral.sh/ruff/

# Contributing

Contributions are encouraged! Please use the issue page to submit feature requests or bug reports. Issues with attached PRs will be given priority and have a much higher likelihood of acceptance. Please also open an issue and associate it with any submitted PRs. That said, the aim is to keep this library as lightweight as possible. Only features with broad-based use cases will be considered.

We are actively seeking additional maintainers. If you're interested, please [contact me](https://github.com/bckohan).

## Installation

`django-routines` uses [Poetry](https://python-poetry.org/) for environment, package, and dependency management:

```shell
poetry install
```

## Documentation

`django-routines` documentation is generated using [Sphinx](https://www.sphinx-doc.org/en/master/) with the [readthedocs](https://readthedocs.org/) theme. Any new feature PRs must provide updated documentation for the features added. To build the docs run doc8 to check for formatting issues then run Sphinx:

```bash
cd ./doc
poetry run doc8 --ignore-path build --max-line-length 100
poetry run make html
```

## Static Analysis

`django-routines` uses [ruff](https://docs.astral.sh/ruff/) for Python linting, header import standardization and code formatting. [mypy](http://mypy-lang.org/) and [pyright](https://github.com/microsoft/pyright) are used for static type checking. Before any PR is accepted the following must be run, and static analysis tools should not produce any errors or warnings. Disabling certain errors or warnings where justified is acceptable:

```bash
./check.sh
```

To run static analysis without automated fixing you can run:

```bash
./check.sh --no-fix
```

## Running Tests

`django-routines` is set up to use [pytest](https://docs.pytest.org/en/stable/) to run unit tests. All the tests are housed in `tests/tests.py`. Before a PR is accepted, all tests must be passing and the code coverage must be at 100%. A small number of exempted error handling branches are acceptable.

To run the full suite:

```shell
poetry run pytest
```

To run a single test, or group of tests in a class:

```shell
poetry run pytest <path_to_tests_file>::ClassName::FunctionName
```

For instance, to run all tests in Tests, and then just the test_command test you would do:

```shell
poetry run pytest tests/tests.py::Tests
poetry run pytest tests/tests.py::Tests::test_command
```
