"""Day 1 练习：用 socket 手写一个 HTTP 请求（你要实现的）

目标：不用 requests/httpx，用最原始的 TCP 套接字发出这条报文，并打印服务器的原始响应。

    GET / HTTP/1.1\r\n
    Host: 127.0.0.1:8000\r\n
    Connection: close\r\n
    \r\n

⚠️ 注意 `\r\n`（回车+换行）——HTTP 协议规定行尾必须是 CRLF，不是单个 \n。
   用单个 \n 时，有的服务器直接 400；有的能容忍，但那是运气。

用法：
    终端 A：uv run python server.py
    终端 B：uv run python raw_request.py

运行后你应该看到：
    1) 你发出去的报文（原样打印）
    2) 服务器返回的原始响应（状态行 + 头 + 空行 + 正文）
"""

import socket


def build_request(host: str, port: int, path: str = "/") -> bytes:
    """拼出完整的 HTTP 请求报文（返回 bytes）。

    要求：
    - 请求行：`GET {path} HTTP/1.1`
    - 请求头：`Host: {host}:{port}`、`Connection: close`
    - 每行以 \r\n 结尾，最后再补一个空行（也就是 \r\n\r\n 结尾）
    - 返回 encode("utf-8") 之后的 bytes

    提示：用列表 + "\r\n".join(lines) 再手动加结尾的 "\r\n\r\n"。
    """
    request_line = f"GET {path} HTTP/1.1"
    request_head = (f"Host: {host}:{port}\r\n"
                    f"Connection: close\r\n")
    return (request_line+"\r\n"+request_head+"\r\n").encode("utf-8")


def fetch(host: str, port: int, path: str = "/") -> bytes:
    """建立 TCP 连接 → 发送报文 → 读回所有数据 → 返回原始响应 bytes。

    要求：
    - 用 socket.create_connection((host, port), timeout=5) 建连接（自动处理 DNS 和三次握手）
    - sendall 发送 build_request(...) 的结果
    - 循环 recv(4096) 直到收到 b""（对方关闭连接）
    - 返回拼起来的 bytes

    提示：
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.sendall(request)
            chunks = []
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
        return b"".join(chunks)

    为什么要 recv 多次？因为 TCP 是"流"，一次 recv 可能只拿到一部分。
    """
    req = build_request(host, port, path)
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(req)
        chunks = []
        while True:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)
    return b"".join(chunks)


if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 8000

    request = build_request(HOST, PORT)
    print("=== 我要发出去的原始报文 ===")
    print(request.decode())
    print("（上面每个空行都是 \\r\\n）")

    response = fetch(HOST, PORT)
    print("=== 服务器返回的原始响应 ===")
    # 只解码前 800 字节，避免刷屏；中文/二进制混在一起时用 errors="replace"
    print(response[:800].decode("utf-8", errors="replace"))
