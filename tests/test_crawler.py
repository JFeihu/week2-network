"""Day 3 的测试 —— 用同一个真实服务器（conftest.py）。"""

from typing import Any

from crawler import FetchResult, crawl, summarize


async def test_crawl_all_success(clean_state: tuple[str, dict[str, Any]]) -> None:
    base, _ = clean_state
    urls = [f"{base}/a", f"{base}/b", f"{base}/c"]

    results = await crawl(urls)

    assert [r.ok for r in results] == [True, True, True]
    assert [r.text for r in results] == ["ok", "ok", "ok"]
    assert [r.status for r in results] == [200, 200, 200]


async def test_crawl_keeps_input_order(clean_state: tuple[str, dict[str, Any]]) -> None:
    base, _ = clean_state
    urls = [f"{base}/z", f"{base}/a", f"{base}/m"]

    results = await crawl(urls)

    assert [r.url for r in results] == urls


async def test_crawl_records_failure_without_raising(
    clean_state: tuple[str, dict[str, Any]],
) -> None:
    """一个 URL 一直 500，其他正常的应该照常返回。"""
    base, state = clean_state
    state["fail_first"]["/bad"] = 99
    urls = [f"{base}/good", f"{base}/bad"]

    results = await crawl(urls, retries=0)

    assert results[0].ok is True
    assert results[1].ok is False
    assert results[1].error is not None
    assert results[1].status is None


async def test_crawl_retries_then_succeeds(clean_state: tuple[str, dict[str, Any]]) -> None:
    """服务器前 2 次 500，第 3 次成功；retries=2 表示总共试 3 次。"""
    base, state = clean_state
    state["fail_first"]["/flaky"] = 2

    results = await crawl([f"{base}/flaky"], retries=2)

    assert results[0].ok is True
    assert state["calls"]["/flaky"] == 3


async def test_crawl_respects_limit(clean_state: tuple[str, dict[str, Any]]) -> None:
    base, state = clean_state
    urls = [f"{base}/l{i}" for i in range(9)]

    results = await crawl(urls, limit=3)

    assert len(results) == 9
    assert state["max_active"] <= 3


async def test_crawl_handles_connection_error(clean_state: tuple[str, dict[str, Any]]) -> None:
    """连不上的地址不应该让整个爬取崩溃。"""
    base, _ = clean_state
    urls = [f"{base}/ok", "http://127.0.0.1:1/nope"]

    results = await crawl(urls, retries=0)

    assert results[0].ok is True
    assert results[1].ok is False


def test_summarize_counts() -> None:
    results = [
        FetchResult(url="a", ok=True, status=200, text="ok"),
        FetchResult(url="b", ok=True, status=200, text="ok"),
        FetchResult(url="c", ok=False, error="HTTP 500"),
    ]

    summary = summarize(results)

    assert summary["total"] == 3
    assert summary["ok"] == 2
    assert summary["failed"] == 1
    assert summary["failures"] == [("c", "HTTP 500")]


def test_summarize_all_success() -> None:
    results = [FetchResult(url="a", ok=True, status=200, text="ok")]

    summary = summarize(results)

    assert summary["failed"] == 0
    assert summary["failures"] == []
