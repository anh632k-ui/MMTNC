"""NMS: thu thập SNMP/local, đo ICMP RTT, lưu lịch sử và cảnh báo khi đổi trạng thái.

Giữ nguyên giao diện với web.py/notifier.py/snmp_utils.py của dự án.
Không tạo dữ liệu mẫu: OID/ping không hỗ trợ sẽ trả về None.
"""

import datetime
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from collections import deque

import psutil
import yaml

import notifier
from service_checks import check_http, check_tcp
from collector import get_local_metrics, list_up_ifaces, ping

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE, "state.json")
ALERT_FILE = os.path.join(BASE, "nms_alerts.jsonl")
METRICS_FILE = os.path.join(BASE, "nms_history.jsonl")
SERVICE_FILE = os.path.join(BASE, "nms_services.jsonl")
LOCK_FILE = os.path.join(BASE, ".nms-monitor.lock")

DATA_LOCK = threading.RLock()
LATEST = {}   # Các chỉ số hiện tại cho Dashboard
HISTORY = {}  # Tương thích API cũ: [cpu, ram] (60 mẫu)
SERIES = {}   # Dữ liệu theo thời gian: CPU/RAM/RTT/mất gói/Network I/O (120 mẫu)
ALERTS = deque(maxlen=150)
PREV_NET = {}  # Mẫu byte theo thiết bị/giao diện để tính KB/s
SERVICES = {}  # Kiểm tra HTTP/TCP gần nhất, tách khỏi thiết bị SNMP
SERVICE_HISTORY = {}  # 60 mẫu gần nhất cho từng dịch vụ

LABELS = {"reachable": "kết nối", "cpu": "CPU", "ram": "RAM", "temp": "nhiệt độ"}


def load_config(path=None):
    """Đọc config.yaml hoặc file cấu hình truyền qua dòng lệnh."""
    if path is None:
        args = [a for a in sys.argv[1:] if a.endswith((".yaml", ".yml"))]
        path = args[0] if args else "config.yaml"
    if not os.path.isabs(path):
        path = os.path.join(BASE, path)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                state = json.load(f)
            return state if isinstance(state, dict) else {}
        except (OSError, ValueError):
            return {}
    return {}


def save_state(state):
    temp = STATE_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(temp, STATE_FILE)


def now():
    return datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")


def iso_now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _append_jsonl(path, value):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(value, ensure_ascii=False) + "\n")
    except OSError as exc:
        print("Không ghi được lịch sử:", exc, flush=True)


def _read_last_jsonl(path, count=2500):
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            lines = deque(f, maxlen=count)
        result = []
        for line in lines:
            if not line.strip():
                continue
            try:
                result.append(json.loads(line))
            except ValueError:
                continue  # Bỏ qua một dòng hỏng, không mất cả lịch sử
        return result
    except OSError:
        return []


def _save_alert(cfg, device, key, severity, message):
    item = {
        "time": iso_now(), "device": device, "condition": key,
        "level": severity, "message": message,
    }
    with DATA_LOCK:
        ALERTS.append(item)
    _append_jsonl(ALERT_FILE, item)
    try:
        notifier.send(cfg, message)
    except Exception as exc:
        print("Gửi cảnh báo thất bại:", exc, flush=True)


def evaluate(cfg, name, m, state):
    """Chỉ gửi cảnh báo hoặc phục hồi khi trạng thái điều kiện thay đổi."""
    th = cfg["thresholds"]
    conds = {"reachable": (not m["reachable"], f"{name} không phản hồi")}
    if m["reachable"]:
        for key, label, unit in (("cpu", "CPU", "%"), ("ram", "RAM", "%"), ("temp", "Nhiệt độ", "°C")):
            value = m.get(key)
            if value is not None and th.get(key) is not None:
                conds[key] = (
                    value > th[key],
                    f"{name}: {label} = {value}{unit} (ngưỡng {th[key]}{unit})",
                )
        for ifname, status in m.get("ifaces", {}).items():
            if status in ("up", "down"):  # 'unknown' không được xem là DOWN
                conds[f"if:{ifname}"] = (status == "down", f"{name}: interface {ifname} DOWN")

    for key, (bad, message) in conds.items():
        state_key = f"{name}|{key}"
        was_bad = state.get(state_key, False)
        if bad and not was_bad:
            _save_alert(cfg, name, key, "warning", f"🚨 CẢNH BÁO [{now()}]\n{message}")
        elif not bad and was_bad:
            label = LABELS.get(key, key.replace("if:", "interface "))
            _save_alert(cfg, name, key, "recovered", f"✅ ĐÃ PHỤC HỒI [{now()}]\n{name}: {label} trở lại bình thường")
        state[state_key] = bad



def evaluate_service(cfg, name, result, state):
    """Báo Telegram 1 lần khi HTTP/TCP lỗi, 1 lần khi khôi phục."""
    key = f"service|{result['kind']}|{name}"
    bad = not result['ok']
    was_bad = state.get(key, False)
    detail = f"{name} [{result['endpoint']}]: {result['reason']}"
    if bad and not was_bad:
        _save_alert(cfg, name, key, "warning", f"🚨 CẢNH BÁO DỊCH VỤ [{now()}]\n{detail}")
    elif not bad and was_bad:
        _save_alert(cfg, name, key, "recovered", f"✅ ĐÃ PHỤC HỒI DỊCH VỤ [{now()}]\n{detail}")
    state[key] = bad


def check_services_once(cfg, state):
    """Giám sát duy nhất những URL/cổng đã khai báo, không quét dải cổng."""
    config = cfg.get("services") or {}
    for kind, check in (("http", check_http), ("tcp", check_tcp)):
        for item in config.get(kind) or []:
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            key = f"{kind}:{name}"
            try:
                measurement = check(item)
            except (KeyError, ValueError, TypeError) as exc:
                measurement = {"kind": kind, "endpoint": "Cấu hình lỗi",
                               "reachable": False, "ok": False,
                               "response_ms": None, "reason": f"Cấu hình không hợp lệ: {exc}"}
            measurement["time"] = now()
            with DATA_LOCK:
                SERVICES[key] = {"name": name, **measurement}
                SERVICE_HISTORY.setdefault(key, deque(maxlen=60)).append({
                    "time": iso_now(), "ok": measurement["ok"],
                    "response_ms": measurement.get("response_ms"),
                    "status_code": measurement.get("status_code")
                })
            evaluate_service(cfg, name, measurement, state)
            _append_jsonl(SERVICE_FILE, {"id": key, "name": name, "time": iso_now(), **measurement})
            print(now(), "DỊCH VỤ", name, measurement["reason"], flush=True)


def _parse_float(text):
    if text is None:
        return None
    try:
        return float(str(text).strip().strip('"'))
    except (ValueError, TypeError):
        return None


def probe_rtt(host):
    """1 ICMP echo thực tế; không suy diễn RTT từ trạng thái SNMP."""
    args = (["ping", "-n", "1", "-w", "1000", host] if os.name == "nt"
            else ["ping", "-c", "1", "-W", "1", host])
    try:
        res = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return None, None
    text = (res.stdout or "") + "\n" + (res.stderr or "")
    # Windows: time=15ms / time<1ms; Linux: time=0.512 ms
    match = re.search(r"(?:time|thời gian)\s*([=<])\s*([0-9]+(?:[.,][0-9]+)?)\s*ms", text, re.I)
    if res.returncode == 0:
        value = float(match.group(2).replace(",", ".")) if match else None
        return value, 0.0  # Một gói thành công -> 0% mất gói trong mẫu
    return None, 100.0   # Một gói thất bại -> 100% mất gói trong mẫu


def _rate_from_counters(key, received, sent):
    stamp = time.monotonic()
    old = PREV_NET.get(key)
    PREV_NET[key] = (stamp, received, sent)
    if old is None:
        return None, None
    delta_time = stamp - old[0]
    if delta_time <= 0:
        return None, None
    delta_rx, delta_tx = received - old[1], sent - old[2]
    # Nếu counter reset/quay vòng, bỏ mẫu này thay vì hiển thị một đỉnh giả.
    if delta_rx < 0 or delta_tx < 0:
        return None, None
    return round(delta_rx / delta_time / 1024, 2), round(delta_tx / delta_time / 1024, 2)


def _local_network_rate(watched):
    try:
        cards = psutil.net_io_counters(pernic=True)
        names = [name for name in watched if name in cards]
        if not names:
            return None, None
        rx = sum(cards[name].bytes_recv for name in names)
        tx = sum(cards[name].bytes_sent for name in names)
        return _rate_from_counters("local", rx, tx)
    except (OSError, AttributeError):
        return None, None


def _snmp_network_rate(dev):
    """Tính KB/s từ ifInOctets/ifOutOctets trên các ifIndex đã cấu hình."""
    indices = dev.get("interfaces") or []
    if not indices:
        return None, None
    try:
        from snmp_lite import snmp_get
        host, comm, port = dev["ip"], dev["snmp_community"], dev.get("port", 161)
        # Kết quả là tổng theo các cổng được theo dõi, không phải toàn bộ lưu lượng mạng vật lý.
        rx_total = tx_total = 0
        for index in indices:
            rx = _parse_float(snmp_get(host, comm, f"1.3.6.1.2.1.2.2.1.10.{index}", port=port))
            tx = _parse_float(snmp_get(host, comm, f"1.3.6.1.2.1.2.2.1.16.{index}", port=port))
            if rx is None or tx is None:
                return None, None
            rx_total += rx
            tx_total += tx
        return _rate_from_counters("snmp:" + dev["name"], rx_total, tx_total)
    except (OSError, KeyError, ValueError, TypeError):
        return None, None


def _compact_metrics_history():
    """Giới hạn dung lượng lịch sử trong thư mục dự án (tối đa khoảng 10 MB)."""
    try:
        if os.path.getsize(METRICS_FILE) < 10 * 1024 * 1024:
            return
        recent = _read_last_jsonl(METRICS_FILE, 3500)
        temporary = METRICS_FILE + ".tmp"
        with open(temporary, "w", encoding="utf-8") as f:
            for row in recent:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        os.replace(temporary, METRICS_FILE)
    except OSError as exc:
        print("Không thu gọn được lịch sử:", exc, flush=True)


def _persist_measurement(name, metrics):
    sample = {
        "time": iso_now(),
        "cpu": metrics.get("cpu"), "ram": metrics.get("ram"),
        "rtt_ms": metrics.get("rtt_ms"), "packet_loss": metrics.get("packet_loss"),
        "rx_kbps": metrics.get("rx_kbps"), "tx_kbps": metrics.get("tx_kbps"),
    }
    with DATA_LOCK:
        SERIES.setdefault(name, deque(maxlen=120)).append(sample)
        if sample["cpu"] is not None and sample["ram"] is not None:
            HISTORY.setdefault(name, deque(maxlen=60)).append([sample["cpu"], sample["ram"]])
    _append_jsonl(METRICS_FILE, {"device": name, **sample})


def restore_history():
    with DATA_LOCK:
        ALERTS.clear()
        SERIES.clear()
        HISTORY.clear()
        for item in _read_last_jsonl(ALERT_FILE, 150):
            if isinstance(item, dict):
                ALERTS.append(item)
        SERVICES.clear()
        SERVICE_HISTORY.clear()
        for item in _read_last_jsonl(SERVICE_FILE, 500):
            if not isinstance(item, dict) or not item.get("id"):
                continue
            sid = item["id"]
            SERVICES[sid] = {k: v for k, v in item.items() if k != "id"}
            SERVICE_HISTORY.setdefault(sid, deque(maxlen=60)).append({
                "time": item.get("time"), "ok": item.get("ok"),
                "response_ms": item.get("response_ms"), "status_code": item.get("status_code")
            })
        for item in _read_last_jsonl(METRICS_FILE, 3000):
            if not isinstance(item, dict) or not item.get("device"):
                continue
            name = item["device"]
            SERIES.setdefault(name, deque(maxlen=120)).append(
                {key: item.get(key) for key in ("time", "cpu", "ram", "rtt_ms", "packet_loss", "rx_kbps", "tx_kbps")}
            )
            if item.get("cpu") is not None and item.get("ram") is not None:
                HISTORY.setdefault(name, deque(maxlen=60)).append([item["cpu"], item["ram"]])


def get_snapshot(cfg):
    """API snapshot thread-safe, không chứa Bot Token/Community."""
    with DATA_LOCK:
        return {
            "thresholds": dict(cfg["thresholds"]),
            "devices": {k: dict(v) for k, v in LATEST.items()},
            "history": {k: list(v) for k, v in HISTORY.items()},
            "series": {k: list(v) for k, v in SERIES.items()},
            "alerts": list(reversed(ALERTS)),
            "services": {k: dict(v) for k, v in SERVICES.items()},
            "service_history": {k: list(v) for k, v in SERVICE_HISTORY.items()},
            "generated_at": iso_now(),
            "interval": cfg.get("interval", 5),
        }


def run_once(cfg, state, watched):
    local_name = socket.gethostname()
    local_metrics = get_local_metrics(watched)
    local_metrics["rx_kbps"], local_metrics["tx_kbps"] = _local_network_rate(watched)
    local_metrics.setdefault("rtt_ms", None)  # Không đo RTT tới chính máy mình
    local_metrics.setdefault("packet_loss", None)
    results = {local_name: local_metrics}

    for target in cfg.get("targets") or []:
        # Giữ cách kiểm tra ping trước đây, bổ sung RTT từ một gói đo riêng.
        reachable = ping(target["host"])
        rtt, loss = probe_rtt(target["host"])
        results[target["name"]] = {
            "reachable": reachable, "kind": "ping", "host": target["host"],
            "rtt_ms": rtt, "packet_loss": loss,
        }

    devices = cfg.get("devices") or []
    if devices:
        from snmp_utils import get_metrics
        for dev in devices:
            metrics = get_metrics(dev)
            if metrics.get("reachable"):
                metrics["rx_kbps"], metrics["tx_kbps"] = _snmp_network_rate(dev)
            else:
                metrics["rx_kbps"], metrics["tx_kbps"] = None, None
            metrics["rtt_ms"], metrics["packet_loss"] = probe_rtt(dev["ip"])
            results[dev["name"]] = metrics

    for name, metrics in results.items():
        evaluate(cfg, name, metrics, state)
        metrics["time"] = now()
        with DATA_LOCK:
            LATEST[name] = metrics
        _persist_measurement(name, metrics)
        print(now(), name, {k: v for k, v in metrics.items() if k != "time"}, flush=True)
    check_services_once(cfg, state)
    save_state(state)
    _compact_metrics_history()
    try:
        if os.path.getsize(SERVICE_FILE) > 5 * 1024 * 1024:
            last = _read_last_jsonl(SERVICE_FILE, 1500)
            tmp = SERVICE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                for item in last:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            os.replace(tmp, SERVICE_FILE)
    except OSError:
        pass


def _acquire_single_instance_lock():
    """Ngăn web.py và monitor.py cùng cảnh báo trùng trong một thư mục dự án."""
    fd = open(LOCK_FILE, "a+b")
    fd.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            if os.fstat(fd.fileno()).st_size == 0:
                fd.write(b"0")
                fd.flush()
            fd.seek(0)
            msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        fd.close()
        return None
    return fd  # Giữ mở tới khi tiến trình kết thúc


def loop(cfg):
    lock = _acquire_single_instance_lock()
    if lock is None:
        print("Đã có NMS Monitor chạy trong thư mục này; không khởi động vòng giám sát thứ hai.", flush=True)
        return
    try:
        restore_history()
        state = load_state()
        watched = cfg.get("interfaces") or list_up_ifaces()
        notifier.send(cfg, f"🟢 NMS Monitor đã khởi động [{now()}]\nInterface theo dõi: {', '.join(watched) or '(không có)'}")
        while True:
            try:
                run_once(cfg, state, watched)
            except Exception as exc:
                print("Lỗi trong vòng giám sát:", exc, flush=True)
            time.sleep(max(1, float(cfg.get("interval", 5))))
    finally:
        lock.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    loop(load_config())
