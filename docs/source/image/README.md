### EdificePyramid.svg source

https://en.m.wikipedia.org/wiki/File:Pyramid.svg

### Generate EdificePyramid.ico

```
nix run nixpkgs#imagemagick -- convert -resize 32x32 -background none EdificePyramid.svg EdificePyramid.ico
```