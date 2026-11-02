"""Day 2 的测试 —— 跑在真实的本地服务器上（见 conftest.py）。

每个测试都会验证"行为"而不只是"返回值"：
- 是否真的并发（看服务器记录的峰值并发数）
- 限流是否真的生效（峰值不能超过 limit）
- 重试是否真的重试（服务器故意失败前 N 次）
"""

import time
from typing import Any

import httpx
import pytest

from async_http import fetch_all, fetch_limited, fetch_with_retry


async def test_fetch_all_returns_texts(clean_state: tuple[str, dict[str, Any]]) -> None:
    base, _ = clean_state
    urls = [f"{base}/a", f"{base}/b", f"{base}/c"]

    assert await fetch_all(urls) == ["ok", "ok", "ok"]


async def test_fetch_all_runs_concurrently(clean_state: tuple[str, dict[str, Any]]) -> None:
    """10 个请求、每个 0.15s：串行要 1.5s，并发应该在 0.7s 以内。"""
    base, state = clean_state
    urls = [f"{base}/x{i}" for i in range(10)]

    start = time.perf_counter()
    results = await fetch_all(urls)
    elapsed = time.perf_counter() - start

    assert len(results) == 10
    assert elapsed < 0.7, f"看起来没并发：{elapsed:.2f}s"
    assert state["max_active"] >= 5, f"峰值并发只有 {state['max_active']}"


async def test_fetch_limited_caps_concurrency(clean_state: tuple[str, dict[str, Any]]) -> None:
    base, state = clean_state
    urls = [f"{base}/l{i}" for i in range(10)]

    results = await fetch_limited(urls, limit=3)

    assert len(results) == 10
    assert state["max_active"] <= 3, f"超过限流：峰值 {state['max_active']} > 3"


async def test_fetch_limited_still_parallel(clean_state: tuple[str, dict[str, Any]]) -> None:
    """限流 3 不代表串行，峰值应该能达到 3 左右。"""
    base, state = clean_state
    urls = [f"{base}/p{i}" for i in range(9)]

    await fetch_limited(urls, limit=3)

    assert state["max_active"] >= 2


async def test_retry_succeeds_after_failures(
    clean_state: tuple[str, dict[str, Any]],
) -> None:
    """服务器前 2 次返回 500，第 3 次成功。"""
    base, state = clean_state
    state["fail_first"]["/flaky"] = 2

    assert await fetch_with_retry(f"{base}/flaky", times=3) == "ok"
    assert state["calls"]["/flaky"] == 3  # 确实试了 3 次


async def test_retry_gives_up(clean_state: tuple[str, dict[str, Any]]) -> None:
    base, state = clean_state
    state["fail_first"]["/bad"] = 99

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_with_retry(f"{base}/bad", times=2)

    assert state["calls"]["/bad"] == 2
