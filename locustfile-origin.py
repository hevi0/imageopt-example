import os
import random
from locust import HttpUser, constant, task

BUCKET_DIR = os.environ.get('BUCKET_DIR', 'bucket')
class UserRequest(HttpUser):
    host = 'http://localhost:8080'

    wait_time = constant(0.2) # Each user will make about 5 req/s

    IMAGES = os.listdir(BUCKET_DIR)

    @task
    def fetch_image_origin(self):
        image = random.choice(UserRequest.IMAGES)
        self.client.get(f'/{image}')
    
    # Run with 100 peak users, spawning 20 users at a time, for 5 minutes
    # locust --processes 4 -f locustfile-origin.py -u 100 -r 20 -t 5m