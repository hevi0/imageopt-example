import asyncio
import os
from fastapi import FastAPI, Response

BUCKET_DIR = os.environ.get('BUCKET_DIR', 'bucket')
SIMULATED_LATENCY = os.environ.get('SIMULATED_LATENCY', 0.050)
image_cache = {}
images = os.listdir(BUCKET_DIR)
for i in images:
    with open(f'{BUCKET_DIR}/{i}', 'rb') as f:
        image_cache[i] = f.read()

app = FastAPI()
@app.get('/{img}')
async def get_image_from_cache(img: str):
    if SIMULATED_LATENCY > 0.0:
        await asyncio.sleep(SIMULATED_LATENCY)
    ext = img.split('.')[-1]
    contenttype = 'jpeg' if ext in ['jpeg', 'jpg'] else ext

    return Response(content=image_cache[img], media_type=f'image/{contenttype}')

#gunicorn origin-server:app -w 8 -b 0.0.0.0:8080 -k uvicorn.workers.UvicornWorker