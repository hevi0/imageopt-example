import logging
import pyvips
import requests
import os
import tempfile
import time
from typing import Any, List, Tuple, TypeVar
import urllib3
import urllib3.util
from wand.image import Image


from common import ImageFormat

ORIGIN = os.environ.get('ORIGIN', 'http://localhost:8080')
DEFAULT_MAX_CONTENT_LENGTH = os.environ.get('DEFAULT_MAX_CONTENT_LENGTH', 10*1024*1024) # 10mb default limit

class ImageOptSync(object):
    """
    Baseline, sync version of image optimization logic.
    It uses ImageMagick underneath.
    """
    def __init__(self, img: str):
        self.orig_img_path = img
        
        filename = img.split('/')[-1]
        format = filename.split('.')[-1]
        format = 'jpeg' if format == 'jpg' else format

        outformat = ImageFormat(format)
        if outformat is None:
            raise ValueError(f"{filename} is not a supported image")

        # Transient state maintained while handling image
        self.state = {
            'filename': filename,
            'tempfile': None,
            'image_checked': False,
            'outformat': outformat,
            'outfile': None
        }

        # Selected image options
        self.imageoptions = {}

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def _fetchimg(self, imgurl) -> Tuple[bytes, Tuple[float, float]] | Tuple[None, Tuple[float, float]]:
        start = time.time()
        r = requests.get(imgurl)
        end = time.time()
        if r.status_code == 200:
            return r.content, (start, end)
        else:
            return None, (start, end)

    def load(self):
        if self.state['image_checked']:
            return
        
        url = urllib3.util.parse_url(self.orig_img_path)
        is_valid_url = url.scheme and url.host and url.path

        if is_valid_url:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                content, elapsed = self._fetchimg(self.orig_img_path)
                self.state['request_time'] = elapsed

                if content is None:
                    raise FileNotFoundError(self.orig_img_path)
                
                if len(content) > DEFAULT_MAX_CONTENT_LENGTH:
                    raise BufferError(f"Content length cannot be more than {DEFAULT_MAX_CONTENT_LENGTH}mb")

                f.write(content)
                self.state['tempfile'] = f.name
        else:
            raise FileNotFoundError(self.orig_img_path)
        
        self.state['image_checked'] = True

    def close(self):
        tempfile = self.state['tempfile']
        if tempfile and os.path.isfile(tempfile):
            os.unlink(tempfile)
            logging.debug(f'deleted temp file: {tempfile}')

        self.state['tempfile'] = None
        self.state['image_checked'] = False
            

    def get_bytes(self) -> bytes | None:
        self.load()
        with open(self.state['tempfile'], 'rb') as f:
            image_binary = f.read()
            start_proc = time.time()
            img = Image(blob=image_binary)
            if 'resize' in self.imageoptions.keys():
                (width, height) = self.imageoptions['resize']
                if height <= 0:
                    val = f'{width}'
                else:
                    val = f'{width}x{height}'
                img.transform(resize=val)

            if 'quality' in self.imageoptions.keys() and img.format in ['jpg', 'jpeg']:
                img.compression_quality = self.imageoptions['quality']

            if 'webp' in self.imageoptions.keys() and self.imageoptions['webp']:
                img.format = 'webp'

            blob = img.make_blob()
            end_proc = time.time()
            self.state['proc_time'] = (start_proc, end_proc)
                
            return blob

    def ext(self):
        return self.state['outformat'].value
        
    def resize(self, width: int, height: int):
        self.imageoptions['resize'] = (width, height)

    def png2webp(self, activate: bool):
        if activate and self.state['outformat'] == ImageFormat.PNG:
            self.imageoptions['webp'] = True
            self.state['outformat'] = ImageFormat.WEBP

    def quality(self, quality: float):
        if self.state['outformat'] == ImageFormat.JPEG:
            self.imageoptions['quality'] = quality

class ImageOptSyncV2(ImageOptSync):
    def __init__(self, img: str):
        super().__init__(img)

    def load(self):
        if self.state['image_checked']:
            return
        
        url = urllib3.util.parse_url(self.orig_img_path)
        is_valid_url = url.scheme and url.host and url.path

        if is_valid_url:
            content, elapsed = self._fetchimg(self.orig_img_path)
            self.state['request_time'] = elapsed

            if content is None:
                raise FileNotFoundError(self.orig_img_path)
            
            if len(content) > DEFAULT_MAX_CONTENT_LENGTH:
                raise BufferError(f"Content length cannot be more than {DEFAULT_MAX_CONTENT_LENGTH}mb")

            self.state['tempfile'] = content
        else:
            raise FileNotFoundError(self.orig_img_path)
        
        self.state['image_checked'] = True

    def close(self):
        # No tempfile to delete anymore

        self.state['tempfile'] = None
        self.state['image_checked'] = False

    def get_bytes(self) -> bytes | None:
        self.load()

        image_binary = self.state['tempfile']
        start_proc = time.time()
        img = Image(blob=image_binary)

        if 'resize' in self.imageoptions.keys():
            (width, height) = self.imageoptions['resize']
            if height <= 0:
                val = f'{width}'
            else:
                val = f'{width}x{height}'
            img.transform(resize=val)

        if 'quality' in self.imageoptions.keys() and img.format in ['jpg', 'jpeg']:
            img.compression_quality = self.imageoptions['quality']

        if 'webp' in self.imageoptions.keys() and self.imageoptions['webp']:
            img.format = 'webp'
        
        blob = img.make_blob()
        end_proc = time.time()
        self.state['proc_time'] = (start_proc, end_proc)
        return blob

class ImageOptSyncV3(ImageOptSyncV2):
    def __init__(self, img: str):
        super().__init__(img)

    def load(self):
        if self.state['image_checked']:
            return
        
        url = urllib3.util.parse_url(self.orig_img_path)
        is_valid_url = url.scheme and url.host and url.path

        if is_valid_url:
            content, elapsed = self._fetchimg(self.orig_img_path)
            self.state['request_time'] = elapsed

            if content is None:
                raise FileNotFoundError(self.orig_img_path)
            
            if len(content) > DEFAULT_MAX_CONTENT_LENGTH:
                raise BufferError(f"Content length cannot be more than {DEFAULT_MAX_CONTENT_LENGTH}mb")

            self.state['tempfile'] = content
        else:
            raise FileNotFoundError(self.orig_img_path)
        
        self.state['image_checked'] = True

    def get_bytes(self) -> bytes | None:
        self.load()

        start_proc = time.time()
        outformat = ImageFormat(self.state['outformat'])

        if 'resize' in self.imageoptions.keys():
            (width, height) = self.imageoptions['resize']
            if height <= 0:
                img = pyvips.Image.thumbnail_buffer(self.state['tempfile'], width)
            else:
                img = pyvips.Image.thumbnail_buffer(self.state['tempfile'], width, height=height)
        else:
            img = pyvips.Image.new_from_buffer(self.state['tempfile'])

        if 'webp' in self.imageoptions.keys() and self.imageoptions['webp']:
            outformat = ImageFormat.WEBP
        
        if outformat == ImageFormat.PNG:
            buffer = img.pngsave_buffer()
        elif outformat == ImageFormat.WEBP:
            buffer = img.webpsave_buffer()
        elif outformat == ImageFormat.JPEG:
            if 'quality' in self.imageoptions.keys() and outformat == ImageFormat.JPEG:
                buffer = img.jpegsave_buffer(Q=self.imageoptions['quality'])
            else:
                buffer = img.jpegsave_buffer()

        end_proc = time.time()
        self.state['proc_time'] = (start_proc, end_proc)
        return buffer