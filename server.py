"""Day 1 实验：一个最小 HTTP 服务器（已经写好，不用改）

作用：让你能"看到"客户端发来的原始请求。

用法（开一个终端跑着，别关）：
    uv run python server.py

然后在浏览器访问 http://127.0.0.1:8000/
终端会打印出完整的请求报文 —— 这就是 HTTP 请求的真身。
"""

from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        # 把收到的请求原样打印出来（这是本次实验的重点）
        print("=" * 60)
        print(f"请求行: {self.command} {self.path} {self.request_version}")
        print("请求头:")
        for key, value in self.headers.items():
            print(f"  {key}: {value}")
        print("=" * 60, flush=True)

        body = "hello from server\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format: str, *args) -> None:
        # 关掉默认的访问日志，让输出干净一点
        return


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    print("监听 http://127.0.0.1:8000/ ，Ctrl+C 停止")
    server.serve_forever()
