"""Server HTTP kiểm thử cục bộ từ Lab 4: /ok, /error, /slow.

Chỉ chạy thủ công khi demo; không sử dụng làm API sản xuất.
"""
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            time.sleep(4)
        code = 503 if self.path == "/error" else 200 if self.path in ("/ok", "/slow") else 404
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        try:
            self.wfile.write(f"HTTP {code}".encode())
        except BrokenPipeError:
            pass

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Demo Lab 4: http://127.0.0.1:8765/ok, /error, /slow")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Đã dừng demo HTTP")
    finally:
        server.server_close()
