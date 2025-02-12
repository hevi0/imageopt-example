import os
import random
from locust import HttpUser, between, tag, task

BUCKET_DIR = os.environ.get('BUCKET_DIR', 'bucket')
class UserRequest(HttpUser):
    host = 'http://localhost:8001'
    
    IMAGES = [i for i in os.listdir(BUCKET_DIR) if i.endswith(('.jpg',  '.jpeg', '.png', '.webp'))]

    WIDTHS = [1024]

    wait_time = between(0.2, 2)

    @tag('async-imagemagick')
    @task
    def fetch_image_async_imagemagick(self):
        image = random.choice(UserRequest.IMAGES)
        width = random.choice(UserRequest.WIDTHS)
        self.client.get(f'/async-imagemagick/{image}?width={width}')

    @tag('async-imagemagick-notemp')
    @task
    def fetch_image_async_imagemagick_notemp(self):
        image = random.choice(UserRequest.IMAGES)
        width = random.choice(UserRequest.WIDTHS)
        self.client.get(f'/async-imagemagick-notemp/{image}?width={width}')

    @tag('async-libvips-notemp')
    @task
    def fetch_image_async_libvips_notemp(self):
        image = random.choice(UserRequest.IMAGES)
        width = random.choice(UserRequest.WIDTHS)
        self.client.get(f'/async-libvips-notemp/{image}?width={width}')

    # run each version of the endpoint with 100 users, spawn-rate of 20 for 5 minutes
    # locust -f locustfile-async.py --tag async-imagemagick -u 100 -r 20 -t 5m
    # locust -f locustfile-async.py --tag async-imagemagick-notemp -u 100 -r 20 -t 5m
    # locust -f locustfile-async.py --tag async-libvips-notemp -u 100 -r 20 -t 5m

    # run each version of the endpoint with 10 users, spawn-rate of 2 for 5 minutes
    # locust -f locustfile-async.py --tag async-imagemagick -u 10 -r 2 -t 5m
    # locust -f locustfile-async.py --tag async-imagemagick-notemp -u 10 -r 2 -t 5m
    # locust -f locustfile-async.py --tag async-libvips-notemp -u 10 -r 2 -t 5m