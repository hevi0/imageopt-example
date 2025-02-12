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
    (fetch_times, proc_times) = await fn(images)
    run_end = asyncio.get_running_loop().time()

    memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    fetch_times_agg = sum([(end - start) for (start, end) in fetch_times])
    proc_times_agg = sum([(end - start) for (start, end) in proc_times])

    report(
        title,
        len(fetch_times),
        run_end - run_start,
        fetch_times_agg,
        proc_times_agg,
        memory[1]
    )

def report(title, num_images, runtime, fetch_times_agg, proc_times_agg, peak_mem):
    print(f'--- {title} ---')
    print(f'Number of image requests: {num_images}')
    print(f'Runtime: {runtime}')
    print(f'Est. time spent fetching images: {fetch_times_agg}')
    print(f'Est. time spent optimizing images: {proc_times_agg}')
    print(f'Peak memory use: {peak_mem}\n')

async def perftest1(images):
    outputdir = 'output'
    def task(image):
        with ImageOptSync(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            with open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                f.write(opt.get_bytes())

            return opt.state

    fetch_times = []
    proc_times = []
    for i in range(len(images)):
        state = task(images[i])
        proc_times.append(state['proc_time'])
        fetch_times.append(state['request_time'])

    return fetch_times, proc_times

async def perftest2(images):
    outputdir = 'output'
    def task(image):
        with ImageOptSyncV2(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            with open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                f.write(opt.get_bytes())

            return opt.state
        
    proc_times = []
    fetch_times = []
    for i in range(len(images)):
        state = task(images[i])
        proc_times.append(state['proc_time'])
        fetch_times.append(state['request_time'])

    return fetch_times, proc_times

async def perftest3(images):
    outputdir = 'output'
    def task(image):
        with ImageOptSyncV3(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            with open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                f.write(opt.get_bytes())

            return opt.state
        
    proc_times = []
    fetch_times = []
    for i in range(len(images)):
        state = task(images[i])
        proc_times.append(state['proc_time'])
        fetch_times.append(state['request_time'])

    return fetch_times, proc_times

async def perftest4(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsync(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state

    coros = [ task(i) for i in images ]
    states = await asyncio.gather(*coros)
    fetch_times = [s['request_time'] for s in states]
    proc_times = [s['proc_time'] for s in states]

    return fetch_times, proc_times

async def perftest5(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsyncV2(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state

    coros = [ task(i) for i in images ]
    states = await asyncio.gather(*coros)
    fetch_times = [s['request_time'] for s in states]
    proc_times = [s['proc_time'] for s in states]

    return fetch_times, proc_times

async def perftest6(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsyncV3(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state

    coros = [ task(i) for i in images ]
    states = await asyncio.gather(*coros)
    fetch_times = [s['request_time'] for s in states]
    proc_times = [s['proc_time'] for s in states]

    return fetch_times, proc_times

async def perftest7(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsyncV4(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state

    coros = [ task(i) for i in images ]
    states = await asyncio.gather(*coros)
    fetch_times = [s['request_time'] for s in states]
    proc_times = [s['proc_time'] for s in states]

    return fetch_times, proc_times


n = 100
# Don't let chunksize exceed the number of workers/cores on the origin server
# as it makes the calculation of the time spent fetching the images
# include excessive blocking
chunksize = 4
async def perftest8(images):
    outputdir = 'output'
    def task(image):
        with ImageOptSync(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            with open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                f.write(opt.get_bytes())

            return opt.state

    fetch_times = []
    proc_times = []
    for i in range(n):
        state = task(images[i % len(images)])
        fetch_times.append(state['request_time'])
        proc_times.append(state['proc_time'])

    return fetch_times, proc_times

async def perftest9(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsync(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state

    fetch_times = []
    proc_times = []

    for iter in range(0, n, chunksize):
        coros = [ task(images[i%len(images)]) for i in range(chunksize) if iter + i < n]
        states = (await asyncio.gather(*coros))
        fetch_times.append([s['request_time'] for s in states])
        proc_times.append([s['proc_time'] for s in states])

    return flatten(fetch_times), flatten(proc_times)

async def perftest10(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsyncV3(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state

    fetch_times = []
    proc_times = []

    for iter in range(0, n, chunksize):
        coros = [ task(images[i%len(images)]) for i in range(chunksize) if iter + i < n]
        states = (await asyncio.gather(*coros))
        fetch_times.append([s['request_time'] for s in states])
        proc_times.append([s['proc_time'] for s in states])

    return flatten(fetch_times), flatten(proc_times)

async def perftest11(images):
    outputdir = 'output'
    async def task(image):
        async with ImageOptAsyncV4(f'{ORIGIN}/{image}') as opt:
            set_optimizations(opt)
            
            async with aiofiles.open(f'{outputdir}/{image}.{opt.ext()}', 'wb') as f:
                await f.write(await opt.get_bytes())

        return opt.state

    fetch_times = []
    proc_times = []

    for iter in range(0, n, chunksize):
        coros = [ task(images[i%len(images)]) for i in range(chunksize) if iter + i < n]
        states = (await asyncio.gather(*coros))
        fetch_times.append([s['request_time'] for s in states])
        proc_times.append([s['proc_time'] for s in states])

    return flatten(fetch_times), flatten(proc_times)

async def main_test_basic():
    images = [i for i in os.listdir(BUCKET_DIR) if i.endswith(('.jpeg', '.jpg', '.png', '.webp'))]

    await perftest(images, perftest1, 'SyncIO ImageMagick (wand) with temp file')
    await perftest(images, perftest1, 'SyncIO ImageMagick (wand) In-memory')
    await perftest(images, perftest3, 'SyncIO libvips (pyvips) In-memory')
    await perftest(images, perftest4, 'AsyncIO ImageMagick (wand) with temp file')
    await perftest(images, perftest5, 'AsyncIO ImageMagick (wand) In-memory')
    await perftest(images, perftest6, 'AsyncIO libvips (pyvips) In-memory')
    await perftest(images, perftest6, 'AsyncIO libvips (pyvips) with temp file')

async def main_test_bulk():
    images = [i for i in os.listdir(BUCKET_DIR) if i.endswith(('.jpeg', '.jpg', '.png', '.webp'))]

    await perftest(images, perftest8, 'Bulk SyncIO ImageMagick (wand) with temp file')
    await perftest(images, perftest9, 'Bulk AsyncIO ImageMagick (wand) In-memory')
    await perftest(images, perftest10, 'Bulk AsyncIO libvips (pyvips) In-memory')
    await perftest(images, perftest11, 'Bulk AsyncIO libvips (pyvips) with temp file')

if __name__ == '__main__':
    if not os.path.exists('output'):
        os.mkdir('output')
    
    logging.basicConfig(level=logging.WARNING)

    asyncio.run(main_test_basic())
    asyncio.run(main_test_bulk())
