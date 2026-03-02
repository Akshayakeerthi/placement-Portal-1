import json

from flask import current_app

from backend.extensions import redis_client


def cache_get(key: str):
    if not redis_client:
        return None
    value = redis_client.get(key)
    return json.loads(value) if value else None


def cache_set(key: str, value, ttl: int | None = None):
    if not redis_client:
        return
    redis_client.setex(key, ttl or current_app.config["CACHE_TTL"], json.dumps(value, default=str))


def cache_delete(prefix: str):
    if not redis_client:
        return
    for key in redis_client.scan_iter(match=f"{prefix}*"):
        redis_client.delete(key)
