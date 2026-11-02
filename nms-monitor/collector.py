"""Thu thập số liệu của máy đang chạy script (CPU, RAM, nhiệt độ, interface) và ping."""
import platform
import subprocess

import psutil


def _temperature():
    """Nhiệt độ CPU (°C). Trả None nếu máy không có cảm biến (Windows thường không có)."""
    try:
        sensors = psutil.sensors_temperatures()
    except Exception:
        return None
    for entries in sensors.values():
        for e in entries:
            if e.current:
                return round(e.current, 1)
    return None


def list_up_ifaces():
    return [n for n, s in psutil.net_if_stats().items() if s.isup]


def get_local_metrics(watched):
    stats = psutil.net_if_stats()
    return {
        "reachable": True,
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "temp": _temperature(),
        "ifaces": {n: ("up" if n in stats and stats[n].isup else "down") for n in watched},
    }


def ping(host, timeout=2):
    """True nếu host trả lời ping."""
    if platform.system() == "Windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout), host]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, errors="ignore",
                             timeout=timeout + 3)
        # Windows trả mã 0 cả khi nhận "Destination host unreachable", nên kiểm tra thêm TTL
        return out.returncode == 0 and "TTL=" in out.stdout.upper()
    except Exception:
        return False
