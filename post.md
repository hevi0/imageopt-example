# Comparing ImageMagick and libvips in image optimization task



## Situation
### an old service that was in KTLO mode (PHP)
I'm taking a very simple service that resizes images using imagemagick and seeing if I can find optimizations that would improve throughput and latency. The architecture:

Some things to note about the architecture:

## Architecture changes
A brief aside about the architecture as there is need for improvement. No way we want to retrieve data directly from an origin provided by the client since an impact of an outage can leak beyond the client themselves. Also, when there is a cache miss the response times are often around multiple seconds per image. The way to solve this is to have an ingestion process that will take data delivered from the client and store it in a cloud bucket that is both "nearer" in the latency sense and is something we can ensure uptime, data lifecycle, compliance etc.

I'm going with a separate consumer to handle the ingestion from an event bus that is taking in the image assets from some ETL scripts. Consumer traffic pattern is significantly different from the the service. I expect large amount (10s of thousands) of images, intermittently. We want to process these in a reasonable amount of time (order of minutes, but not in any way similar to responding to a web request). This could be done with a Cloud Function, rather than a dedicated service, potentially reducing maintenance.

Based on existing request patterns, I expect the web-facing service to receive about 1% of the traffic since the cache miss rate is about 1%.

### Implementation limits
Descending down into software implementation, we are also dealing with code written without an Async I/O model. If we could switch over to Async I/O we wouldn't necessarily see a latency improvement as an individual request still needs the I/O operations to occur before the response can be received. However, it can help with throughput and enable us to handle more requests with fewer resources. Being able to progress more requests could allow the average latency experienced to be lower given the available resources are the same.

Of course, the image processing performed by ImageMagick and libvips will be CPU bounded rather than I/O bounded. The question is whether the libvips improvements would be substantial enough that we see a difference in any metric. As I thought about it, I suspected it could be beneficial to our throughput along with the switch over to Async I/O.

The service is designed do the following for an image request:
- Resize based on the width requested, maintaining the aspect ratio
- Use a predefined quality, say 80, for JPEGs
- Convert PNG images to WEBP for payload reduction

The consumer could do certain things ahead-of-time, such as converting PNG to WEBP. Efficiently processing images in bulk this way could be important. However, for the time I decided to keep the responsibility of the consumer to the following:
- Validating images meet certain criteria (e.g. formatting, size) and reporting rejections in the results
- Placing image in Cloud storage and recording the URL for the results report
- Produce an event message that will report the result for each image

I expected that certain widths would be most commonly requested, but we could not
fully know all possible sizes. For the time being, I decided not to do anything special for any specific image sizes.

### temp files are not necessary
Saving images to local disk shouldn't be necessary while resizing/optimizing an image, so that saves at least a write and read I/O operation.

### notice that it would take some time to perform optimization for images
Now, some of this had to do with how the origin servers were configured. We were in some instances getting the data directly from a client's own data source. No good, obviously, for both security and reputational perspective. In my case, I also cared how having the assets stored "closer" to the service would positively impact the response times. We could reliably get somewhere in the ballpark of 50ms response times when the assets parked in the same cluster as the service.


## Further observations of the implementation





### ImageMagick to libvips
libvips claims a 6-7 times improvement over ImageMagick. 

## The tests

- Blocking I/O, ImageMagick, temp file (the original implementation)
- Blocking I/O, ImageMagick, in-memory
- Blocking I/O, libvips, in-memory

- Non-blocking I/O, ImageMagick, temp file
- Non-blocking I/O, ImageMagick, in-memory
- Non-blocking I/O, libvips, in-memory

A handful of images are served using a local running static server (`origin-server.py`) with some simulated latency to represent cloud storage. An example URL:

```
http://localhost:8080/Desert_Electric.jpg
```

I created a test service with blocking I/O (`imageopt-sync-svc.py`) and one with non-blocking I/O (`imageopt-async-svc.py`) that will take the request and optimize the image after fetching it from the origin. An example request:

```
http://localhost:8000/sync-imagemagick/Desert_Electric.jpg
```

And there was an endpoint for each of the 6 services under test:

- `http://localhost:8000/sync-imagemagick/Desert_Electric.jpg`
- `http://localhost:8000/sync-imagemagick-notemp/Desert_Electric.jpg`
- `http://localhost:8000/sync-pyvips-notemp/Desert_Electric.jpg`
- `http://localhost:8001/async-imagemagick/Desert_Electric.jpg`
- `http://localhost:8001/async-imagemagick-notemp/Desert_Electric.jpg`
- `http://localhost:8001/async-pyvips-notemp/Desert_Electric.jpg`

I used the locust library to run the load tests

### Establishing the simulated origin performs well enough
I had to make sure the server running the origin could handle the expected load. Traffic to the CDN could be expected to be in the hundreds per second, so I assumed we should expect 1000 req/s. With a 1% cache-miss I'm assuming about 10 req/s reach the origin. At the same time, there can be spikes of traffic reaching the origin for various cache-busting scenarios.

With that information, I decided to target handling 100 req/s with a latency under 200ms.

```
# Run the origin server locally
gunicorn origin-server:app -w 8 -b 0.0.0.0:8080 -k uvicorn.workers.UvicornWorker

# Run with 100 peak users, spawning 20 users at a time, for 5 minutes
locust --processes 4 -f locustfile-origin.py -u 100 -r 20 -t 5m
```

The load test showed that the simulated origin can comfortably handle 300+ req/s.
![Origin server load test](https://hevi0.github.io/assets/imageopt/origin-server-load.png)

## Simple tests to provide some evidence for the hypothesis

I wrote a script that just cycles through the images on the server for each version

```bash
# Run the origin server locally
gunicorn origin-server:app -w 8 -b 0.0.0.0:8080 -k uvicorn.workers.UvicornWorker

python imageopt-perftest.py
```

```
--- SyncIO ImageMagick (wand) with temp file ---
Number of image requests: 6
Runtime: 0.9465919170179404
Est. time spent fetching images: 0.38345861434936523
Peak memory use: 9569161

--- SyncIO libvips (pyvips) with temp file ---
Number of image requests: 6
Runtime: 0.9112042500055395
Est. time spent fetching images: 0.3740732669830322
Peak memory use: 9491514

--- AsyncIO ImageMagick (wand) with temp file ---
Number of image requests: 6
Runtime: 0.6063121249899268
Est. time spent fetching images: 0.3504221670445986
Peak memory use: 17100641

--- AsyncIO ImageMagick (wand) In-memory ---
Number of image requests: 6
Runtime: 0.5966014160076156
Est. time spent fetching images: 0.34820599999511614
Peak memory use: 15985168

--- AsyncIO libvips (pyvips) In-memory ---
Number of image requests: 6
Runtime: 0.36186812503729016
Est. time spent fetching images: 0.3397534160176292
Peak memory use: 15903523
```

There is an additional two tests that do a larger batch of requests cycling through the images on the server.

```
--- Bulk SyncIO ImageMagick (wand) with temp file ---
Number of image requests: 100
Runtime: 15.376233540999237
Est. time spent fetching images: 6.2957587242126465
Peak memory use: 9508735

--- Bulk AsyncIO libvips (pyvips) In-memory ---
Number of image requests: 100
Runtime: 6.228253667009994
Est. time spent fetching images: 5.573981120891403
Peak memory use: 9565989
```

These results agree with the smaller test that we could expect to see images get processed almost well above 2x faster than the original implementation. With some math, we can see that on the average time spent fetching images is around the 50-60ms range. That's what we expect from the origin and shows that libvips minimizes the runtime.

An aside, the estimates of the time spent fetching the images can be thrown off in the async cases as blocking will be included in the time calculations. I tried to minimize the possibility of blocking for this test, at least, by limiting the number of simultaneous tasks.

### libvips Concurrency considerations
libvips touts the ability to take advantage of all the cores on the machine to parallelize its work. However, what would it look like if libvips could not take advantage of so many cores?

Turning down the concurrency still showed libvips to be better, but that should be considered for sizing of pods/cloud instances. You'll want a box that provides some true parallelism.

```
VIPS_CONCURRENCY=1 python imageopt-perftest.py
```

```
--- Bulk AsyncIO libvips (pyvips) In-memory ---
Number of image requests: 100
Runtime: 7.248223875008989
Est. time spent fetching images: 5.578979282698128
Peak memory use: 11852878
```

```
VIPS_CONCURRENCY=2 python imageopt-perftest.py
```

```
--- Bulk AsyncIO libvips (pyvips) In-memory ---
Number of image requests: 100
Runtime: 6.484328041959088
Est. time spent fetching images: 5.674379328323994
Peak memory use: 11880271
```

## The real test

Now for a more realistic test, I set up some locust scripts to hit the services to their limit. Of course, I tested on boxes that are not very big and the absolute numbers for response time and throughput are not so important. It's the relative numbers for each that I cared about.

Each test consisted of 100 users making a request every 0.2 to 2 seconds.

### Test setup for sync I/O versions

```
# Run the origin server locally
gunicorn origin-server:app -w 8 -b 0.0.0.0:8080 -k uvicorn.workers.UvicornWorker

# Run the optimization service locally
gunicorn -w 4 -b 0.0.0.0:8000 imageopt-sync-svc:app
```

With the origin and sync I/O version of the service up, I could run the load tests:

```bash
locust -f locustfile-sync.py --tag sync-imagemagick -u 100 -r 20 -t 5m
```

```bash
locust -f locustfile-sync.py --tag sync-imagemagick-notemp -u 100 -r 20 -t 5m
```

```bash
locust -f locustfile-sync.py --tag sync-pyvips-notemp -u 100 -r 20 -t 5m
```

### Results from the sync I/O tests

![Sync I/O - ImageMagick - Temp File](https://hevi0.github.io/assets/imageopt/user100/async-imagemagick-load.png)

![Sync I/O - ImageMagick - No Temp File](https://hevi0.github.io/assets/imageopt/user100/async-imagemagick-notemp-load.png)

![Sync I/O - libvips - No Temp File](https://hevi0.github.io/assets/imageopt/user100/async-libvips-notemp-load.png)

It seems removing the extra read and write I/O with a temp file was not so impactful. As it involves local disk, it's probably lost in the variance of the network communication to fetch from the origin. Recalling the latency numbers for reading and writing from an SSD, it's probably around 1ms vs the 50-100ms latency fetching the image.

A slight surprise is that the CPU-bound work to perform the image operations is enough to be on the order of the fetch latency. This makes the libvips implementation improvements significant. It nearly halves the response times and boosts the requests per second to the upper 30s.

### Results from the async I/O tests

![Async  I/O - ImageMagick - Temp File](https://hevi0.github.io/assets/imageopt/user100/async-imagemagick-load.png)

![Async  I/O - ImageMagick - No Temp File](https://hevi0.github.io/assets/imageopt/user100/async-imagemagick-notemp-load.png)

![Async  I/O - libvips - No Temp File](https://hevi0.github.io/assets/imageopt/user100/async-libvips-notemp-load.png)

There is improvement across all async I/O versions in throughput, which makes sense. Where the sync I/O versions using ImageMagick hovered around 25 req/s, the async I/O versions were able to maintain 35 req/s. It seems there was even some improvement to the response times at least by looking at the 50th percentiles.


### Test setup for async I/O versions
```
# Run the origin server locally
gunicorn origin-server:app -w 8 -b 0.0.0.0:8080 -k uvicorn.workers.UvicornWorker

# Run the optimization service locally
gunicorn imageopt-async-svc:app -w 4 -b 0.0.0.0:8001 -k uvicorn.workers.UvicornWorker
```

With the origin and async I/O version of the service up, I could run the load tests:

```bash
locust -f locustfile-async.py --tag async-imagemagick -u 100 -r 20 -t 5m
```

```bash
locust -f locustfile-async.py --tag async-imagemagick-notemp -u 100 -r 20 -t 5m
```

```bash
locust -f locustfile-async.py --tag async-pyvips-notemp -u 100 -r 20 -t 5m
```

# Conclusions
It seems I have a case where we can gain some significant improvement by focusing on optimizing a CPU-bound task. My recommendation was to make the following changes, in order of impact:

1. Move assets into our own cloud storage (nothing else matters if this isn't done)
2. Replace ImageMagick with libvips
3. Switch the codebase to an Async I/O model

Making such changes would allow the system to achieve a latency.

## Questions
Are there ways to squeeze more performance out of ImageMagick without switching to libvips? Perhaps, but the switch to libvips is pretty low-effort and gives us the boost straight-away.



## Surprises 

### libvips vs ImageMagick for our needs

## Funny things along the way



