"""Gửi cảnh báo: luôn in ra terminal, thêm Telegram/Slack nếu bật trong config.yaml."""
import requests


def send(cfg, text):
    print(text, flush=True)
    n = cfg.get("notify", {})

    t = n.get("telegram", {})
    if t.get("enabled"):
        try:
            requests.post(f"https://api.telegram.org/bot{t['token']}/sendMessage",
                          data={"chat_id": t["chat_id"], "text": text}, timeout=10)
        except Exception as e:
            print("Telegram lỗi:", e)

    s = n.get("slack", {})
    if s.get("enabled"):
        try:
            requests.post(s["webhook"], json={"text": text}, timeout=10)
        except Exception as e:
            print("Slack lỗi:", e)
