"""Day 2 练习：异步 HTTP 三件套（你要实现的）

前置：先看 notes/day02.md 的实验数字——同步 3.37s / 异步 0.57s。

三个函数都会用 httpx.AsyncClient，它是 httpx 的异步版本：
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)

为什么必须用 AsyncClient？用同步的 httpx.Client 在协程里调用，会像 time.sleep 一样
卡住事件循环（昨天实验的 3.00s 那行）。
"""

import asyncio

import httpx

# r = httpx.get("https://www.example.org/")
# print(r)

# ---------------------------------------------------------------- 练习 1


async def fetch_all(urls: list[str]) -> list[str]:
    """并发请求所有 URL，按**输入顺序**返回每个响应的文本。

    要求：
    - 用一个 AsyncClient 处理全部请求（复用连接池）；
    - 用 asyncio.gather 并发；
    - 返回顺序必须和 urls 一致（gather 保证这一点）。

    提示：
        async with httpx.AsyncClient(timeout=5) as client:
            responses = await asyncio.gather(*(client.get(u) for u in urls))
        return [r.text for r in responses]

    注意 `*(... for ...)`：把生成器解包成多个参数传给 gather。
    """
    async with httpx.AsyncClient(timeout=5) as client:
        responses = await asyncio.gather(*(client.get(u) for u in urls))
    return [r.text for r in responses]


# ---------------------------------------------------------------- 练习 2


async def fetch_limited(urls: list[str], limit: int) -> list[str]:
    """和 fetch_all 一样，但同时最多只有 limit 个请求在飞。

    为什么要限流：真实目标网站扛不住几百个并发，你也可能被封 IP。

    要求：
    - 用 asyncio.Semaphore(limit) 控制并发；
    - 仍然返回与 urls 同序的结果。

    提示：
        sem = asyncio.Semaphore(limit)

        async def one(url: str) -> str:
            async with sem:                     # 拿到"许可"才发请求
                resp = await client.get(url)
                return resp.text

        return await asyncio.gather(*(one(u) for u in urls))
    """
    sem = asyncio.Semaphore(limit)
    async with httpx.AsyncClient(timeout=5) as client:

        async def one(url: str):
            async with sem:
                resp = await client.get(url)
                return resp.text

        return await asyncio.gather(*(one(u) for u in urls))


# ---------------------------------------------------------------- 练习 3


async def fetch_with_retry(url: str, times: int = 3) -> str:
    """请求一个 URL，失败就重试，最多 times 次；全失败则抛出最后一次的异常。

    要求：
    - 响应状态码 >= 400 也算失败（用 response.raise_for_status()）；
    - 每次重试前 await asyncio.sleep(0.01)（别把对方打挂）；
    - 全部失败时 raise 最后一个异常。

    提示：这和 Day 8 的 retry 装饰器思路一样，只是把"循环 + try"写在函数里：

        last_error = None
        for _ in range(times):
            try:
                ...
                return ...
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(0.01)
        raise last_error
    """
    last_error = None
    async with httpx.AsyncClient(timeout=5) as client:
        for _ in range(times):
            try:
                resp = await client.get(url)
                resp.raise_for_status()    # 连接失败会自己抛出错误，不用在raise
                return resp.text
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(0.01)

    raise last_error
