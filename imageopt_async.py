import asyncio
import aiofiles
import aiofiles.os
import aiofiles.ospath
import aiohttp
import logging
import os
import pyvips
import time
from typing import Tuple
import urllib3
import urllib3.util
from wand.image import Image

from common import ImageFormat

ORIGIN = os.environ.get('ORIGIN', 'http://localhost:8080')
DEFAULT_MAX_CONTENT_LENGTH = os.environ.get('DEFAULT_MAX_CONTENT_LENGTH', 10*1024*1024) # 10mb default limit

class ImageOptAsync(object):

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

    async def __aenter__(self):
        await self.load()
        return self

    async def __aexit__(self, type, value, traceback):
        await self.close()

    async def _fetchimg(self, imgurl)  -> Tuple[bytes, Tuple[float, float]] | Tuple[None, Tuple[float, float]]:
        async with aiohttp.ClientSession() as session:
            start = asyncio.get_running_loop().time()
            async with session.get(imgurl) as r:
                end = asyncio.get_running_loop().time()
                if r.status == 200:
                    contents = await r.read()

                    return contents, (start, end)
                else:
                    return None, (start, end)
                
    async def load(self):
        if self.state['image_checked']:
            return
        
        url = urllib3.util.parse_url(self.orig_img_path)
        is_valid_url = url.scheme and url.host and url.path

        if is_valid_url:
            async with aiofiles.tempfile.NamedTemporaryFile(delete=False) as f:
                content, elapsed = await self._fetchimg(self.orig_img_path)
                self.state['request_time'] = elapsed

                if content is None:
                    raise FileNotFoundError(self.orig_img_path)
                
                if len(content) > DEFAULT_MAX_CONTENT_LENGTH:
                    raise BufferError(f"Content length cannot be more than {DEFAULT_MAX_CONTENT_LENGTH}mb")
                await f.write(content)
                
                self.state['tempfile'] = f.name
        else:
            raise FileNotFoundError(self.orig_img_path)
        
        self.state['image_checked'] = True

    async def close(self):
        tempfile = self.state['tempfile']
        if tempfile and await aiofiles.os.path.isfile(tempfile):
            await aiofiles.os.unlink(tempfile)
            logging.debug(f'deleted temp file: {tempfile}')

        self.state['tempfile'] = None
        self.state['image_checked'] = False
            

    async def get_bytes(self):
        await self.load()
        async with aiofiles.open(self.state['tempfile'], 'rb') as f:
            image_binary = await f.read()

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

class ImageOptAsyncV2(ImageOptAsync):
    def __init__(self, img: str):
        super().__init__(img)

    async def load(self):
        if self.state['image_checked']:
            return
        
        url = urllib3.util.parse_url(self.orig_img_path)
        is_valid_url = url.scheme and url.host and url.path

        if is_valid_url:
            # Replace use of temp file with keeping contents in memory
            content, elapsed = await self._fetchimg(self.orig_img_path)
            self.state['request_time'] = elapsed
            if content is None:
                raise FileNotFoundError(self.orig_img_path)
                
            if len(content) > DEFAULT_MAX_CONTENT_LENGTH:
                raise BufferError(f"Content length cannot be more than {DEFAULT_MAX_CONTENT_LENGTH}mb")
            
            self.state['tempfile'] = content
        else:
            raise FileNotFoundError(self.orig_img_path)
        
        self.state['image_checked'] = True

    async def close(self):
        """
        No more temp files to delete
        """

        self.state['tempfile'] = None
        self.state['image_checked'] = False

    async def get_bytes(self):
        await self.load()

        start_proc = time.time()
        img = Image(blob=self.state['tempfile'])

        if 'resize' in self.imageoptions.keys():
            (width, height) = self.imageoptions['resize']
            if height <= 0:
                val = f'{width}'
            else:
                val = f'{width}x{height}'
            img.transform(resize=val)

        if 'quality' in self.imageoptions.keys() and img.format == 'jpg':
            img.compression_quality = self.imageoptions['webp']

        if 'webp' in self.imageoptions.keys() and self.imageoptions['webp']:
            img.format = 'webp'
        
        blob = img.make_blob()
        end_proc = time.time()
        self.state['proc_time'] = (start_proc, end_proc)
        return blob
    
class ImageOptAsyncV3(ImageOptAsyncV2):
    def __init__(self, img: str):
        super().__init__(img)

    async def get_bytes(self):
        await self.load()

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
    
class ImageOptAsyncV4(ImageOptAsync):
    async def get_bytes(self):
        await self.load()

        start_proc = time.time()
        outformat = ImageFormat(self.state['outformat'])

        if 'resize' in self.imageoptions.keys():
            (width, height) = self.imageoptions['resize']
            if height <= 0:
                img = pyvips.Image.thumbnail(self.state['tempfile'], width)
            else:
                img = pyvips.Image.thumbnail(self.state['tempfile'], width, height=height)
        else:
            img = pyvips.Image.new_from_file(self.state['tempfile'])

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