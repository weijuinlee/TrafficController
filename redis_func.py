import os
import urlparse
import redis
from rq import Queue

redis_conn = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis://default:T0yW5gl8JejxBbc6k2z4EErSpArFpDtO@redis-18286.c233.eu-west-1-1.ec2.cloud.redislabs.com"),
    port=os.getenv("REDIS_PORT", "18286"),
    password=os.getenv("REDIS_PASSWORD", "T0yW5gl8JejxBbc6k2z4EErSpArFpDtO"),
)

redis_queue = Queue(connection=redis_conn)
