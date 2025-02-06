import os
import random
from locust import HttpUser, between, tag, task

BUCKET_DIR = os.environ.get('BUCKET_DIR', 'bucket')
class UserRequest(HttpUser):
    host = 'http://localhost:8001'
    
    IMAGES = os.listdir(BUCKET_DIR)

    wait_time = between(0.2, 2)

    @tag('async-imagemagick')
    @task
    def fetch_image_async_imagemagick(self):
        image = random.choice(UserRequest.IMAGES)
        self.client.get(f'/async-imagemagick/{image}')

    @tag('async-imagemagick-notemp')
    @task
    def fetch_image_async_imagemagick_notemp(self):
        image = random.choice(UserRequest.IMAGES)
        self.client.get(f'/async-imagemagick-notemp/{image}')

    @tag('async-pyvips-notemp')
    @task
    def fetch_image_async_pyvips_notemp(self):
        image = random.choice(UserRequest.IMAGES)
        self.client.get(f'/async-pyvips-notemp/{image}')

    # run each version of the endpoint with 100 users, spawn-rate of 20 for 5 minutes
    # locust -f locustfile-async.py --tag async-imagemagick -u 100 -r 20 -t 5m
    # locust -f locustfile-async.py --tag async-imagemagick-notemp -u 100 -r 20 -t 5m
    # locust -f locustfile-async.py --tag async-pyvips-notemp -u 100 -r 20 -t 5m

    # run each version of the endpoint with 10 users, spawn-rate of 2 for 5 minutes
    # locust -f locustfile-async.py --tag async-imagemagick -u 10 -r 2 -t 5m
    # locust -f locustfile-async.py --tag async-imagemagick-notemp -u 10 -r 2 -t 5m
    # locust -f locustfile-async.py --tag async-pyvips-notemp -u 10 -r 2 -t 5m