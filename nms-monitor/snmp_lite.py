"""SNMP v2c tối giản (GET / GETNEXT) viết bằng Python thuần, không cần cài thêm thư viện.
Dùng chung cho client (snmp_utils.py) và router giả lập (router_sim.py)."""
import random
import socket
import time

# ---------- mã hóa BER ----------
NO_SUCH_INSTANCE = b"\x81\x00"
END_OF_MIB_VIEW = b"\x82\x00"


def enc_len(n):
    if n < 128:
        return bytes([n])
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(raw)]) + raw


def tlv(tag, content):
    return bytes([tag]) + enc_len(len(content)) + content


def enc_int(value, tag=0x02):
    size = 1
    while True:
        try:
            return tlv(tag, value.to_bytes(size, "big", signed=True))
        except OverflowError:
            size += 1


def enc_gauge(value):
    return enc_int(int(value), 0x42)


def enc_octets(text):
    return tlv(0x04, text.encode("utf-8"))


def enc_oid(oid):
    body = bytearray([40 * oid[0] + oid[1]])
    for x in oid[2:]:
        chunk = [x & 0x7F]
        x >>= 7
        while x:
            chunk.append(0x80 | (x & 0x7F))
            x >>= 7
        body += bytes(reversed(chunk))
    return tlv(0x06, bytes(body))


# ---------- giải mã BER ----------
def read_tlv(data, pos):
    tag = data[pos]
    length = data[pos + 1]
    pos += 2
    if length & 0x80:
        k = length & 0x7F
        length = int.from_bytes(data[pos:pos + k], "big")
        pos += k
    end = pos + length
    if end > len(data):
        raise ValueError("gói tin bị cắt")
    return tag, data[pos:end], end


def children(content):
    pos, out = 0, []
    while pos < len(content):
        tag, val, pos = read_tlv(content, pos)
        out.append((tag, val))
    return out


def dec_int(raw):
    return int.from_bytes(raw, "big", signed=True) if raw else 0


def dec_oid(raw):
    first = raw[0]
    out = [2, first - 80] if first >= 80 else [first // 40, first % 40]
    value = 0
    for b in raw[1:]:
        value = (value << 7) | (b & 0x7F)
        if not b & 0x80:
            out.append(value)
            value = 0
    return tuple(out)


def value_to_str(tag, raw):
    """Đổi giá trị SNMP sang chuỗi. Trả None nếu không có giá trị (NULL, noSuchObject...)."""
    if tag == 0x02:
        return str(dec_int(raw))
    if tag in (0x41, 0x42, 0x43, 0x46):          # Counter32, Gauge32, TimeTicks, Counter64
        return str(int.from_bytes(raw, "big"))
    if tag == 0x04:
        return raw.decode("utf-8", "ignore")
    if tag == 0x40:
        return ".".join(str(b) for b in raw)
    if tag == 0x06:
        return ".".join(str(n) for n in dec_oid(raw))
    return None


def parse_oid(text):
    return tuple(int(x) for x in text.strip(".").split("."))


# ---------- gói tin ----------
def build_request(community, oid, req_id, pdu_tag=0xA0, version=1):
    varbind = tlv(0x30, enc_oid(oid) + b"\x05\x00")
    pdu = tlv(pdu_tag, enc_int(req_id) + enc_int(0) + enc_int(0) + tlv(0x30, varbind))
    return tlv(0x30, enc_int(version) + tlv(0x04, community.encode()) + pdu)


def build_response(community, req_id, varbinds, version=1):
    """varbinds: danh sách (oid_tuple, giá trị đã mã hóa BER)."""
    body = b"".join(tlv(0x30, enc_oid(o) + v) for o, v in varbinds)
    pdu = tlv(0xA2, enc_int(req_id) + enc_int(0) + enc_int(0) + tlv(0x30, body))
    return tlv(0x30, enc_int(version) + tlv(0x04, community.encode()) + pdu)


def parse_message(data):
    tag, body, _ = read_tlv(data, 0)
    if tag != 0x30:
        raise ValueError("không phải gói SNMP")
    parts = children(body)
    pdu_tag, pdu = parts[2]
    p = children(pdu)
    varbinds = []
    for _, vb in children(p[3][1]):
        oid_part, val_part = children(vb)[:2]
        varbinds.append((dec_oid(oid_part[1]), val_part[0], val_part[1]))
    return {
        "version": dec_int(parts[0][1]),
        "community": parts[1][1].decode("utf-8", "ignore"),
        "pdu_tag": pdu_tag,
        "req_id": dec_int(p[0][1]),
        "err_status": dec_int(p[1][1]),
        "varbinds": varbinds,
    }


# ---------- client ----------
def snmp_get(ip, community, oid, timeout=2, retries=1, port=161):
    """Trả về chuỗi giá trị, hoặc None nếu lỗi / không có OID / thiết bị không trả lời."""
    try:
        oid_t = parse_oid(oid)
        req_id = random.randint(1, 0x7FFFFFFF)
        packet = build_request(community, oid_t, req_id)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            for _ in range(retries + 1):
                s.sendto(packet, (ip, port))
                deadline = time.time() + timeout
                while True:
                    remaining = deadline - time.time()
                    if remaining <= 0:
                        break
                    s.settimeout(remaining)
                    try:
                        data, _ = s.recvfrom(65535)
                    except OSError:              # hết giờ, hoặc Windows báo cổng đóng
                        break
                    try:
                        msg = parse_message(data)
                    except Exception:
                        continue
                    if msg["req_id"] != req_id:
                        continue
                    if msg["err_status"] or not msg["varbinds"]:
                        return None
                    _, tag, raw = msg["varbinds"][0]
                    return value_to_str(tag, raw)
    except Exception:
        return None
    return None
