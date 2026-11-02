
"""Giam sat Cisco Router va Ubuntu Linux qua SNMP v2c."""

from snmp_lite import snmp_get


CISCO_OID = {
    "cpu": "1.3.6.1.4.1.9.9.109.1.1.1.1.7.1",
    "mem_used": "1.3.6.1.4.1.9.9.48.1.1.1.5.1",
    "mem_free": "1.3.6.1.4.1.9.9.48.1.1.1.6.1",
    "temp": "1.3.6.1.4.1.9.9.13.1.3.1.3.1",
}

LINUX_OID = {
    "cpu_idle": "1.3.6.1.4.1.2021.11.11.0",
    "mem_total": "1.3.6.1.4.1.2021.4.5.0",
    "mem_free": "1.3.6.1.4.1.2021.4.6.0",
    "mem_buffer": "1.3.6.1.4.1.2021.4.14.0",
    "mem_cached": "1.3.6.1.4.1.2021.4.15.0",
}

IF_NAME = "1.3.6.1.2.1.2.2.1.2."
IF_STATUS = "1.3.6.1.2.1.2.2.1.8."


def to_number(value):
    if value is None:
        return None

    try:
        return float(str(value).strip().strip('"'))
    except (ValueError, TypeError):
        return None


def get_metrics(dev):
    ip = dev["ip"]
    community = dev["snmp_community"]
    port = dev.get("port", 161)

    def get(oid):
        return snmp_get(ip, community, oid, port=port)

    # Kiem tra thiet bi co phan hoi SNMP hay khong
    hostname = get("1.3.6.1.2.1.1.5.0")

    m = {
        "reachable": hostname is not None,
        "cpu": None,
        "ram": None,
        "temp": None,
        "ifaces": {},
    }

    if not m["reachable"]:
        return m

    # Nhan dien Ubuntu Linux qua UCD-SNMP-MIB
    idle = to_number(get(LINUX_OID["cpu_idle"]))

    if idle is not None:
        # ===== UBUNTU / LINUX =====
        m["cpu"] = round(
            max(0, min(100, 100 - idle)), 1
        )

        total = to_number(get(LINUX_OID["mem_total"]))
        free = to_number(get(LINUX_OID["mem_free"]))
        buffers = to_number(get(LINUX_OID["mem_buffer"]))
        cached = to_number(get(LINUX_OID["mem_cached"]))

        if total is not None and total > 0 and free is not None:
            # Tru bo phan RAM co the thu hoi (cache/buffers)
            reclaimable = (buffers or 0) + (cached or 0)
            used = total - free - reclaimable
            percent = used / total * 100
            m["ram"] = round(
                max(0, min(100, percent)), 1
            )

        # Nhiet do khong co OID chung tin cay
        m["temp"] = None

    else:
        # ===== CISCO ROUTER =====
        m["cpu"] = to_number(get(CISCO_OID["cpu"]))

        used = to_number(get(CISCO_OID["mem_used"]))
        free = to_number(get(CISCO_OID["mem_free"]))

        if (
            used is not None
            and free is not None
            and used + free > 0
        ):
            m["ram"] = round(
                used / (used + free) * 100, 1
            )

        m["temp"] = to_number(get(CISCO_OID["temp"]))

    # ===== GIAM SAT INTERFACE =====
    for idx in dev.get("interfaces", []):
        name = get(IF_NAME + str(idx)) or f"if{idx}"
        status = get(IF_STATUS + str(idx))

        value = str(status).strip().lower() if status is not None else ""

        if value == "1" or value.startswith("up"):
            state = "up"
        elif value == "2" or value.startswith("down"):
            state = "down"
        else:
            state = "unknown"

        m["ifaces"][str(name)] = state

    return m
