from rq import Worker, Queue, Connection
from redis import Redis
import os

# Redis connection
redis_conn = Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=0
)

if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker(['video_generation', 'digital_self', 'default'])
        worker.work()