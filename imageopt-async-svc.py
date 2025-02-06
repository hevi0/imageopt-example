from fastapi import FastAPI, Response
import os
from imageopt_async import ImageOptAsync, ImageOptAsyncV2, ImageOptAsyncV3

ORIGIN = os.environ.get('ORIGIN', 'http://localhost:8080')

app = FastAPI()

def set_optimizations(opt: ImageOptAsync):
    opt.resize(640, 480)
    opt.png2webp(True)
    opt.quality(80)

@app.get('/async-imagemagick/{img}')
async def get_image(img: str):
    async with ImageOptAsync(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt)
        content = await opt.get_bytes()
        contenttype = opt.ext()

    return Response(content=content, media_type=f'image/{contenttype}')

@app.get('/async-imagemagick-notemp/{img}')
async def get_image_v2(img: str):
    async with ImageOptAsyncV2(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt)
        content = await opt.get_bytes()
        contenttype = opt.ext()
        
    return Response(content=content, media_type=f'image/{contenttype}')

@app.get('/async-pyvips-notemp/{img}')
async def get_image_v3(img: str):
    async with ImageOptAsyncV3(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt)
        content = await opt.get_bytes()
        contenttype = opt.ext()
        
    return Response(content=content, media_type=f'image/{contenttype}')

# fastapi dev imageopt-async-svc.py

# gunicorn imageopt-async-svc:app -w 4 -b 0.0.0.0:8001 -k uvicorn.workers.UvicornWorker
