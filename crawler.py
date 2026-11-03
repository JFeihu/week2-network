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
    异步批量抓取一批url，控制并发 + 失败自动重试
    :param urls: 需要抓取的url列表
    :param limit: 并发信号量上限
    :param retries: 重试次数
    :param timeout: 请求超时
    :return: 和urls顺序一一对应的FetchResult结果列表

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
                            return FetchResult(
                                url=url,
                                ok=True,
                                status=resp.status_code,
                                text=resp.text)
                        except Exception as exc:
                            last = str(exc)
                    await asyncio.sleep(0.01)
                return FetchResult(url=url, ok=False, error=last)

            return list(await asyncio.gather(*(one(u) for u in urls)))

    注意：受 asyncio.gather 保护，one() 里不要让异常冒出去，否则整个 gather 会失败。
    """
    # 信号量：用来限制并发数量，防止同时请求过多
    sem = asyncio.Semaphore(limit)

    # 创建异步 http 客户端，with 语法会自动关闭
    async with httpx.AsyncClient(timeout=timeout) as client:

        async def one(url):
            """抓取单个url，带重试逻辑"""
            lastError = "未知错误"
            for _ in range(retries + 1):  # 循环：总共尝试 retries+1 次
                async with sem:
                    # 进入信号量保护区，控制并发
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()  # 状态码4xx/5xx 直接抛出异常
                        # 请求成功，返回结果
                        return FetchResult(
                            url=url, ok=True, status=resp.status_code, text=resp.text
                        )
                    except Exception as exc:
                        # 捕获所有异常，记录最新的错误信息
                        lastError = str(exc)
                # 释放信号量后短暂休眠，避免疯狂重试
                await asyncio.sleep(0.01)
            # 全部重试机会用完仍然失败，返回失败结果
            return FetchResult(url=url, ok=False, error=lastError)

        # gather 并发执行所有one 任务，结果顺序和url保持一致
        return list(await asyncio.gather(*(one(u) for u in urls)))


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
    failures = [(r.url, r.error) for r in results if not r.ok]
    return {
        "total": len(results),
        "ok": len(results) - len(failures),
        "failed": len(failures),
        "failures": failures,
    }
