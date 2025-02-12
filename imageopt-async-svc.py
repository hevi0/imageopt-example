from fastapi import FastAPI, Response, Request
import os
from imageopt_async import ImageOptAsync, ImageOptAsyncV2, ImageOptAsyncV3, ImageOptAsyncV4

ORIGIN = os.environ.get('ORIGIN', 'http://localhost:8080')

app = FastAPI()

def set_optimizations(opt: ImageOptAsync, req: Request):
    try:
        width = int(req.query_params['width'])
        if width > 0:
            opt.resize(width, 0)
    except:
        pass
    opt.png2webp(True)
    opt.quality(80)

@app.get('/async-imagemagick/{img}')
async def get_image(img: str, req: Request):
    async with ImageOptAsync(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt, req)
        content = await opt.get_bytes()
        contenttype = opt.ext()

    return Response(content=content, media_type=f'image/{contenttype}')

@app.get('/async-imagemagick-notemp/{img}')
async def get_image_v2(img: str, req: Request):
    async with ImageOptAsyncV2(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt, req)
        content = await opt.get_bytes()
        contenttype = opt.ext()
        
    return Response(content=content, media_type=f'image/{contenttype}')

@app.get('/async-libvips-notemp/{img}')
async def get_image_v3(img: str, req: Request):
    async with ImageOptAsyncV3(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt, req)
        content = await opt.get_bytes()
        contenttype = opt.ext()

@app.get('/async-libvips/{img}')
async def get_image_v4(img: str, req: Request):
    async with ImageOptAsyncV4(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt, req)
        content = await opt.get_bytes()
        contenttype = opt.ext()
        
    return Response(content=content, media_type=f'image/{contenttype}')

# fastapi dev imageopt-async-svc.py

# gunicorn imageopt-async-svc:app -w 4 -b 0.0.0.0:8001 -k uvicorn.workers.UvicornWorker
