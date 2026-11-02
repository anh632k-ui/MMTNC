"""Báo cáo HTML ngoại tuyến cho NMS Monitor V2.

Chỉ sử dụng dữ liệu thực có trong /api/metrics; biểu đồ SVG được nhúng trực
 tiếp để file HTML tải về vẫn xem/in được khi không có Internet.
"""
from __future__ import annotations

import html
import math
from datetime import datetime
from typing import Any

PALETTE = ("#2563eb", "#0d9488", "#7c3aed", "#d97706", "#db2777", "#0891b2", "#4d7c0f", "#be123c")
METRICS = (
    ("cpu", "CPU theo thời gian", "%", 100.0, "CPU đo được trên từng thiết bị; router không hỗ trợ OID sẽ không có đường"),
    ("ram", "RAM theo thời gian", "%", 100.0, "Dùng tỷ lệ RAM do Collector / SNMP trả về"),
    ("rtt_ms", "RTT / độ trễ ICMP", "ms", None, "Mỗi mẫu RTT là kết quả phép đo ICMP; đây không phải độ trễ liên tục"),
    ("rx_kbps", "Network I/O — Received", "KB/s", None, "Tốc độ nhận từ các interface được theo dõi"),
    ("tx_kbps", "Network I/O — Sent", "KB/s", None, "Tốc độ gửi từ các interface được theo dõi"),
    ("packet_loss", "Mất gói tại lần đo", "%", 100.0, "Một gói ICMP mỗi lần; 0% hoặc 100% chỉ phản ánh mẫu hiện tại"),
)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def numeric(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        num = float(value)
    except (ValueError, TypeError):
        return None
    return num if math.isfinite(num) else None


def timesec(item: dict, fallback: int) -> float:
    raw = item.get("time")
    if raw:
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
        except (ValueError, OverflowError, OSError):
            pass
    return float(fallback)


def hhmm(raw: Any) -> str:
    if not raw:
        return "—"
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).strftime("%H:%M")
    except ValueError:
        return str(raw)[-8:-3]


def status_problem(metrics: dict, thresholds: dict) -> bool:
    if not metrics.get("reachable"):
        return True
    for key in ("cpu", "ram", "temp"):
        val, threshold = numeric(metrics.get(key)), numeric(thresholds.get(key))
        if val is not None and threshold is not None and val > threshold:
            return True
    return any(v == "down" for v in (metrics.get("ifaces") or {}).values())


def name_order(name: str) -> tuple:
    upper = name.upper()
    if upper.startswith("DESKTOP") or upper.startswith("WINDOWS"):
        return (0, upper)
    if "UBUNTU" in upper:
        return (1, upper)
    if len(upper) <= 3 and upper.startswith("R") and upper[1:].isdigit():
        return (2, int(upper[1:]))
    return (3, upper)


def svg_chart(data: dict, key: str, title: str, unit: str, bound: float | None, description: str, colors: dict) -> str:
    series_map = data.get("series") or {}
    W, H = 690, 255
    left, right, top, bottom = 51, 18, 21, 36
    iw, ih = W-left-right, H-top-bottom
    all_lines = []
    values = []
    for name in sorted(series_map, key=name_order):
        records = series_map.get(name) or []
        pts = [(timesec(item,i), numeric(item.get(key))) for i,item in enumerate(records) if isinstance(item,dict)]
        good = [(t,v) for t,v in pts if v is not None]
        if good:
            all_lines.append((name, good))
            values.extend(v for _,v in good)
    if not all_lines:
        return f'''<article class="chart-card"><div class="chart-top"><h3>{esc(title)}</h3><span>{esc(unit)}</span></div>
          <div class="empty-chart">Không có mẫu đo {esc(title.lower())} trong khoảng lịch sử hiện có.</div>
          <p class="chart-note">{esc(description)}</p></article>'''
    xvalues = [x for _,line in all_lines for x,_ in line]
    x0, x1 = min(xvalues), max(xvalues)
    if x1 <= x0: x1 = x0+1
    ymax = float(bound) if bound else max(1.0,max(values)*1.12)
    if bound is None:
        magnitude = 10**math.floor(math.log10(ymax))
        step = magnitude*(0.2 if ymax/magnitude<=2 else 0.5 if ymax/magnitude<=5 else 1)
        ymax = math.ceil(ymax/step)*step
    defs = []
    defs.append('<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="'+esc(title)+'" viewBox="0 0 690 255" class="plot">')
    defs.append('<rect width="690" height="255" rx="8" fill="#ffffff"/>')
    for step in range(5):
        y = top + ih*step/4
        value = ymax*(4-step)/4
        fmt = f"{value:.0f}" if bound else f"{value:.1f}" if ymax < 20 else f"{value:.0f}"
        defs.append(f'<line x1="{left}" y1="{y:.1f}" x2="{W-right}" y2="{y:.1f}" stroke="#e4eaf2" stroke-width="1"/>')
        defs.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="12" fill="#62748c">{fmt}</text>')
    for frac in (0,.25,.5,.75,1):
        x = left+frac*iw
        stamp = x0+(x1-x0)*frac
        label = datetime.fromtimestamp(stamp).strftime('%H:%M:%S') if x0 > 1000000000 else f'{frac*100:.0f}%'
        defs.append(f'<text x="{x:.1f}" y="{H-11}" text-anchor="middle" font-size="11" fill="#70829b">{label}</text>')
    for name, line in all_lines:
        coords = [(left+(t-x0)/(x1-x0)*iw, top+ih-max(0,min(ymax,v))/ymax*ih) for t,v in line]
        color = colors[name]
        if len(coords)>1:
            points = ' '.join(f'{x:.1f},{y:.1f}' for x,y in coords)
            defs.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.7" stroke-linejoin="round" stroke-linecap="round" points="{points}"/>')
        for x,y in (coords if len(coords)==1 else coords[-1:]):
            defs.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.7" fill="{color}" stroke="#ffffff" stroke-width="1.2"/>')
    defs.append('</svg>')
    legend = ''.join(f'<span class="legend-item"><i style="background:{colors[name]}"></i>{esc(name)}</span>' for name,_ in all_lines)
    n_samples = max(len(line) for _,line in all_lines)
    return f'''<article class="chart-card"><div class="chart-top"><h3>{esc(title)}</h3><span>{esc(unit)} · tối đa {n_samples} mẫu / thiết bị</span></div>
     {''.join(defs)}<div class="legend">{legend}</div><p class="chart-note">{esc(description)}</p></article>'''


def fmt_metric(value, unit="", digits=1):
    n = numeric(value)
    return f'{n:,.{digits}f}{unit}' if n is not None else '—'


def device_table(data:dict, colors:dict) -> str:
    th = data.get('thresholds') or {}
    result = []
    for name, m in sorted((data.get('devices') or {}).items(),key=lambda item:name_order(item[0])):
        reachable = bool(m.get('reachable'))
        status = 'Mất kết nối' if not reachable else 'Cảnh báo' if status_problem(m,th) else 'Hoạt động'
        cls = 'offline' if not reachable else 'warning' if status == 'Cảnh báo' else 'online'
        interfaces = m.get('ifaces') or {}
        iface_text = ', '.join(f'{k}: {v}' for k,v in interfaces.items()) or '—'
        mark=f'<i class="name-dot" style="background:{colors.get(name,"#2563eb")}"></i>'
        row = (f'<tr><td class="name-cell">{mark}{esc(name)}<small>{"ICMP" if m.get("kind")=="ping" else "SNMP / Local"}</small></td>',
               f'<td><span class="status {cls}">{status}</span></td>',
               f'<td>{esc(fmt_metric(m.get("cpu"),"%"))}</td>',
               f'<td>{esc(fmt_metric(m.get("ram"),"%"))}</td>',
               f'<td>{esc(fmt_metric(m.get("rtt_ms")," ms"))}</td>',
               f'<td>{esc(fmt_metric(m.get("rx_kbps")," KB/s"))}</td>',
               f'<td>{esc(fmt_metric(m.get("tx_kbps")," KB/s"))}</td>',
               f'<td class="iface-cell">{esc(iface_text)}</td></tr>')
        result.append(''.join(row))
    return ''.join(result) if result else '<tr><td colspan="8" class="empty-td">Chưa có thiết bị nào được thu thập.</td></tr>'



def service_table(data: dict) -> str:
    rows = []
    for s in (data.get("services") or {}).values():
        status = "Hoạt động" if s.get("ok") else "Cảnh báo"
        klass = "online" if s.get("ok") else "warning"
        code = str(s["status_code"]) if s.get("status_code") is not None else "—"
        ms = fmt_metric(s.get("response_ms"), " ms")
        rows.append('<tr>'
            f'<td>{esc(s.get("name", ""))}</td>'
            f'<td>{esc(str(s.get("kind", "")).upper())}</td>'
            f'<td>{esc(s.get("endpoint", ""))}</td>'
            f'<td><span class="status {klass}">{status}</span></td>'
            f'<td>{esc(code)}</td><td>{esc(ms)}</td>'
            f'<td>{esc(s.get("reason", ""))}</td></tr>')
    return ''.join(rows) if rows else '<tr><td colspan="7" class="empty-td">Chưa có dịch vụ HTTP/TCP được cấu hình.</td></tr>'


def alert_table(data:dict) -> str:
    result=[]
    for item in (data.get('alerts') or [])[:60]:
        level=item.get('level')
        shown='Khôi phục' if level=='recovered' else 'Cảnh báo' if level=='warning' else level or 'Sự kiện'
        color='online' if level=='recovered' else 'warning'
        result.append('<tr>'
            f'<td>{esc(str(item.get("time","" )).replace("T"," "))}</td>'
            f'<td>{esc(item.get("device",""))}</td>'
            f'<td><span class="status {color}">{esc(shown)}</span></td>'
            f'<td>{esc(item.get("message",""))}</td></tr>')
    return ''.join(result) if result else '<tr><td colspan="4" class="empty-td">Chưa có cảnh báo nào được ghi vào nhật ký NMS. Cảnh báo gửi trước khi có nms_alerts.jsonl không tự xuất hiện tại đây.</td></tr>'


def make_report(data: dict) -> str:
    """Sinh HTML hoàn toàn tự chứa: không JS bên ngoài, không phụ thuộc Chart.js/CDN."""
    if data.get('error'):
        return '<!doctype html><meta charset="utf-8"><h1>Không thể tạo báo cáo</h1><p>'+esc(data['error'])+'</p>'
    devices = data.get('devices') or {}
    alerts = data.get('alerts') or []
    services = data.get('services') or {}
    thresholds = data.get('thresholds') or {}
    names = sorted(set(devices) | set(data.get('series') or {}), key=name_order)
    colors={name:PALETTE[i%len(PALETTE)] for i,name in enumerate(names)}
    online=sum(bool(m.get('reachable')) for m in devices.values())
    offline=len(devices)-online
    warning=sum(bool(m.get('reachable')) and status_problem(m,thresholds) for m in devices.values())
    generated = data.get('generated_at') or datetime.now().isoformat(timespec='seconds')
    try: report_stamp = datetime.fromisoformat(str(generated)).strftime('%d/%m/%Y %H:%M:%S')
    except ValueError: report_stamp = str(generated).replace('T',' ')
    sample_count = sum(len(v or []) for v in (data.get('series') or {}).values())
    all_times = [str(s.get('time')) for ser in (data.get('series') or {}).values() for s in ser if s.get('time')]
    duration = (f'{hhmm(min(all_times))} – {hhmm(max(all_times))}' if all_times else 'Chưa có lịch sử')
    charts=''.join(svg_chart(data,*metric,colors) for metric in METRICS)
    style=r'''
:root{--ink:#17283e;--slate:#60738e;--line:#dce5ef;--blue:#0c67aa;--pale:#f3f7fb}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:#eaf0f6;color:var(--ink);font:14px/1.48 "Segoe UI",Arial,sans-serif}
.report{max-width:1220px;margin:28px auto 65px;background:white;box-shadow:0 18px 50px #1c36552b}
.masthead{color:white;background:linear-gradient(115deg,#0b213e,#144a76 70%,#166b91);padding:31px 40px 35px}
.eyebrow{font-size:11px;font-weight:800;letter-spacing:2.7px;color:#8ddcff}
h1{font-size:30px;margin:10px 0 12px;line-height:1.12;letter-spacing:-.4px}
.masthead p{color:#d3e6f5;max-width:720px;margin:0}.byline{margin-top:17px;font-size:12px;color:#d1e6fa}
.content{padding:28px 40px 35px}.chapter{margin:26px 0 15px;display:flex;align-items:center;gap:13px}
.chapter .no{display:grid;place-items:center;min-width:32px;height:32px;background:#e7f4ff;color:#0969a6;font-weight:800;border-radius:8px}
h2{font-size:20px;line-height:1.3;margin:0;letter-spacing:-.2px}h3{font-size:15px;margin:0}
.subtitle{font-size:13px;color:var(--slate);margin:0 0 13px}.ribbon{background:#f1f7fc;border:1px solid #d9e9f8;border-radius:12px;padding:13px 17px;display:flex;gap:24px;flex-wrap:wrap;color:#365371}
.ribbon strong{color:#093a67}.kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-top:19px}
.kpi{border:1px solid var(--line);border-radius:12px;padding:18px 16px;background:#fff;position:relative;overflow:hidden}
.kpi:before{position:absolute;content:"";height:4px;top:0;left:0;right:0;background:var(--accent,#0c67aa)}
.kpi b{display:block;font-size:30px;line-height:1.1;color:#12365c;margin:5px 0}.kpi span{font-size:12px;color:#677a92}
.charts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.chart-card{border:1px solid var(--line);border-radius:12px;padding:17px;background:white;min-width:0;break-inside:avoid;page-break-inside:avoid}
.chart-top{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:9px}
.chart-top span{font-size:11px;color:#788ba0;text-align:right}.plot{width:100%;height:auto;display:block}
.legend{display:flex;flex-wrap:wrap;gap:8px 15px;margin:8px 0 2px}.legend-item{font-size:11px;color:#425977;display:inline-flex;align-items:center;gap:6px}
.legend-item i{height:9px;width:9px;display:inline-block;border-radius:50%}.chart-note{font-size:11px;color:#7b8da0;margin:8px 0 0}
.empty-chart{height:244px;display:grid;place-items:center;color:#8898a9;text-align:center;padding:16px;border:1px dashed #dbe5ef;border-radius:8px}
.table-wrap{border:1px solid var(--line);border-radius:10px;overflow:hidden}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px}
th{background:#edf4fb;color:#385574;text-align:left;text-transform:uppercase;letter-spacing:.45px;font-size:10px}
th,td{padding:10px 9px;border-bottom:1px solid #e1e8ef;vertical-align:middle;overflow-wrap:anywhere}
tr:nth-child(even){background:#fbfdff}tbody tr:last-child td{border-bottom:0}
.name-cell{font-weight:700}.name-cell small{display:block;color:#8291a3;font-size:10px;margin-left:13px;font-weight:400}.name-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px}
.status{font-size:10px;font-weight:750;display:inline-block;border-radius:6px;padding:4px 7px;white-space:nowrap}
.status.online{background:#e5f8ee;color:#13744a}.status.warning{background:#fff2d6;color:#a9650e}.status.offline{background:#ffebef;color:#a6223d}
.iface-cell{font-size:10.5px;color:#586d83}.empty-td{text-align:center;color:#7c8da4;padding:23px!important}
.note{background:#f7fafd;border-left:4px solid #2899cf;color:#4b6179;font-size:12px;padding:13px 16px;margin-top:14px;border-radius:0 9px 9px 0}
footer{padding:15px 40px;border-top:1px solid var(--line);color:#7c8fa6;font-size:11px;display:flex;justify-content:space-between;gap:12px}
.actions{padding:10px 0;color:#3e658c;font-size:12px}.actions button{cursor:pointer;background:#0f6fa8;color:white;border:0;border-radius:8px;padding:9px 15px}
@media(max-width:820px){.report{margin:0}.content{padding:20px}.masthead{padding:25px}.kpis{grid-template-columns:repeat(2,1fr)}.charts{grid-template-columns:1fr}.table-wrap{overflow:auto}table{min-width:800px}footer{padding:14px 20px}}
@media print{@page{size:A4 landscape;margin:12mm}body{background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}.report{max-width:none;margin:0;box-shadow:none}.masthead{padding:19px 26px}.content{padding:10px 26px}.kpi{padding:12px}.kpi b{font-size:23px}.charts{gap:10px}.chart-card{padding:10px}.chapter{margin-top:18px}h1{font-size:25px}.plot{max-height:190px}tr{break-inside:avoid}.chart-card{break-inside:avoid}thead{display:table-header-group}footer{padding:10px 26px}.actions{display:none}}
'''
    return ('''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Báo cáo NMS Monitor | Biểu đồ giám sát</title><style>'''+style+'''</style></head><body><div class="report">
<header class="masthead"><div class="eyebrow">NMS MONITOR · NETWORK OPERATIONS</div>
<h1>BÁO CÁO GIÁM SÁT HỆ THỐNG</h1><p>Trạng thái thiết bị, chỉ số hiệu suất, độ trễ mạng, lưu lượng và lịch sử cảnh báo từ hệ thống NMS Monitor.</p>
<div class="byline">Xuất báo cáo: '''+esc(report_stamp)+''' · Nguồn SNMP / ICMP / HTTP / TCP / Windows Local</div></header>
<div class="content"><div class="actions"><button onclick="window.print()">In / Lưu PDF</button> · Báo cáo HTML hoạt động ngoại tuyến; biểu đồ được nhúng trực tiếp.</div>
<div class="chapter"><span class="no">01</span><h2>Tổng quan hệ thống</h2></div>
<div class="ribbon"><span>Ngưỡng CPU: <strong>'''+esc(thresholds.get('cpu','—'))+'''%</strong></span><span>Ngưỡng RAM: <strong>'''+esc(thresholds.get('ram','—'))+'''%</strong></span><span>Chu kỳ lấy mẫu: <strong>'''+esc(data.get('interval','—'))+''' giây</strong></span><span>Lịch sử biểu đồ: <strong>'''+esc(duration)+'''</strong></span></div>
<div class="kpis">'''+''.join(f'<div class="kpi" style="--accent:{accent}"><span>{label}</span><b>{value}</b></div>' for label,value,accent in (
    ('Tổng thiết bị',len(devices),'#2563eb'),('Đang hoạt động',online,'#10b981'),('Cảnh báo',warning,'#f59e0b'),('Mất kết nối',offline,'#ef476f'),('Sự kiện đã ghi',len(alerts),'#8b5cf6'))) +'''</div>
<div class="chapter"><span class="no">02</span><h2>Biểu đồ giám sát theo thời gian</h2></div>
<p class="subtitle">Dữ liệu lấy từ lịch sử do NMS thu thập. Mỗi đường màu đại diện cho một thiết bị; chỉ vẽ khi thiết bị có mẫu hợp lệ.</p>
<div class="charts">'''+charts+'''</div>
<div class="chapter"><span class="no">03</span><h2>Trạng thái và chỉ số tại thời điểm xuất</h2></div>
<div class="table-wrap"><table><colgroup><col style="width:13%"><col style="width:11%"><col style="width:8%"><col style="width:8%"><col style="width:9%"><col style="width:10%"><col style="width:10%"><col style="width:31%"></colgroup>
<thead><tr><th>Thiết bị</th><th>Trạng thái</th><th>CPU</th><th>RAM</th><th>RTT</th><th>RX</th><th>TX</th><th>Interface</th></tr></thead><tbody>'''+device_table(data,colors)+'''</tbody></table></div>
<div class="chapter"><span class="no">04</span><h2>Giám sát dịch vụ HTTP / TCP</h2></div>
<p class="subtitle">Lab 4 kiểm tra mã phản hồi và độ trễ HTTP; Lab 5 kiểm tra khả năng kết nối của các cổng TCP đã khai báo.</p>
<div class="ribbon"><span>Dịch vụ được theo dõi: <strong>'''+str(len(services))+'''</strong></span><span>Hoạt động: <strong>'''+str(sum(bool(s.get("ok")) for s in services.values()))+'''</strong></span><span>Có sự cố: <strong>'''+str(sum(not s.get("ok") for s in services.values()))+'''</strong></span></div>
<div class="table-wrap" style="margin-top:14px"><table><thead><tr><th>Dịch vụ</th><th>Loại</th><th>Đích</th><th>Trạng thái</th><th>HTTP</th><th>Độ trễ</th><th>Ghi chú</th></tr></thead><tbody>'''+service_table(data)+'''</tbody></table></div>
<div class="chapter"><span class="no">05</span><h2>Lịch sử cảnh báo và khôi phục</h2></div>
<p class="subtitle">Các sự kiện được ghi trong phiên bản NMS có nhật ký cảnh báo; tối đa 60 sự kiện gần nhất trong báo cáo này.</p>
<div class="table-wrap"><table><colgroup><col style="width:19%"><col style="width:18%"><col style="width:13%"><col style="width:50%"></colgroup>
<thead><tr><th>Thời gian</th><th>Thiết bị</th><th>Loại</th><th>Nội dung</th></tr></thead><tbody>'''+alert_table(data)+'''</tbody></table></div>
<div class="note"><strong>Ghi chú:</strong> Biểu đồ sử dụng tối đa 120 mẫu gần nhất mỗi thiết bị do API cung cấp. Dấu “—” nghĩa là không có số liệu, không phải 0. RTT và tỷ lệ mất gói chỉ đại diện cho các lần đo ICMP đã thực hiện; không sử dụng làm bằng chứng SLA dài hạn. Các ngưỡng là cấu hình tại thời điểm xuất.</div>
</div><footer><span>NMS Monitor · Báo cáo từ dữ liệu giám sát thật · HTML tự chứa</span><span>'''+esc(report_stamp)+'''</span></footer></div></body></html>''')
