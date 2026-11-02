"""Day 3 练习：并发爬取器（你要实现的）

和 Day 2 的三个函数相比，这里多了三件事：
1. **结果建模**——成功和失败都存进 FetchResult，而不是抛异常
2. **容错**——一个 URL 挂了，不影响其他 URL
3. **汇总**——最后给出"成功几个、失败几个、失败原因"

真实爬虫/批量任务基本都是这个结构。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx


@dataclass(frozen=True, slots=True)
class FetchResult:
    """一次抓取的结果（成功或失败都放在这里）。"""

    url: str
    ok: bool
    status: int | None = None
    text: str | None = None
    error: str | None = None


async def crawl(
    urls: list[str],
    *,
    limit: int = 5,
    retries: int = 2,
    timeout: float = 5.0,
) -> list[FetchResult]:
    """并发抓取所有 URL，返回结果列表（顺序与 urls 一致）。

    要求：
    - 同时最多 limit 个请求在飞（Semaphore）；
    - 每个 URL 最多尝试 retries + 1 次（含首次），失败后 `await asyncio.sleep(0.01)` 再试；
    - **任何异常都不要往外抛**，转成 FetchResult(ok=False, error=str(exc))；
    - 成功时填 status 和 text；
    - 返回列表的顺序必须和 urls 一致。

    提示：
        sem = asyncio.Semaphore(limit)

        async with httpx.AsyncClient(timeout=timeout) as client:

            async def one(url: str) -> FetchResult:
                last = "未知错误"
                for _ in range(retries + 1):
                    async with sem:
                        try:
                            resp = await client.get(url)
                            resp.raise_for_status()
                            return FetchResult(url=url, ok=True, status=resp.status_code, text=resp.text)
                        except Exception as exc:
                            last = str(exc)
                    await asyncio.sleep(0.01)
                return FetchResult(url=url, ok=False, error=last)

            return list(await asyncio.gather(*(one(u) for u in urls)))

    注意：受 asyncio.gather 保护，one() 里不要让异常冒出去，否则整个 gather 会失败。
    """
    raise NotImplementedError("TODO: 实现 crawl")


def summarize(results: list[FetchResult]) -> dict:
    """汇总抓取结果。

    返回：
        {
            "total": 3,
            "ok": 2,
            "failed": 1,
            "failures": [("http://x/500", "Server error '500 Internal Server Error' for url ...")],
        }

    要求：
    - failures 里每项是 (url, error) 元组；
    - 全部成功时 failures 为空列表。

    提示：用列表推导式筛 ok=False 的，别用两个循环。
    """
    raise NotImplementedError("TODO: 实现 summarize")
