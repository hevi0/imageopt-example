import os
import random
from locust import HttpUser, between, tag, task

BUCKET_DIR = os.environ.get('BUCKET_DIR', 'bucket')
class UserRequest(HttpUser):
    host = 'http://localhost:8000'

    wait_time = between(0.2, 2)

    WIDTHS = [1024]

    IMAGES = [i for i in os.listdir(BUCKET_DIR) if i.endswith(('.jpg',  '.jpeg', '.png', '.webp'))]

    @tag('sync-imagemagick')
    @task
    def fetch_image_sync_imagemagick(self):
        image = random.choice(UserRequest.IMAGES)
        width = random.choice(UserRequest.WIDTHS)
        self.client.get(f'/sync-imagemagick/{image}?width={width}')
    
    @tag('sync-imagemagick-notemp')
    @task
    def fetch_image_sync_imagemagick_notemp(self):
        image = random.choice(UserRequest.IMAGES)
        width = random.choice(UserRequest.WIDTHS)
        self.client.get(f'/sync-imagemagick-notemp/{image}?width={width}')

    @tag('sync-libvips-notemp')
    @task
    def fetch_image_sync_libvips_notemp(self):
        image = random.choice(UserRequest.IMAGES)
        width = random.choice(UserRequest.WIDTHS)
        self.client.get(f'/sync-libvips-notemp/{image}?width={width}')

    # run each version of the endpoint with 100 users, spawn-rate of 20 for 5 minutes
    # locust -f locustfile-sync.py --tag sync-imagemagick -u 100 -r 20 -t 5m
    # locust -f locustfile-sync.py --tag sync-imagemagick-notemp -u 100 -r 20 -t 5m
    # locust -f locustfile-sync.py --tag sync-pyvips-notemp -u 100 -r 20 -t 5m

    # run each version of the endpoint with 10 users, spawn-rate of 2 for 5 minutes
    # locust -f locustfile-sync.py --tag sync-imagemagick -u 10 -r 2 -t 5m
    # locust -f locustfile-sync.py --tag sync-imagemagick-notemp -u 10 -r 2 -t 5m
    # locust -f locustfile-sync.py --tag sync-pyvips-notemp -u 10 -r 2 -t 5m