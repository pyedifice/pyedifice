# Development Notes

How to work on Edifice.

## Nix Build System

There is a [Nix Flake](https://nixos.wiki/wiki/Flakes) with
three development environments:

1. `nix develop .#default`

   Nixpkgs `pythonWithPackages` environment.

   In this environment the tests should pass.

       ./run_tests.sh

2. `nix develop .#poetry`

   Poetry environment.

   In this environment the tests should pass.

       poetry install --sync --all-extras --no-root
       poetry shell
       ./run_tests.sh

   In this environment
   [publishing to PyPI](https://python-poetry.org/docs/libraries/#publishing-to-pypi)
   should work.

3. `nix develop .#poetry2nix`

   poetry2nix [`mkPoetryEnv`](https://github.com/nix-community/poetry2nix#mkpoetryenv)
   environment with editable `edifice/` source files.

   In this environment the tests should pass.

       ./run_tests.sh

   In this environment building the [Docs](docs) should work.

There are also Nix Flake `apps` for running the tests and the examples, see
[Examples](https://pyedifice.github.io/examples.html) or

```
nix flake show github:pyedifice/pyedifice
```
## Release Checklist

- `pyproject.toml` `version`
- `docs/source/version.rst`
- `nix run .#run_tests`

```
nix develop .#poetry
```

```
poetry build
```

```
poetry publish
```

- `git tag`
- Publish `docs`
