"""Day 2 实验：一个"慢"服务器（每次请求睡 0.3 秒）

模拟真实世界的网络延迟：数据库查询、第三方 API、磁盘 IO——都要等。
没有这个"等"，同步和异步的差别就看不出来。

用法：
    uv run python slow_server.py       # 终端 A 跑着
"""

import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DELAY = 0.3  # 秒


class SlowHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        time.sleep(DELAY)  # 关键：模拟"等待 IO"
        body = b"ok\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


class SlowServer(ThreadingHTTPServer):
    # backlog 是**服务器**的属性（写在 Handler 上无效）：
    # 默认只有 5，10 个并发连接会在内核队列里排队，把"异步"拖成"伪串行"
    request_queue_size = 128
    daemon_threads = True


if __name__ == "__main__":
    server = SlowServer(("127.0.0.1", 8100), SlowHandler)
    print(f"慢服务器启动：http://127.0.0.1:8100/  （每次请求延迟 {DELAY}s）")
    server.serve_forever()
