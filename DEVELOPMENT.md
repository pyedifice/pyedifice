# Development Notes

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