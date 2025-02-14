# For local dev on OSX
Installing all of this can take a little while as `brew` builds these packages.

```
brew install vips
brew install freetype ImageMagick
export MAGICK_HOME=/opt/homebrew/opt/imagemagick
export PATH=$MAGICK_HOME/bin:$PATH
```

# On Ubuntu 24.04+

```
sudo apt install libvips libvips-tools libvips-dev
sudo apt install imagemagick
```

# On all machines
After ImageMagick and libvips are properly configured on the machine we just need to setup
the Python environment

In the root directory of this project setup the venv. I employed the help of pyenv to get the versions of Python I wanted.
```
python -m venv ./venv
source ./venv/bin/activate
```

Install packages
```
pip install -r requirements.txt
```

Then run the origin server:
```
gunicorn origin-server:app -w 8 -b 0.0.0.0:8080 -k uvicorn.workers.UvicornWorker
```

Run the sync web service:
```
gunicorn -w 4 -b 0.0.0.0:8000 imageopt-sync-svc:app
```

and one of the load tests
```
# locust -f locustfile-sync.py --tag sync-imagemagick -u 100 -r 20 -t 5m
# locust -f locustfile-sync.py --tag sync-imagemagick-notemp -u 100 -r 20 -t 5m
# locust -f locustfile-sync.py --tag sync-libvips-notemp -u 100 -r 20 -t 5m
```

**or** run the async version of the web service
```
gunicorn imageopt-async-svc:app -w 4 -b 0.0.0.0:8001 -k uvicorn.workers.UvicornWorker
```

Run a load test for the async version
```
# locust -f locustfile-async.py --tag async-imagemagick -u 100 -r 20 -t 5m
# locust -f locustfile-async.py --tag async-imagemagick-notemp -u 100 -r 20 -t 5m
# locust -f locustfile-async.py --tag async-libvips-notemp -u 100 -r 20 -t 5m
```
