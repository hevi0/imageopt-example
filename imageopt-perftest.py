import asyncio
import aiofiles
import aiofiles.os
import aiofiles.ospath
import logging
import math
import os
import tracemalloc
from typing import Any, Callable, List, TypeVar

from imageopt_sync import *
from imageopt_async import *

BUCKET_DIR = os.environ.get('BUCKET_DIR', 'bucket')
ORIGIN = os.environ.get('ORIGIN', 'http://localhost:8080')
DEFAULT_MAX_CONTENT_LENGTH = os.environ.get('DEFAULT_MAX_CONTENT_LENGTH', 10*1024*1024) # 10mb default limit

T = TypeVar("T")

def flatten(thelist: List[List[T]]) -> List[T]:
    accum = []
    for nestedlist in thelist:
        accum.extend(nestedlist)

    return accum

def set_optimizations(opt: ImageOptSync | ImageOptAsync):
    opt.resize(640, 480)
    opt.png2webp(True)
    opt.quality(80)

async def perftest(images: List[str], fn: Callable[[List],List[float]], title: str):
    tracemalloc.start()
    tracemalloc.clear_traces()
    
    run_start = asyncio.get_running_loop().time()
    fetch_times = await fn(images)
    run_end = asyncio.get_running_loop().time()

    memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    fetch_times_agg = sum([(end - start) for (start, end) in fetch_times])

    report(
        title,
        len(fetch_times),
        run_end - run_start,
        fetch_times_agg,
        memory[1]
    )

def report(title, num_images, runtime, fetch_times_agg, peak_mem):
    print(f'--- {title} ---')
    print(f'Number of image requests: {num_images}')
    print(f'Runtime: {runtime}')
    print(f'Est. time spent fetching images: {fetch_times_agg}')
    print(f'Peak memory use: {peak_mem}\n')

async def perftest1(images):
    outputdir = 'output'
    def task(image):
        with ImageOptSync(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            with open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                f.write(opt.get_bytes())

            return opt.state['request_time']

    fetch_times = []
    for i in range(len(images)):
        fetch_times.append(task(images[i]))

    return fetch_times

async def perftest2(images):
    outputdir = 'output'
    def task(image):
        with ImageOptSyncV2(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            with open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                f.write(opt.get_bytes())

            return opt.state['request_time']
        
    fetch_times = []
    for i in range(len(images)):
        fetch_times.append(task(images[i]))

    return fetch_times

async def perftest3(images):
    outputdir = 'output'
    def task(image):
        with ImageOptSyncV3(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            with open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                f.write(opt.get_bytes())

            return opt.state['request_time']
        
    fetch_times = []
    for i in range(len(images)):
        fetch_times.append(task(images[i]))

    return fetch_times

async def perftest4(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsync(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state['request_time']

    coros = [ task(i) for i in images ]
    fetch_times = await asyncio.gather(*coros)

    return fetch_times

async def perftest5(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsyncV2(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state['request_time']

    coros = [ task(i) for i in images ]
    fetch_times = await asyncio.gather(*coros)

    return fetch_times

async def perftest6(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsyncV3(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state['request_time']

    coros = [ task(i) for i in images ]
    fetch_times = await asyncio.gather(*coros)

    return fetch_times


n = 100
# Don't let chunksize exceed the number of workers/cores on the origin server
# as it makes the calculation of the time spent fetching the images
# include excessive blocking
chunksize = 4
async def perftest7(images):
    outputdir = 'output'
    def task(image):
        with ImageOptSync(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            with open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                f.write(opt.get_bytes())

            return opt.state['request_time']

    fetch_times = []
    for i in range(n):
        fetch_times.append(task(images[i % len(images)]))

    return fetch_times

async def perftest8(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsyncV3(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state['request_time']

    fetch_times = []

    for iter in range(0, n, chunksize):
        coros = [ task(images[i%len(images)]) for i in range(chunksize) if iter + i < n]
        fetch_times.append(await asyncio.gather(*coros))

    return flatten(fetch_times)

async def main_test_basic():
    images = os.listdir(BUCKET_DIR)

    await perftest(images, perftest1, 'SyncIO ImageMagick (wand) with temp file')
    await perftest(images, perftest1, 'SyncIO ImageMagick (wand) In-memory')
    await perftest(images, perftest3, 'SyncIO libvips (pyvips) In-memory')
    await perftest(images, perftest4, 'AsyncIO ImageMagick (wand) with temp file')
    await perftest(images, perftest5, 'AsyncIO ImageMagick (wand) In-memory')
    await perftest(images, perftest6, 'AsyncIO libvips (pyvips) In-memory')

async def main_test_bulk():
    images = os.listdir(BUCKET_DIR)

    await perftest(images, perftest7, 'Bulk SyncIO ImageMagick (wand) with temp file')
    await perftest(images, perftest8, 'Bulk AsyncIO libvips (pyvips) In-memory')

if __name__ == '__main__':
    if not os.path.exists('output'):
        os.mkdir('output')
    
    logging.basicConfig(level=logging.WARNING)

    asyncio.run(main_test_basic())
    asyncio.run(main_test_bulk())
