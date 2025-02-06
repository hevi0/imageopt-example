from flask import *
import os
from imageopt_sync import ImageOptSync, ImageOptSyncV2, ImageOptSyncV3

app = Flask(__name__)

ORIGIN = os.environ.get('ORIGIN', 'http://localhost:8080')

def set_optimizations(opt: ImageOptSync):
    opt.resize(640, 480)
    opt.png2webp(True)
    opt.quality(80)

@app.route("/sync-imagemagick/<img>")
def get_image_sync_imagemagick(img):
    with ImageOptSync(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt)
        content = opt.get_bytes()
        contenttype = opt.ext()
    return content, 200, {'Content-Type': f'image/{contenttype}'}

@app.route("/sync-imagemagick-notemp/<img>")
def get_image_sync_imagemagick_notemp(img):
    with ImageOptSyncV2(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt)
        content = opt.get_bytes()
        contenttype = opt.ext()
    return content, 200, {'Content-Type': f'image/{contenttype}'}

@app.route("/sync-pyvips-notemp/<img>")
def get_image_sync_pyvips_notemp(img):
    with ImageOptSyncV3(f'{ORIGIN}/{img}') as opt:
        set_optimizations(opt)
        content = opt.get_bytes()
        contenttype = opt.ext()
    return content, 200, {'Content-Type': f'image/{contenttype}'}

if __name__ == '__main__':
    app.run(debug=True)

    # Run 
    # gunicorn -w 4 -b 0.0.0.0:8000 imageopt-sync-svc:app