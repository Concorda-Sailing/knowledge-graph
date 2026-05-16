"""Decorator factories: parameterized, stacked, functools.wraps inside."""
from __future__ import annotations

import functools


def require_role(role: str):
    """Parameterized decorator factory — returns a decorator."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_call(func):
    """Simple decorator (not a factory) using functools.wraps."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def retry(times: int = 3):
    """Another parameterized factory."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    pass
        return wrapper
    return decorator


@require_role("admin")
def delete_record(record_id: int) -> bool:
    """Decorated with a single factory call."""
    return True


@require_role("user")
@log_call
@retry(times=5)
def fetch_data(url: str) -> dict:
    """Stacked: factory + plain + factory(arg). Three decorator entries."""
    return {}


class Service:
    @require_role("admin")
    def admin_action(self) -> None:
        pass

    @log_call
    @retry()
    def retried_action(self) -> None:
        pass
