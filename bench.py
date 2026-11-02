"""Day 2 实验：三种方式请求 10 次，比耗时（代码已写好，直接跑）

用法（先开另一个终端跑 slow_server.py）：
    uv run python bench.py

它会依次跑：
    1. 同步：一次一个，等完再下一个
    2. 线程池：10 个线程同时发
    3. 异步：asyncio.gather 并发
    4. 反例：async def 里调 time.sleep（阻塞事件循环）—— 看它有多慢
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

URL = "http://127.0.0.1:8100/"
N = 10


def sync_way() -> float:
    start = time.perf_counter()
    with httpx.Client(timeout=10) as client:
        for _ in range(N):
            client.get(URL)
    return time.perf_counter() - start


def thread_way() -> float:
    start = time.perf_counter()
    with httpx.Client(timeout=10) as client, ThreadPoolExecutor(max_workers=N) as pool:
        list(pool.map(lambda _: client.get(URL), range(N)))
    return time.perf_counter() - start


async def async_way() -> float:
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=10) as client:
        await asyncio.gather(*(client.get(URL) for _ in range(N)))
    return time.perf_counter() - start


async def blocking_way() -> float:
    """反例：在协程里用 time.sleep，事件循环被卡住，等于串行。"""

    async def one() -> None:
        time.sleep(0.3)  # ← 错误的写法：这里应该是 await asyncio.sleep(0.3)
        await asyncio.sleep(0)

    start = time.perf_counter()
    await asyncio.gather(*(one() for _ in range(N)))
    return time.perf_counter() - start


def main() -> None:
    results = [
        ("同步（一个接一个）", sync_way()),
        ("线程池（10 线程）", thread_way()),
        ("异步（asyncio.gather）", asyncio.run(async_way())),
        ("异步但用了 time.sleep（反例）", asyncio.run(blocking_way())),
    ]

    print(f"\n{N} 次请求，每次服务端延迟 0.3s\n" + "-" * 46)
    for name, cost in results:
        print(f"{name:<26} {cost:6.2f} 秒")
    print("-" * 46)


if __name__ == "__main__":
    main()
