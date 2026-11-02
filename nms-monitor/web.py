"""Dashboard V2 cho NMS Monitor.

    python web.py --host 127.0.0.1 --port 5055
    python web.py config_routers.yaml
    python web.py --source http://IP:5055  # Dashboard đọc từ máy chủ khác

Không thay thế collector.py, notifier.py hay snmp_utils.py.
"""

import argparse
import csv
import html
import io
import re
import sys
import threading
from datetime import datetime

import requests
from flask import Flask, Response, jsonify, render_template_string

import monitor
from nms_report import make_report

app = Flask(__name__)
CFG = None
SOURCE = None

PAGE = r"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NMS Monitor V2 | Network Operations Center</title>
<style>
:root{color-scheme:dark;--bg:#0a1121;--panel:#141f33;--panel2:#19263e;--line:#293852;--txt:#e9f1ff;--muted:#91a3bd;--blue:#44b8ff;--green:#37dab0;--amber:#ffca77;--red:#ff7188;--violet:#a994ff}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:14px/1.5 system-ui,"Segoe UI",sans-serif;color:var(--txt);background:radial-gradient(circle at 85% -10%,#122c4a 0%,transparent 30%),var(--bg)}
a{color:inherit;text-decoration:none}button,select{font:inherit}button{cursor:pointer}
.layout{display:grid;grid-template-columns:238px minmax(0,1fr);min-height:100vh}
aside{border-right:1px solid var(--line);background:#10192b;position:sticky;top:0;height:100vh;padding:26px 16px;display:flex;flex-direction:column}
.brand{display:flex;gap:11px;align-items:center;padding:4px 8px 30px}.brandlogo{display:grid;place-items:center;width:38px;height:38px;border-radius:12px;background:linear-gradient(145deg,#39acff,#6559ff);font-size:20px;box-shadow:0 8px 24px #1875ff40}
.brand b{font-size:19px;letter-spacing:.3px}.brand small{display:block;color:var(--muted);font-size:10px;letter-spacing:2px}
.nav-label{color:#627b9d;font-size:10px;letter-spacing:2px;padding:8px 12px 10px;font-weight:700}
.nav{display:flex;flex-direction:column;gap:6px}.nav a{border-radius:10px;padding:11px 13px;color:#a7bbd4;display:flex;gap:12px;align-items:center}
.nav a:hover,.nav a.active{background:#19314d;color:#bde7ff}.nav a.active{border-left:3px solid var(--blue)}
.aside-bottom{margin-top:auto;padding:12px;border:1px solid var(--line);background:#17243a;border-radius:12px;color:var(--muted);font-size:12px}
.live-dot{display:inline-block;width:9px;height:9px;background:var(--green);border-radius:50%;box-shadow:0 0 0 4px #37dab01d;vertical-align:middle;margin-right:7px}
main{padding:28px clamp(18px,3vw,44px) 50px;min-width:0;max-width:1800px;width:100%}
.top{display:flex;gap:16px;align-items:center;justify-content:space-between;margin-bottom:25px;flex-wrap:wrap}
.kicker{font-weight:700;color:var(--blue);font-size:11px;letter-spacing:2.4px;text-transform:uppercase}
h1{font-size:clamp(24px,3vw,32px);line-height:1.2;margin:5px 0 8px;letter-spacing:-1px}h2{font-size:17px;margin:0;letter-spacing:-.2px}
.muted{color:var(--muted)}.tiny{font-size:12px}.top-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;color:#dceafd;padding:10px 14px;border-radius:10px;border:1px solid #314764;background:#1c2c44;transition:.2s}
.btn:hover{border-color:var(--blue);transform:translateY(-1px)}.btn.primary{background:#066ca9;border-color:#168ac6;color:white}
.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin-bottom:20px}
.card,.panel{background:linear-gradient(180deg,#17243a 0%,#142034 100%);border:1px solid var(--line);border-radius:16px;box-shadow:0 9px 24px #00000016}
.card{padding:18px 20px}.card .label{color:var(--muted);font-size:12px}.card .num{font-size:32px;line-height:1.2;font-weight:750;letter-spacing:-1px;margin:12px 0 6px}
.card .foot{font-size:12px;color:var(--muted)}.card .corner{float:right;color:var(--blue);font-size:20px}.num.green{color:var(--green)}.num.red{color:var(--red)}
.section-head{display:flex;align-items:center;justify-content:space-between;gap:14px;margin:25px 1px 13px;flex-wrap:wrap}
.section-head .hint{font-size:12px;color:var(--muted)}.select-wrap{display:flex;gap:8px;align-items:center;color:var(--muted);font-size:12px}
select{background:#1a2c44;color:var(--txt);border:1px solid #38506d;padding:9px 12px;border-radius:9px;max-width:220px;outline:none}
.charts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}.panel{padding:18px;min-width:0}
.chart-header{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:13px}
.chart-header b{font-size:14px}.chart-header small{color:var(--muted);font-size:11px}
.legend{display:flex;gap:14px;font-size:11px;color:var(--muted);margin-top:5px;flex-wrap:wrap}.swatch{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:6px}
canvas{display:block;width:100%;height:185px}.panel-note{margin:10px 0 0;color:var(--muted);font-size:11px}
.table-wrap{overflow:auto}.grid-table{width:100%;border-collapse:collapse;min-width:850px}.services-table{min-width:780px}.services-table td{overflow-wrap:anywhere}
.grid-table th{text-align:left;padding:12px 15px;color:#91a3bd;font-weight:600;font-size:11px;border-bottom:1px solid var(--line);text-transform:uppercase;letter-spacing:.8px}
.grid-table td{padding:14px 15px;border-bottom:1px solid #263650;font-size:13px;vertical-align:middle}
.grid-table tr:last-child td{border-bottom:none}.grid-table tbody tr{cursor:pointer}.grid-table tbody tr:hover{background:#1a2c45}.grid-table tbody tr.selected{background:#163653}
.devname{font-weight:650}.devsub{font-size:11px;color:var(--muted);margin-top:4px}.badge{display:inline-flex;align-items:center;gap:6px;border-radius:100px;padding:5px 10px;font-size:11px;font-weight:650;background:#1b453d;color:#5bebc3;white-space:nowrap}
.badge.bad{background:#50283a;color:#ff93a0}.badge.warn{background:#493d28;color:#ffdb86}
.dot{width:6px;height:6px;border-radius:50%;background:currentColor;display:inline-block}.plain{color:var(--muted)}
.track{height:5px;border-radius:5px;background:#293a51;min-width:54px;max-width:112px;overflow:hidden;margin-top:6px}.track>i{display:block;height:100%;border-radius:5px;background:var(--blue)}.track>i.high{background:var(--red)}
.ifaces{display:flex;gap:4px;flex-wrap:wrap;max-width:300px}.iface{border:1px solid #386052;color:#79dcb5;padding:3px 7px;border-radius:6px;font-size:10px}.iface.down{border-color:#984254;color:var(--red)}.iface.unknown{border-color:#716443;color:var(--amber)}
.alerts{display:flex;flex-direction:column;gap:10px;max-height:350px;overflow-y:auto}.alert{padding:12px;border:1px solid #34435b;background:#18283f;border-left:3px solid var(--amber);border-radius:9px;display:grid;grid-template-columns:1fr auto;gap:8px}
.alert.recovered{border-left-color:var(--green)}.alert strong{font-size:13px}.alert p{margin:4px 0 0;color:#b6c8da;white-space:pre-wrap;font-size:12px}.alert time{white-space:nowrap;color:var(--muted);font-size:11px}
.footer{text-align:center;color:#7085a5;font-size:11px;padding-top:30px}#error{display:none;color:#ffb3c0;border:1px solid #9a4d61;background:#502737;padding:11px 15px;border-radius:10px;margin:15px 0}
@media(max-width:1150px){.layout{grid-template-columns:75px 1fr}.brand b,.brand small,.nav span,.nav-label,.aside-bottom{display:none}.brand{padding:6px 0 30px;justify-content:center}.nav a{justify-content:center;font-size:19px}}
@media(max-width:800px){.layout{display:block}aside{position:static;height:auto;display:block;padding:10px 14px}.brand{padding:0}.brand b{display:block}.brand small{display:block}.nav,.nav-label,.aside-bottom{display:none}main{padding:20px 12px}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.charts{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="layout">
<aside>
  <div class="brand"><div class="brandlogo">◈</div><div><b>NMS Monitor</b><small>NETWORK OPERATIONS</small></div></div>
  <div class="nav-label">TRUNG TÂM GIÁM SÁT</div>
  <nav class="nav">
    <a class="active" href="#overview">◉ <span>Tổng quan</span></a>
    <a href="#charts">▥ <span>Biểu đồ hiệu suất</span></a>
    <a href="#devices">▤ <span>Danh sách thiết bị</span></a>
    <a href="#services">◈ <span>Dịch vụ HTTP/TCP</span></a>
    <a href="#alerts">♢ <span>Lịch sử cảnh báo</span></a>
  </nav>
  <div class="aside-bottom"><span class="live-dot"></span><b>Monitoring Active</b><div style="margin-top:8px">SNMP · ICMP · HTTP · TCP · Telegram</div><div style="margin-top:5px">Lấy dữ liệu từ API nội bộ</div></div>
</aside>
<main id="overview">
  <div class="top">
    <div><div class="kicker">NETWORK MANAGEMENT SYSTEM</div><h1>Dashboard giám sát mạng</h1><div class="muted tiny" id="updated">Đang tải dữ liệu hệ thống…</div></div>
    <div class="top-actions">
      <a class="btn" id="telegram" href="https://t.me/bta0004bot" target="_blank" rel="noopener noreferrer">✈ Mở Telegram</a>
      <a class="btn" href="/report/download">⇩ Xuất báo cáo HTML</a>
      <button class="btn primary" id="refresh">↻ Làm mới</button>
    </div>
  </div>
  <div id="error" role="alert"></div>
  <section class="cards" aria-label="Tóm tắt trạng thái">
    <div class="card"><span class="corner">▥</span><div class="label">Tổng thiết bị</div><div class="num" id="count-total">—</div><div class="foot">Đang theo dõi</div></div>
    <div class="card"><span class="corner" style="color:var(--green)">●</span><div class="label">Đang hoạt động</div><div class="num green" id="count-online">—</div><div class="foot">Đã phản hồi</div></div>
    <div class="card"><span class="corner" style="color:var(--red)">⚑</span><div class="label">Thiết bị cảnh báo</div><div class="num red" id="count-alert">—</div><div class="foot">Offline / vượt ngưỡng / interface DOWN</div></div>
    <div class="card"><span class="corner">◷</span><div class="label">Chu kỳ giám sát</div><div class="num" id="interval">—</div><div class="foot">Dashboard làm mới 5 giây</div></div>
  </section>
  <div class="section-head" id="charts"><div><h2>Biểu đồ hiệu suất</h2><div class="hint">Mỗi điểm là số đo thật; lịch sử lưu tối đa 120 mẫu / thiết bị</div></div><label class="select-wrap">Thiết bị <select id="device-select"><option>Đang tải…</option></select></label></div>
  <div class="charts">
    <section class="panel"><div class="chart-header"><b>CPU Usage (%)</b><small id="cpu-last">—</small></div><canvas id="chart-cpu" aria-label="Biểu đồ CPU" role="img"></canvas><div class="legend"><span><i class="swatch" style="background:var(--blue)"></i>CPU</span><span class="muted">Ngưỡng cảnh báo: <b id="cpu-th">—</b>%</span></div></section>
    <section class="panel"><div class="chart-header"><b>RAM Usage (%)</b><small id="ram-last">—</small></div><canvas id="chart-ram" aria-label="Biểu đồ RAM" role="img"></canvas><div class="legend"><span><i class="swatch" style="background:var(--green)"></i>RAM</span><span class="muted">Ngưỡng cảnh báo: <b id="ram-th">—</b>%</span></div></section>
    <section class="panel"><div class="chart-header"><b>RTT / Packet Loss</b><small id="rtt-last">—</small></div><canvas id="chart-rtt" aria-label="Biểu đồ RTT" role="img"></canvas><div class="legend"><span><i class="swatch" style="background:var(--amber)"></i>RTT (ms)</span><span class="muted">1 ICMP / lần · <i class="swatch" style="background:var(--red)"></i>Dấu đỏ = mất gói</span></div></section>
    <section class="panel"><div class="chart-header"><b>Network I/O (KB/s)</b><small id="net-last">—</small></div><canvas id="chart-net" aria-label="Biểu đồ mạng" role="img"></canvas><div class="legend"><span><i class="swatch" style="background:var(--violet)"></i>Receive</span><span><i class="swatch" style="background:var(--blue)"></i>Send</span></div><p class="panel-note">Lưu lượng trên các interface được theo dõi. Mẫu đầu tiên chưa tính được tốc độ.</p></section>
  </div>
  <div class="section-head" id="devices"><h2>Thiết bị đang giám sát</h2><span class="hint">Chọn hàng để xem biểu đồ</span></div>
  <section class="panel" style="padding:0"><div class="table-wrap"><table class="grid-table"><thead><tr><th>Thiết bị</th><th>Trạng thái</th><th>CPU</th><th>RAM</th><th>RTT</th><th>Interface</th></tr></thead><tbody id="rows"><tr><td colspan="6" class="plain">Đang thu thập dữ liệu…</td></tr></tbody></table></div></section>
  <div class="section-head" id="services"><h2>Giám sát dịch vụ HTTP / TCP</h2><span class="hint" id="services-summary">Chưa khai báo dịch vụ</span></div>
  <section class="panel" style="padding:0"><div class="table-wrap"><table class="grid-table services-table"><thead><tr><th>Dịch vụ</th><th>Loại</th><th>Đích kiểm tra</th><th>Trạng thái</th><th>HTTP</th><th>Thời gian phản hồi</th></tr></thead><tbody id="service-rows"><tr><td colspan="6" class="plain">Chưa có dữ liệu dịch vụ</td></tr></tbody></table></div></section>
  <div class="section-head" id="alerts"><h2>Nhật ký cảnh báo</h2><span class="hint">Lưu sự cố và khôi phục vào nms_alerts.jsonl</span></div>
  <section class="panel"><div class="alerts" id="alerts-list"><span class="muted">Chưa có cảnh báo nào.</span></div></section>
  <div class="footer">NMS Monitor · Windows + Ubuntu VMware + Cisco GNS3 · SNMP / ICMP / HTTP / TCP / Telegram</div>
</main></div>
<script>
'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let DATA = null, selected = '', busy = false;
const sane = x => x !== null && x !== undefined && Number.isFinite(Number(x));
const fmt = (x,d=1) => sane(x) ? Number(x).toFixed(d) : '—';
const problematic = (m,th) => !m.reachable || ['cpu','ram','temp'].some(k=>sane(m[k]) && sane(th[k]) && Number(m[k])>Number(th[k])) || Object.values(m.ifaces||{}).includes('down');
function metricHtml(value,limit){
  if(!sane(value))return '<span class="plain">Không có dữ liệu</span>';
  const high=sane(limit)&&Number(value)>Number(limit),p=Math.max(0,Math.min(100,Number(value)));
  return `<b style="color:${high?'var(--red)':'var(--txt)'}">${fmt(value)}%</b><div class="track"><i class="${high?'high':''}" style="width:${p}%"></i></div>`;
}
function deviceRow(name,m,th){
  const bad=problematic(m,th), ping=m.kind==='ping';
  const st=bad?(m.reachable?'Cảnh báo':'Offline'):'Online';
  const cls=bad?(m.reachable?'warn':'bad'):'';
  const iface=Object.entries(m.ifaces||{}).map(([k,v])=>`<span class="iface ${v==='down'?'down':v==='unknown'?'unknown':''}">${esc(k)}: ${esc(v)}</span>`).join('')||'<span class="plain">—</span>';
  return `<tr class="${selected===name?'selected':''}" data-name="${esc(name)}"><td><div class="devname">${esc(name)}</div><div class="devsub">${ping?'ICMP · '+esc(m.host):esc(m.time||'SNMP / Local')}</div></td><td><span class="badge ${cls}"><i class="dot"></i>${st}</span></td><td>${metricHtml(m.cpu,th.cpu)}</td><td>${metricHtml(m.ram,th.ram)}</td><td>${sane(m.rtt_ms)?fmt(m.rtt_ms,2)+' ms':'—'}${sane(m.packet_loss)?`<div class="devsub">Mất ${fmt(m.packet_loss,0)}%</div>`:''}</td><td><div class="ifaces">${iface}</div></td></tr>`;
}
function serviceRow(item){
  const ok=item.ok===true, code=item.status_code;
  const label=ok?'Hoạt động':'Có sự cố';
  const state=ok?'':'bad';
  return `<tr><td><strong>${esc(item.name||'—')}</strong><div class="devsub">${esc(item.time||'')}</div></td><td>${esc(String(item.kind||'').toUpperCase())}</td><td><span class="devsub">${esc(item.endpoint||'—')}</span></td><td><span class="badge ${state}"><i class="dot"></i>${label}</span><div class="devsub">${esc(item.reason||'')}</div></td><td>${code===null||code===undefined?'—':esc(code)}</td><td>${sane(item.response_ms)?fmt(item.response_ms,1)+' ms':'—'}</td></tr>`;
}
function eventsHtml(items){
  if(!items.length)return '<span class="muted">Chưa có cảnh báo. Khi xuất hiện sự cố hoặc khôi phục, nhật ký sẽ hiển thị ở đây.</span>';
  return items.slice(0,30).map(a=>`<article class="alert ${a.level==='recovered'?'recovered':''}"><div><strong>${a.level==='recovered'?'✓ Đã khôi phục':'⚠ Cảnh báo'} · ${esc(a.device)}</strong><p>${esc(a.message)}</p></div><time>${esc(a.time||'')}</time></article>`).join('');
}
function drawChart(canvasId,series,keys,colors,opts={}){
  const canvas=$(canvasId); if(!canvas)return;
  const w=Math.max(300,Math.round(canvas.getBoundingClientRect().width||440)),h=185,dpr=window.devicePixelRatio||1;
  canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);
  const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
  const L=44,R=12,T=13,B=25, iw=w-L-R,ih=h-T-B;
  ctx.clearRect(0,0,w,h);
  let vals=[]; for(const item of series){for(const k of keys){if(sane(item[k]))vals.push(Number(item[k]));}}
  const max=opts.percent?100:Math.max(opts.floor||5, Math.ceil((Math.max(...vals,0)*1.15)/(opts.step||5))*(opts.step||5));
  ctx.strokeStyle='#31425d';ctx.lineWidth=1;ctx.font='11px Segoe UI, sans-serif';ctx.fillStyle='#8ba0bd';ctx.textAlign='right';
  for(let i=0;i<=4;i++){let y=T+i*ih/4;ctx.beginPath();ctx.moveTo(L,y);ctx.lineTo(w-R,y);ctx.stroke();ctx.fillText((max*(4-i)/4).toFixed(opts.percent?0:1),L-8,y+4);}
  if(!series.length||!vals.length){ctx.textAlign='center';ctx.fillStyle='#8398b5';ctx.fillText('Chưa có dữ liệu đo cho thiết bị này',w/2,h/2);return;}
  const labels=[0,Math.round((series.length-1)/2),series.length-1];ctx.textAlign='center';ctx.fillStyle='#7d90ac';
  for(const n of [...new Set(labels)]){const t=series[n].time||'';ctx.fillText(String(t).slice(11,19)||'—',L+(series.length===1?0:n/(series.length-1)*iw),h-5);}
  keys.forEach((key,index)=>{ctx.strokeStyle=colors[index];ctx.lineWidth=2.2;ctx.lineJoin='round';ctx.lineCap='round';ctx.beginPath();let active=false,valid=0;
    series.forEach((p,i)=>{if(!sane(p[key])){active=false;return;} const x=L+(series.length===1?iw/2:i/(series.length-1)*iw),y=T+ih-(Math.max(0,Math.min(max,Number(p[key])))/max)*ih;
      if(!active){ctx.moveTo(x,y);active=true;}else{ctx.lineTo(x,y);} valid++;});ctx.stroke();
    if(valid===1){let i=series.findIndex(p=>sane(p[key]));let p=series[i];let x=L+(series.length===1?iw/2:i/(series.length-1)*iw),y=T+ih-Number(p[key])/max*ih;ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fillStyle=colors[index];ctx.fill();}
  });
  if(canvasId==='chart-rtt'){
    ctx.fillStyle='#ff7188';
    series.forEach((p,i)=>{if(!sane(p.packet_loss)||Number(p.packet_loss)<=0)return;
      const x=L+(series.length===1?iw/2:i/(series.length-1)*iw);
      ctx.fillRect(x-2,T+1,4,11);
    });
  }
}
function refreshCharts(){if(!DATA)return;const series=(DATA.series||{})[selected]||[];const m=(DATA.devices||{})[selected]||{},th=DATA.thresholds||{};
  $('cpu-th').textContent=fmt(th.cpu,0);$('ram-th').textContent=fmt(th.ram,0);
  $('cpu-last').textContent=sane(m.cpu)?fmt(m.cpu)+' %':'—';$('ram-last').textContent=sane(m.ram)?fmt(m.ram)+' %':'—';
  $('rtt-last').textContent=(sane(m.rtt_ms)?fmt(m.rtt_ms,2)+' ms':'—')+(sane(m.packet_loss)?' · mất '+fmt(m.packet_loss,0)+'%':'');
  $('net-last').textContent=(sane(m.rx_kbps)||sane(m.tx_kbps))?`↓ ${fmt(m.rx_kbps)} / ↑ ${fmt(m.tx_kbps)} KB/s`:'—';
  drawChart('chart-cpu',series,['cpu'],['#44b8ff'],{percent:true});
  drawChart('chart-ram',series,['ram'],['#37dab0'],{percent:true});
  drawChart('chart-rtt',series,['rtt_ms'],['#ffca77'],{floor:5,step:5});
  drawChart('chart-net',series,['rx_kbps','tx_kbps'],['#a994ff','#44b8ff'],{floor:5,step:5});
}
function render(d){DATA=d;const devices=d.devices||{}, names=Object.keys(devices),th=d.thresholds||{};
  if(!names.includes(selected))selected=names.find(n=>sane(devices[n].cpu))||names[0]||'';
  const sel=$('device-select');const current=[...sel.options].map(x=>x.value).join('|');
  if(current!==names.join('|'))sel.innerHTML=names.map(n=>`<option value="${esc(n)}">${esc(n)}</option>`).join('');sel.value=selected;
  const online=names.filter(n=>devices[n].reachable).length,bad=names.filter(n=>problematic(devices[n],th)).length;
  $('count-total').textContent=names.length;$('count-online').textContent=online;$('count-alert').textContent=bad;$('interval').textContent=String(d.interval||5)+'s';
  $('updated').textContent=`Dữ liệu mới nhất: ${d.generated_at?String(d.generated_at).replace('T',' '):'chờ thu thập'} · Web tự làm mới mỗi 5 giây`;
  $('rows').innerHTML=names.length?names.map(n=>deviceRow(n,devices[n],th)).join(''):'<tr><td colspan="6">Chưa có dữ liệu. Đang chờ vòng giám sát đầu tiên…</td></tr>';
  const services=Object.values(d.services||{});
  $('service-rows').innerHTML=services.length?services.map(serviceRow).join(''):'<tr><td colspan="6" class="plain">Chưa khai báo dịch vụ. Thêm mục services: trong config.yaml để bật Lab 4/5.</td></tr>';
  $('services-summary').textContent=services.length?`${services.filter(x=>x.ok).length}/${services.length} dịch vụ hoạt động`:'Chưa khai báo dịch vụ';
  $('alerts-list').innerHTML=eventsHtml(d.alerts||[]);
  if(d.telegram_url && /^https:\/\/t\.me\/[A-Za-z0-9_]+$/.test(d.telegram_url))$('telegram').href=d.telegram_url;
  refreshCharts();
}
async function tick(){if(busy)return;busy=true;
  try{const r=await fetch('/api/metrics',{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);const d=await r.json();if(d.error)throw new Error(d.error);$('error').style.display='none';render(d);}
  catch(e){$('error').textContent='Không nhận được dữ liệu từ máy chủ: '+e.message;$('error').style.display='block';}
  finally{busy=false;}
}
$('device-select').addEventListener('change',e=>{selected=e.target.value;refreshCharts();if(DATA)render(DATA);});
$('refresh').addEventListener('click',tick);
$('rows').addEventListener('click',e=>{const tr=e.target.closest('tr[data-name]');if(!tr)return;selected=tr.getAttribute('data-name');if(DATA)render(DATA);});
window.addEventListener('resize',()=>{clearTimeout(window.__drawTimer);window.__drawTimer=setTimeout(refreshCharts,120);});
tick();setInterval(tick,5000);
</script>
</body>
</html>"""


def _safe_telegram_url(cfg):
    dash = (cfg or {}).get("dashboard") or {}
    username = str(dash.get("telegram_bot_username", "bta0004bot")).lstrip("@")
    username = re.sub(r"[^A-Za-z0-9_]", "", username)
    return "https://t.me/" + (username or "bta0004bot")


def current_snapshot():
    if SOURCE:
        try:
            response = requests.get(SOURCE.rstrip("/") + "/api/metrics", timeout=5)
            response.raise_for_status()
            snapshot = response.json()
            if snapshot.get("error"):
                raise ValueError(snapshot["error"])
            return snapshot
        except (requests.RequestException, ValueError) as exc:
            return {"error": f"Không lấy được số liệu từ nguồn {SOURCE}: {type(exc).__name__}"}
    if CFG is None:
        return {"error": "Chưa khởi tạo cấu hình NMS"}
    snapshot = monitor.get_snapshot(CFG)
    snapshot["telegram_url"] = _safe_telegram_url(CFG)
    return snapshot


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/api/metrics")
def api_metrics():
    data = current_snapshot()
    return jsonify(data), (502 if data.get("error") else 200)


def _report_html(data):
    """Xuất báo cáo HTML đầy đủ, biểu đồ SVG nhúng chạy offline."""
    return make_report(data)


@app.route("/report")
def report_view():
    return Response(_report_html(current_snapshot()), mimetype="text/html; charset=utf-8")


@app.route("/report/download")
def report_download():
    filename = "nms_report_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".html"
    return Response(_report_html(current_snapshot()), mimetype="text/html; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="{filename}"'
    })


@app.route("/report/alerts.csv")
def report_alerts_csv():
    data = current_snapshot()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Time", "Device", "Level", "Condition", "Message"])
    for item in data.get("alerts", []):
        writer.writerow([item.get(k, "") for k in ("time", "device", "level", "condition", "message")])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8", headers={
        "Content-Disposition": 'attachment; filename="nms_alerts.csv"'
    })


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="NMS Dashboard V2")
    parser.add_argument("config", nargs="?", help="Tệp YAML cấu hình (mặc định config.yaml)")
    parser.add_argument("--source", help="Đọc API từ máy đang chạy giám sát")
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ Flask lắng nghe")
    parser.add_argument("--port", type=int, default=5055, help="Cổng Flask")
    args = parser.parse_args()

    SOURCE = args.source
    if SOURCE:
        print("Chế độ Dashboard từ xa:", SOURCE)
    else:
        CFG = monitor.load_config(args.config)
        threading.Thread(target=monitor.loop, args=(CFG,), daemon=True).start()
    print(f"Dashboard: http://127.0.0.1:{args.port}")
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
