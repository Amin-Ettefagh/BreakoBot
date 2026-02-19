import asyncio
import random
from typing import Awaitable, Callable, Tuple, Type


async def retry_async(
    func: Callable[[], Awaitable],
    *,
    retries: int,
    base_delay: float,
    max_delay: float,
    retry_exceptions: Tuple[Type[BaseException], ...],
) -> object:
    """Retry an async callable with exponential backoff and jitter."""
    last_exc: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            return await func()
        except retry_exceptions as exc:
            last_exc = exc
            if attempt >= retries:
                break
            delay = min(max_delay, base_delay * (2 ** attempt))
            delay = delay * (0.5 + random.random())
            await asyncio.sleep(delay)
    if last_exc is None:
        raise RuntimeError("retry_async failed without exception")
    raise last_exc
