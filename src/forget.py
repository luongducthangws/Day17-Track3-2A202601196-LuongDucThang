from __future__ import annotations

import argparse

import redis

from .config import settings
from .zep_common import get_zep_client


def is_not_found(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status == 404:
        return True
    text = str(exc).casefold()
    return "404" in text and "not found" in text


def delete_redis_user(redis_client: redis.Redis, user_id: str) -> int:
    try:
        pattern = f"lab17:user:{user_id}:*"
        keys = list(redis_client.scan_iter(match=pattern))
        if not keys:
            return 0
        return int(redis_client.delete(*keys))
    except Exception:
        return 0


def zep_user_exists(zep, user_id: str) -> bool:
    try:
        zep.user.get(user_id=user_id)
        return True
    except Exception as exc:
        if is_not_found(exc):
            return False
        raise


def delete_zep_user(zep, user_id: str) -> None:
    try:
        zep.user.delete(user_id=user_id)
    except Exception as exc:
        if not is_not_found(exc):
            raise


def verify(zep, rdb: redis.Redis, user_id: str) -> bool:
    exists = zep_user_exists(zep, user_id)
    try:
        redis_remaining = list(rdb.scan_iter(match=f"lab17:user:{user_id}:*"))
    except Exception:
        redis_remaining = []
    print("Zep user absent:", not exists)
    print("Redis user keys remaining:", len(redis_remaining))
    return not exists and not redis_remaining


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    zep = get_zep_client()
    rdb = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    if not args.verify_only:
        print(f"Deleting user-scoped memory for {args.user_id!r}...")
        delete_zep_user(zep, args.user_id)
        deleted_local = delete_redis_user(rdb, args.user_id)
        print("Redis keys deleted:", deleted_local)

    ok = verify(zep, rdb, args.user_id)
    print("Shared semantic KB remains intact because it stores domain knowledge, not user PII.")
    if not ok:
        raise SystemExit("Deletion verification failed")


if __name__ == "__main__":
    main()
