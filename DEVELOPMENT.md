# Development Notes

How to work on Edifice.

## Setuptools Build System

Setuptools `pyproject.toml` with [src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).

## uv dev environment

For development of this package, you can use the
[`uv venv`](https://docs.astral.sh/uv/pip/environments/#using-a-virtual-environment)
environment.

```console
uv venv
```
```console
source .venv/bin/activate
```
```console
uv sync --all-extras
```

In this environment the tests should pass.

```console
./run_tests.sh
```

In this environment
[publishing to PyPI](https://docs.astral.sh/uv/guides/publish/)
should work.

## Nix uv dev environment

The [Nix Flake](https://nixos.wiki/wiki/Flakes) has this development environment:

```console
nix develop .#impure
```

which provides everything for the **uv dev environment**.

## Nix uv2nix dev environment

The [Nix Flake](https://nixos.wiki/wiki/Flakes) has this development environment:

```console
nix develop .#uv2nix
```
[uv2nix](https://github.com/pyproject-nix/uv2nix)
environment with editable `src/edifice/` source files.

In this environment the tests should pass.

```console
./run_tests.sh
```

In this environment
[publishing to PyPI](https://docs.astral.sh/uv/guides/publish/)
should work.

## Nix apps

There are also Nix Flake `apps` for running the tests and the examples, see
[Examples](https://pyedifice.github.io/examples.html) or

```
nix flake show github:pyedifice/pyedifice
```

## Import Edifice

### uv

To use the latest Edifice with a **uv** `pyproject.toml` from Github
instead of PyPI, see
[Adding dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#adding-dependencies)

### Poetry

To use the latest Edifice with a Poetry `pyproject.toml` from Github
instead of PyPI, see
[Poetry git dependencies](https://python-poetry.org/docs/dependency-specification/#git-dependencies),
for example:

```
[tool.poetry.dependencies]
python = ">=3.10,<3.11"
pyedifice = {git = "https://github.com/pyedifice/pyedifice.git"}
PySide6-Essentials = "6.6.2"
```

## Release Checklist

- version agreement
   - `pyproject.toml` `version`
   - `docs/source/versions.rst`
   - `docs/source/conf.py` `release`
- `nix run .#run_tests`

```
nix develop .#uv2nix
```

```
uv build
```

```
uv publish
```

- `git tag`
- Publish [`docs`](docs/)
- Publish [Release](https://github.com/pyedifice/pyedifice/releases)

