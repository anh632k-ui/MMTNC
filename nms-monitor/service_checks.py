"""Kiểm tra HTTP/HTTPS và một số cổng TCP được người vận hành khai báo.

Tái sử dụng ý tưởng của Lab 4/Lab 5. Không quét dải cổng và không tạo
web lỗi mô phỏng trong quá trình giám sát thực tế.
"""

import errno
import socket
import time
import urllib.error
import urllib.request


def _timeout(config, default=3.0):
    try:
        return min(10.0, max(0.2, float(config.get("timeout", default))))
    except (TypeError, ValueError):
        return default



def _friendly_connect_error(error):
    """Chuyển lỗi mạng của Python/Windows/Linux thành thông báo dễ đọc.

    Không hiển thị traceback hoặc toàn bộ exception trong Dashboard/Telegram.
    """
    cause = error.reason if isinstance(error, urllib.error.URLError) else error
    winerror = getattr(cause, "winerror", None)
    err_no = getattr(cause, "errno", None)

    if (isinstance(cause, ConnectionRefusedError)
            or winerror == 10061 or err_no == errno.ECONNREFUSED):
        return "Dịch vụ không chấp nhận kết nối (cổng có thể đang đóng)"
    if (isinstance(cause, TimeoutError)
            or winerror == 10060 or err_no == errno.ETIMEDOUT):
        return "Hết thời gian chờ phản hồi từ dịch vụ"
    if isinstance(cause, socket.gaierror):
        return "Không phân giải được tên máy chủ"
    if isinstance(cause, ConnectionResetError) or winerror == 10054:
        return "Máy chủ đã ngắt kết nối"
    if (winerror in (10051, 10065)
            or err_no in (errno.ENETUNREACH, errno.EHOSTUNREACH)):
        return "Không có đường kết nối tới máy chủ"
    return "Không thể kết nối đến dịch vụ (kiểm tra IP, cổng hoặc tường lửa)"

def check_http(config):
    """Kết quả 'ok' chỉ đúng khi HTTP status khớp và không quá chậm."""
    url = str(config.get("url", "")).strip()
    expected = int(config.get("expected_status", 200))
    limit = float(config.get("max_response_seconds", 3))
    start = time.monotonic()
    status = None
    error = ""
    try:
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL phải bắt đầu bằng http:// hoặc https://")
        req = urllib.request.Request(url, headers={"User-Agent": "NMS-Monitor/2.1"})
        with urllib.request.urlopen(req, timeout=_timeout(config, 6)) as resp:
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except ValueError as exc:
        error = str(exc)[:180]
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        error = _friendly_connect_error(exc)
    seconds = round(time.monotonic() - start, 3)
    ok = status == expected and seconds <= limit and not error
    if error:
        reason = f"Không kết nối: {error}"
    elif status != expected:
        reason = f"HTTP {status} (mong đợi {expected})"
    elif seconds > limit:
        reason = f"Phản hồi {seconds:.2f}s vượt ngưỡng {limit:g}s"
    else:
        reason = "HTTP bình thường"
    return {"kind": "http", "endpoint": url, "reachable": status is not None,
            "ok": ok, "status_code": status, "response_ms": round(seconds * 1000, 1),
            "max_response_ms": round(limit * 1000, 1), "reason": reason}


def check_tcp(config):
    """TCP connect tới đúng một host:port; không quét hàng loạt."""
    host = str(config.get("host", "")).strip()
    port = int(config["port"])
    if not host or not (1 <= port <= 65535):
        raise ValueError("Host/port TCP không hợp lệ")
    start = time.monotonic()
    error = ""
    try:
        with socket.create_connection((host, port), timeout=_timeout(config)):
            pass
        ok = True
    except (OSError, TimeoutError) as exc:
        ok = False
        error = _friendly_connect_error(exc)
    seconds = round(time.monotonic() - start, 3)
    return {"kind": "tcp", "endpoint": f"{host}:{port}", "reachable": ok,
            "ok": ok, "port": port, "response_ms": round(seconds * 1000, 1),
            "reason": "Cổng TCP chấp nhận kết nối" if ok else f"Không kết nối TCP: {error}"}
