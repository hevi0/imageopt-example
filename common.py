
from enum import Enum
import os

BUCKET_DIR = os.environ.get('BUCKET_DIR', 'bucket')
ORIGIN = os.environ.get('ORIGIN', 'http://localhost:8080')
DEFAULT_MAX_CONTENT_LENGTH = os.environ.get('DEFAULT_MAX_CONTENT_LENGTH', 10*1024*1024) # 10mb default limit
SIMULATED_LATENCY = os.environ.get('SIMULATED_LATENCY', 0.050)  # IN milliseconds (0.050 for 50 ms, 0.020 ms for 20 ms...)

class ImageFormat(str, Enum):
    PNG = 'png',
    JPEG = 'jpeg',
    WEBP = 'webp'

