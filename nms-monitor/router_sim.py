"""Giả lập 3 router Cisco (R1, R2, R3) trả lời SNMP trên máy của bạn.
Chạy trong một terminal riêng, gõ lệnh để tạo sự cố (giống thao tác trên router thật).
Gõ 'help' để xem danh sách lệnh."""
import random
import socket
import threading

from snmp_lite import (END_OF_MIB_VIEW, NO_SUCH_INSTANCE, build_response, enc_gauge, enc_int,
                       enc_octets, parse_message)

COMMUNITY = "monitor123"
HOST = "127.0.0.1"

SYS_NAME = (1, 3, 6, 1, 2, 1, 1, 5, 0)
CPU = (1, 3, 6, 1, 4, 1, 9, 9, 109, 1, 1, 1, 1, 7, 1)
MEM_USED = (1, 3, 6, 1, 4, 1, 9, 9, 48, 1, 1, 1, 5, 1)
MEM_FREE = (1, 3, 6, 1, 4, 1, 9, 9, 48, 1, 1, 1, 6, 1)
TEMP = (1, 3, 6, 1, 4, 1, 9, 9, 13, 1, 3, 1, 3, 1)
IF_DESCR = (1, 3, 6, 1, 2, 1, 2, 2, 1, 2)
IF_STATUS = (1, 3, 6, 1, 2, 1, 2, 2, 1, 8)

TOTAL_MEM = 128 * 1024 * 1024
IFACES = {1: "FastEthernet0/0", 2: "FastEthernet0/1", 3: "Loopback0"}

HELP = """Lệnh (tên router: R1, R2, R3; ifIndex: 1 = FastEthernet0/0, 2 = FastEthernet0/1, 3 = Loopback0)
  status                 xem trạng thái các router
  down R2 1              tắt interface (giống: int fa0/0 > shutdown)
  up R2 1                bật lại interface (giống: no shutdown)
  cpu R1 95              ép CPU lên 95%      |  cpu R1 auto   trả về dao động tự nhiên
  ram R1 92              ép RAM lên 92%      |  ram R1 auto
  temp R1 75             giả lập có cảm biến nhiệt độ 75 °C  |  temp R1 off   bỏ cảm biến
  off R3                 tắt hẳn router (không trả lời SNMP) |  on R3   bật lại
  help                   hiện bảng này
  quit                   thoát"""


class Router:
    def __init__(self, name, port, cpu_base, ram_base):
        self.name, self.port = name, port
        self.cpu_base, self.ram_base = cpu_base, ram_base
        self.cpu_set = self.ram_set = self.temp = None
        self.up = {i: True for i in IFACES}
        self.online = True

    def cpu(self):
        if self.cpu_set is not None:
            return self.cpu_set
        return max(1, min(99, round(self.cpu_base + random.uniform(-3, 3))))

    def ram_pct(self):
        if self.ram_set is not None:
            return self.ram_set
        return max(1.0, min(99.0, self.ram_base + random.uniform(-1, 1)))

    def table(self):
        used = int(TOTAL_MEM * self.ram_pct() / 100)
        t = {
            SYS_NAME: enc_octets(self.name),
            CPU: enc_gauge(self.cpu()),
            MEM_USED: enc_gauge(used),
            MEM_FREE: enc_gauge(TOTAL_MEM - used),
        }
        if self.temp is not None:
            t[TEMP] = enc_gauge(self.temp)
        for idx, ifname in IFACES.items():
            t[IF_DESCR + (idx,)] = enc_octets(ifname)
            t[IF_STATUS + (idx,)] = enc_int(1 if self.up[idx] else 2)
        return t


def answer(router, msg):
    table = router.table()
    keys = sorted(table)
    out = []
    for oid, _, _ in msg["varbinds"]:
        if msg["pdu_tag"] == 0xA0:                       # GET
            out.append((oid, table.get(oid, NO_SUCH_INSTANCE)))
        else:                                            # GETNEXT
            nxt = next((k for k in keys if k > oid), None)
            out.append((nxt, table[nxt]) if nxt else (oid, END_OF_MIB_VIEW))
    return build_response(msg["community"], msg["req_id"], out, msg["version"])


def serve(router):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((HOST, router.port))
    except OSError as e:
        print(f"Không mở được cổng {router.port} cho {router.name}: {e}")
        return
    sock.settimeout(0.5)
    while True:
        try:
            data, addr = sock.recvfrom(65535)
        except socket.timeout:
            continue
        except OSError:
            continue
        if not router.online:
            continue                                     # router "tắt": im lặng như thiết bị thật
        try:
            msg = parse_message(data)
            if msg["version"] != 1 or msg["community"] != COMMUNITY or msg["pdu_tag"] not in (0xA0, 0xA1):
                continue
            sock.sendto(answer(router, msg), addr)
        except Exception:
            continue


def show_status(routers):
    for r in routers.values():
        ifs = ", ".join(f"{IFACES[i]}={'up' if r.up[i] else 'DOWN'}" for i in IFACES)
        temp = f"{r.temp} °C" if r.temp is not None else "không có cảm biến"
        print(f"{r.name} (cổng {r.port}) {'BẬT' if r.online else 'TẮT'} | CPU {r.cpu()}% | "
              f"RAM {r.ram_pct():.0f}% | nhiệt độ: {temp} | {ifs}")


def run_command(routers, line):
    parts = line.split()
    if not parts:
        return
    cmd = parts[0].lower()
    if cmd in ("help", "?"):
        print(HELP)
    elif cmd == "status":
        show_status(routers)
    elif cmd in ("quit", "exit"):
        raise SystemExit
    else:
        r = routers.get(parts[1].upper()) if len(parts) > 1 else None
        if r is None:
            print("Thiếu hoặc sai tên router (R1, R2, R3). Gõ help để xem lệnh.")
        elif cmd in ("down", "up"):
            idx = int(parts[2])
            if idx not in IFACES:
                print("ifIndex phải là 1, 2 hoặc 3")
                return
            r.up[idx] = cmd == "up"
            print(f"{r.name}: {IFACES[idx]} -> {'up' if r.up[idx] else 'DOWN'}")
        elif cmd in ("cpu", "ram"):
            val = None if parts[2].lower() == "auto" else float(parts[2])
            setattr(r, cmd + "_set", val)
            print(f"{r.name}: {cmd.upper()} -> {'tự động' if val is None else str(val) + '%'}")
        elif cmd == "temp":
            r.temp = None if parts[2].lower() == "off" else float(parts[2])
            print(f"{r.name}: nhiệt độ -> {'không có cảm biến' if r.temp is None else str(r.temp) + ' °C'}")
        elif cmd in ("off", "on"):
            r.online = cmd == "on"
            print(f"{r.name}: {'BẬT' if r.online else 'TẮT (không trả lời SNMP)'}")
        else:
            print("Lệnh không hợp lệ. Gõ help để xem lệnh.")


def main():
    routers = {r.name: r for r in (Router("R1", 1161, 8, 32), Router("R2", 1162, 12, 38), Router("R3", 1163, 6, 30))}
    for r in routers.values():
        threading.Thread(target=serve, args=(r,), daemon=True).start()
    print(f"Đang giả lập {', '.join(routers)} trên {HOST}, cổng 1161-1163, community '{COMMUNITY}'.")
    print("Mở terminal khác và chạy: python web.py config_routers.yaml\n")
    print(HELP)
    while True:
        try:
            run_command(routers, input("\nrouter-sim> "))
        except (EOFError, KeyboardInterrupt, SystemExit):
            print("\nĐã thoát.")
            break
        except (IndexError, ValueError):
            print("Sai cú pháp. Gõ help để xem ví dụ.")


if __name__ == "__main__":
    main()
