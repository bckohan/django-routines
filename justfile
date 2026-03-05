set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set unstable := true
set script-interpreter := ['uv', 'run', '--script']

export PYTHONPATH := source_directory()

[private]
default:
    @just --list --list-submodules

# run the django admin
[script]
manage *COMMAND:
    import os
    import sys
    from django.core import management
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    management.execute_from_command_line(sys.argv + "{{ COMMAND }}".split(" "))

[script]
clean_manage *COMMAND:
    import os
    import sys
    from django.core import management
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.base_settings"
    management.execute_from_command_line(sys.argv + "{{ COMMAND }}".split(" "))

# install the uv package manager
[linux]
[macos]
install-uv:
    curl -LsSf https://astral.sh/uv/install.sh | sh

# install the uv package manager
[windows]
install-uv:
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# setup the venv, pre-commit hooks
setup python="python":
    uv venv -p {{ python }}
    @just install-precommit

# install git pre-commit hooks
install-precommit:
    @just run --no-default-groups --group precommit --exact --isolated pre-commit install

# update and install development dependencies
install *OPTS="--all-extras":
    uv sync {{ OPTS }}

# install documentation dependencies
_install-docs:
    uv sync --no-default-groups --group docs --all-extras

# run the development server
runserver:
    @just manage makemigrations
    @just manage migrate
    @just manage runserver 8027

# run static type checking
check-types *ENV:
    @just run {{ ENV }} --no-default-groups --all-extras --group typing mypy
    @just run {{ ENV }} --no-default-groups --all-extras --group typing pyright

# run package checks
check-package:
    uv pip check

# remove doc build artifacts
[script]
clean-docs:
    import shutil
    shutil.rmtree('./doc/build', ignore_errors=True)

# remove the virtual environment
clean-env:
    python -c "import shutil, pathlib; p=pathlib.Path('.venv'); shutil.rmtree(p, ignore_errors=True) if p.exists() else None"

# remove all git ignored files
clean-git-ignored:
    git clean -fdX

# remove all non repository artifacts
clean: clean-docs clean-env clean-git-ignored

# build html documentation
build-docs-html:
    @just run --no-default-groups --group docs --all-extras --isolated --exact sphinx-build --fresh-env --builder html --doctree-dir ./doc/build/doctrees ./doc/source ./doc/build/html

[script]
_open-pdf-docs:
    import webbrowser
    from pathlib import Path
    webbrowser.open(f"file://{Path('./doc/build/pdf/djangoroutines.pdf').absolute()}")

# build pdf documentation
build-docs-pdf:
    @just run --no-default-groups --group docs --all-extras --isolated --exact sphinx-build --fresh-env --builder latex --doctree-dir ./doc/build/doctrees ./doc/source ./doc/build/pdf
    make -C ./doc/build/pdf
    @just _open-pdf-docs

# build the docs
build-docs: build-docs-html

# build docs and package
build: build-docs-html
    uv build

# open the html documentation
[script]
open-docs:
    import os
    import webbrowser
    webbrowser.open(f'file://{os.getcwd()}/doc/build/html/index.html')

# build and open the documentation
docs: build-docs-html open-docs

[script]
_available_port:
    import socket;
    s=socket.socket();
    s.bind(('',0));
    print(s.getsockname()[1]);s.close()

# serve the documentation, with auto-reload
docs-live:
    @just run --no-default-groups --group docs --all-extras --isolated --exact sphinx-autobuild doc/source doc/build --open-browser --watch src --port {{ shell("just _available_port") }} --delay 1

_link_check:
    -uv run --no-default-groups --group docs --all-extras sphinx-build -b linkcheck -Q -D linkcheck_timeout=10 ./doc/source ./doc/build

# check the documentation links for broken links
[script]
check-docs-links: _link_check
    import os
    import sys
    import json
    from pathlib import Path
    # The json output isn't valid, so we have to fix it before we can process.
    data = json.loads(f"[{','.join((Path(os.getcwd()) / 'doc/build/output.json').read_text().splitlines())}]")
    broken_links = [link for link in data if link["status"] not in {"working", "redirected", "unchecked", "ignored"}]
    if broken_links:
        for link in broken_links:
            print(f"[{link['status']}] {link['filename']}:{link['lineno']} -> {link['uri']}", file=sys.stderr)
        sys.exit(1)

# lint the documentation
check-docs *ENV:
    @just run {{ ENV }} --no-default-groups --group docs doc8 --ignore-path ./doc/build --max-line-length 100 -q ./doc

# fetch the intersphinx references for the given package
[script]
fetch-refs LIB: _install-docs
    import os
    from pathlib import Path
    import logging as _logging
    import sys
    import runpy
    from sphinx.ext.intersphinx import inspect_main
    _logging.basicConfig()

    libs = runpy.run_path(Path(os.getcwd()) / "doc/source/conf.py").get("intersphinx_mapping")
    url = libs.get("{{ LIB }}", None)
    if not url:
        sys.exit(f"Unrecognized {{ LIB }}, must be one of: {', '.join(libs.keys())}")
    if url[1] is None:
        url = f"{url[0].rstrip('/')}/objects.inv"
    else:
        url = url[1]

    raise SystemExit(inspect_main([url]))

# lint the code
check-lint *ENV:
    @just run {{ ENV }} --no-default-groups --group lint ruff check --select I
    @just run {{ ENV }} --no-default-groups --group lint ruff check

# check if the code needs formatting
check-format *ENV:
    @just run {{ ENV }} --no-default-groups --group lint ruff format --check

# check that the readme renders
check-readme *ENV:
    @just run {{ ENV }} --no-default-groups --group lint -m readme_renderer ./README.md -o /tmp/README.html

# sort the python imports
sort-imports *ENV:
    @just run {{ ENV }} --no-default-groups --group lint ruff check --fix --select I

# format the code and sort imports
format *ENV: sort-imports
    just --fmt --unstable
    @just run {{ ENV }} --no-default-groups --group lint ruff format

# sort the imports and fix linting issues
lint *ENV: sort-imports
    @just run {{ ENV }} --no-default-groups --group lint ruff check --fix

# fix formatting, linting issues and import sorting
fix *ENV:
    @just lint {{ ENV }}
    @just format {{ ENV }}

# run all static checks
check *ENV:
    @just check-lint {{ ENV }}
    @just check-format {{ ENV }}
    @just check-types {{ ENV }}
    @just check-package
    @just check-docs {{ ENV }}
    @just check-readme {{ ENV }}

# run all checks including documentation link checking
check-all *ENV:
    @just check {{ ENV }}
    @just check-docs-links

# erase any coverage data
coverage-erase:
    @just run --no-default-groups --group coverage coverage erase

# generate the test coverage report
coverage:
    @just run --no-default-groups --group coverage coverage combine --keep *.coverage
    @just run --no-default-groups --group coverage coverage report
    @just run --no-default-groups --group coverage coverage xml

# run tests without the rich extra (isolated venv)
test-no-rich *ENV:
    uv run --no-default-groups --exact --group test --isolated {{ ENV }} pytest --cov-append

# run tests with the rich extra (isolated venv)
test-rich *ENV:
    uv run --no-default-groups --exact --all-extras --group test --isolated {{ ENV }} pytest --cov-append

# run all tests (isolated venv)
test-all *ENV: coverage-erase
    @just test-rich {{ ENV }}
    @just test-no-rich {{ ENV }}

# run tests
test *TESTS:
    @just run --group test --no-sync pytest {{ TESTS }}

# run the pre-commit checks
precommit:
    @just run pre-commit

# run the command in the virtual environment
run +ARGS:
    uv run {{ ARGS }}

# validate the given version string against the lib version
[script]
validate_version VERSION:
    import re
    import tomllib
    import django_routines
    from packaging.version import Version
    raw_version = "{{ VERSION }}".lstrip("v")
    version_obj = Version(raw_version)
    # the version should be normalized
    assert str(version_obj) == raw_version
    # make sure all places the version appears agree
    assert raw_version == tomllib.load(open('pyproject.toml', 'rb'))['project']['version']
    assert raw_version == django_routines.__version__
    print(raw_version)

# issue a relase for the given semver string (e.g. 2.1.0)
release VERSION:
    @just validate_version v{{ VERSION }}
    git tag -s v{{ VERSION }} -m "{{ VERSION }} Release"
    git push origin v{{ VERSION }}
