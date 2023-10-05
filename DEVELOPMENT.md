# Development Notes

## Release Checklist

- `pyproject.toml` `version`
- `docs/source/version.rst`
- `nix run .#run_tests`
- `git tag`

```
nix develop .#poetry
```

```
poetry build
```

```
poetry publish
```
