import json

from flask import current_app
from redis.exceptions import RedisError

from backend.extensions import redis_client


def cache_get(key: str):
    if not redis_client:
        return None
    try:
        value = redis_client.get(key)
        if not value:
            return None
        return json.loads(value)
    except RedisError:
        return None


def cache_set(key: str, value, ttl: int | None = None):
    if not redis_client:
        return
    try:
        redis_client.setex(key, ttl or current_app.config["CACHE_TTL"], json.dumps(value, default=str))
    except RedisError:
        return


def cache_delete_pattern(pattern: str):
    if not redis_client:
        return
    try:
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
    except RedisError:
        return
