"""Giám sát định kỳ 60 giây và gửi cảnh báo khi trạng thái đổi."""

import os
import sys
import time
from datetime import datetime

from analyzer import analyze_device
from notifier import send_telegram

THRESHOLDS = {"cpu": 80, "ram": 85}
DEVICES = [
    {"name": "anh-ubutun-sdn", "ip": "192.168.10.128", "community": "labMmtnc2026"},
]
INTERVAL = 60


def now():
    return datetime.now().strftime("%H:%M:%S")


def run_once():
    for dev in DEVICES:
        try:
            messages = analyze_device(dev, THRESHOLDS)
        except Exception as exc:
            print(f"[{now()}] Lỗi kiểm tra {dev['name']}: {exc}")
            continue
        if not messages:
            print(f"[{now()}] {dev['name']}: không có thay đổi cần cảnh báo")
        for msg in messages:
            ok = send_telegram(msg)
            print(f"[{now()}] {'Đã gửi' if ok else 'Gửi thất bại'}: {msg}")


if __name__ == "__main__":
    if not os.environ.get("TELEGRAM_BOT_TOKEN") or not os.environ.get("TELEGRAM_CHAT_ID"):
        print("Chưa cấu hình Telegram. Đặt TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID trong PowerShell.")
        sys.exit(1)
    print(f"[{now()}] Bắt đầu giám sát. Nhấn Ctrl+C để dừng.")
    try:
        if "--once" in sys.argv:
            run_once()
        else:
            while True:
                run_once()
                time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nĐã dừng giám sát.")
