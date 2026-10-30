"""Phát hiện vượt ngưỡng, interface DOWN và trạng thái khôi phục."""

from collector import get_cpu_usage, get_ram_usage, get_interfaces

# Chỉ gửi tin khi trạng thái chuyển đổi; giữ trong bộ nhớ khi tiến trình đang chạy.
STATE = {}


def _transition(key, is_bad):
    previous = STATE.get(key, "ok")
    current = "alert" if is_bad else "ok"
    STATE[key] = current
    if previous == "ok" and current == "alert":
        return "alert"
    if previous == "alert" and current == "ok":
        return "recovered"
    return None


def _message(event, label, detail):
    if event == "alert":
        return f"🚨 {label}: {detail}"
    if event == "recovered":
        return f"✅ {label} đã trở về bình thường"
    return None


def analyze_device(dev, thresholds):
    """Trả về danh sách tin cần gửi trong chu kỳ hiện tại."""
    name, ip, community = dev["name"], dev["ip"], dev["community"]
    messages = []
    cpu = get_cpu_usage(ip, community)
    ram = get_ram_usage(ip, community)

    unreachable = cpu is None and ram is None
    event = _transition(f"{name}:reach", unreachable)
    msg = _message(event, name, "mất kết nối SNMP")
    if msg:
        messages.append(msg)
    if unreachable:
        return messages

    if cpu is not None:
        event = _transition(f"{name}:cpu", cpu > thresholds["cpu"])
        msg = _message(event, f"{name} CPU", f"{cpu}% (ngưỡng {thresholds['cpu']}%)")
        if msg:
            messages.append(msg)

    if ram is not None:
        event = _transition(f"{name}:ram", ram > thresholds["ram"])
        msg = _message(event, f"{name} RAM", f"{ram}% (ngưỡng {thresholds['ram']}%)")
        if msg:
            messages.append(msg)

    for idx, info in get_interfaces(ip, community).items():
        name_if = info["name"]
        event = _transition(f"{name}:if:{name_if}", not info["up"])
        msg = _message(event, f"{name} interface {name_if}", "DOWN")
        if msg:
            messages.append(msg)

    return messages


if __name__ == "__main__":
    device = {"name": "anh-ubutun-sdn", "ip": "192.168.10.128", "community": "labMmtnc2026"}
    thresholds = {"cpu": 80, "ram": 85}
    print("Lần 1:", analyze_device(device, thresholds))
    print("Lần 2 (không đổi trạng thái):", analyze_device(device, thresholds))
