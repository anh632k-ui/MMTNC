"""Thu thập CPU, RAM và trạng thái interface của Ubuntu bằng SNMP v2c."""

from pysnmp.hlapi import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
    nextCmd,
)

OID_CPU_IDLE = "1.3.6.1.4.1.2021.11.11.0"
OID_MEM_TOTAL = "1.3.6.1.4.1.2021.4.5.0"
OID_MEM_AVAIL = "1.3.6.1.4.1.2021.4.6.0"
OID_IF_NAME = "1.3.6.1.2.1.2.2.1.2"
OID_IF_OPER = "1.3.6.1.2.1.2.2.1.8"

IP = "192.168.10.128"
COMMUNITY = "labMmtnc2026"


def snmp_get(ip, community, oid, timeout=2, retries=1):
    """Lấy giá trị một OID, trả về None nếu truy vấn thất bại."""
    try:
        response = getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1),
            UdpTransportTarget((ip, 161), timeout=timeout, retries=retries),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )
        error_indication, error_status, _, var_binds = next(response)
        if error_indication or error_status or not var_binds:
            print(f"[SNMP] GET {oid}: {error_indication or error_status}")
            return None
        return var_binds[0][1]
    except Exception as exc:
        print(f"[SNMP] GET {oid}: {exc}")
        return None


def snmp_walk(ip, community, oid):
    """Trả về dict {chỉ_số_interface: giá_trị} cho một nhánh OID."""
    result = {}
    try:
        response = nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1),
            UdpTransportTarget((ip, 161), timeout=2, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False,
        )
        for error_indication, error_status, _, var_binds in response:
            if error_indication or error_status:
                print(f"[SNMP] WALK {oid}: {error_indication or error_status}")
                break
            for name, value in var_binds:
                idx = str(name).split(".")[-1]
                result[idx] = value
    except Exception as exc:
        print(f"[SNMP] WALK {oid}: {exc}")
    return result


def get_cpu_usage(ip, community):
    idle = snmp_get(ip, community, OID_CPU_IDLE)
    return None if idle is None else 100 - int(idle)


def get_ram_usage(ip, community):
    total = snmp_get(ip, community, OID_MEM_TOTAL)
    avail = snmp_get(ip, community, OID_MEM_AVAIL)
    if total is None or avail is None or int(total) <= 0:
        return None
    return round((int(total) - int(avail)) / int(total) * 100, 1)


def get_interfaces(ip, community):
    names = snmp_walk(ip, community, OID_IF_NAME)
    statuses = snmp_walk(ip, community, OID_IF_OPER)
    return {
        idx: {"name": str(names.get(idx, f"if{idx}")), "up": int(status) == 1}
        for idx, status in statuses.items()
    }


if __name__ == "__main__":
    print(f"Thiết bị: {IP}")
    print("CPU sử dụng (%):", get_cpu_usage(IP, COMMUNITY))
    print("RAM sử dụng (%):", get_ram_usage(IP, COMMUNITY))
    for idx, info in get_interfaces(IP, COMMUNITY).items():
        print(f"Interface {idx}: {info['name']} -> {'UP' if info['up'] else 'DOWN'}")
