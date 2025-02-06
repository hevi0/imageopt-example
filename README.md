# image-opt-example

# For local dev on OSX
Installing all of this can take a little while as `brew` builds these packages.

```
brew install vips
brew install freetype ImageMagick
export MAGICK_HOME=/opt/homebrew/opt/imagemagick
export PATH=$MAGICK_HOME/bin:$PATH
```


# Building docker containers

```
docker build ./ -f Dockerfile.imageopt -t imageopt

docker run imageopt
```