
Docs generated with the [Spinx Book Theme](https://sphinx-book-theme.readthedocs.io/en/latest/tutorials/get-started.html).

In the poetry2nix development environment,

```
nix develop
```

[run the build](https://www.sphinx-doc.org/en/master/usage/quickstart.html#running-the-build)

```
make html
```

Currently we need to set the locale to build the docs
because of https://github.com/sphinx-doc/sphinx/issues/11739

```
LC_ALL=C.UTF-8 make html
```

Manually update the https://github.com/pyedifice/pyedifice.github.io website:

```
rm -r ../../pyedifice.github.io/*
```
```
cp -r build/html/* ../../pyedifice.github.io/
```
