"""测试用的本地 HTTP 服务器夹具。

为什么不用 mock：这次要验证的是**真实并发**（同时有几个请求在飞），
mock 出来的假响应测不出这件事。所以起一个真服务器，用计数器记录峰值并发。
"""

import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

DELAY = 0.15  # 每个请求的延迟（秒）
# 说明：延迟放大到 0.15s，是为了让"并发"和"串行"的差距远大于网络/线程开销，
# 否则测试会因为机器快慢而时好时坏（10 个请求：串行 1.5s，并发约 0.3s）。


class BigBacklogServer(ThreadingHTTPServer):
    """默认 listen 队列只有 5，10 个并发会在内核队列里排队。

    注意：request_queue_size 是**服务器**的属性，写在 Handler 上无效。
    """

    request_queue_size = 128
    daemon_threads = True


@pytest.fixture(scope="session")
def server() -> Iterator[tuple[str, dict[str, Any]]]:
    state: dict[str, Any] = {"active": 0, "max_active": 0, "calls": {}, "fail_first": {}}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            with lock:
                state["active"] += 1
                state["max_active"] = max(state["max_active"], state["active"])
                count = state["calls"].get(self.path, 0)
                state["calls"][self.path] = count + 1

            time.sleep(DELAY)

            with lock:
                state["active"] -= 1

            fail_times = state["fail_first"].get(self.path, 0)
            if count < fail_times:
                self.send_response(500)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    lock = threading.Lock()
    httpd = BigBacklogServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        yield base, state
    finally:
        httpd.shutdown()


@pytest.fixture
def clean_state(server: tuple[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    """每个测试前清空计数器。"""
    base, state = server
    state["active"] = 0
    state["max_active"] = 0
    state["calls"].clear()
    state["fail_first"].clear()
    return base, state
