import os
import random
from locust import HttpUser, between, tag, task

BUCKET_DIR = os.environ.get('BUCKET_DIR', 'bucket')
class UserRequest(HttpUser):
    host = 'http://localhost:8000'

    IMAGES = os.listdir(BUCKET_DIR)

    wait_time = between(0.2, 2)

    @tag('sync-imagemagick')
    @task
    def fetch_image_sync_imagemagick(self):
        image = random.choice(UserRequest.IMAGES)
        self.client.get(f'/sync-imagemagick/{image}')
    
    @tag('sync-imagemagick-notemp')
    @task
    def fetch_image_sync_imagemagick_notemp(self):
        image = random.choice(UserRequest.IMAGES)
        self.client.get(f'/sync-imagemagick-notemp/{image}')

    @tag('sync-pyvips-notemp')
    @task
    def fetch_image_sync_pyvips_notemp(self):
        image = random.choice(UserRequest.IMAGES)
        self.client.get(f'/sync-pyvips-notemp/{image}')

    # run each version of the endpoint with 100 users, spawn-rate of 20 for 5 minutes
    # locust -f locustfile-sync.py --tag sync-imagemagick -u 100 -r 20 -t 5m
    # locust -f locustfile-sync.py --tag sync-imagemagick-notemp -u 100 -r 20 -t 5m
    # locust -f locustfile-sync.py --tag sync-pyvips-notemp -u 100 -r 20 -t 5m

    # run each version of the endpoint with 10 users, spawn-rate of 2 for 5 minutes
    # locust -f locustfile-sync.py --tag sync-imagemagick -u 10 -r 2 -t 5m
    # locust -f locustfile-sync.py --tag sync-imagemagick-notemp -u 10 -r 2 -t 5m
    # locust -f locustfile-sync.py --tag sync-pyvips-notemp -u 10 -r 2 -t 5m