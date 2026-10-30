"""Gửi cảnh báo Telegram. Token và chat ID chỉ lưu trong biến môi trường."""

import os
import sys

import requests


def _credentials():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    return token, chat_id


def send_telegram(text, token=None, chat_id=None):
    """Trả về True khi Telegram Bot API xác nhận gửi tin thành công."""
    stored_token, stored_chat_id = _credentials()
    token = token or stored_token
    chat_id = chat_id or stored_chat_id
    if not token or not chat_id:
        print("[Telegram] Chưa đặt TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID.")
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        payload = response.json()
        if response.status_code == 200 and payload.get("ok") is True:
            return True
        print(f"[Telegram] Gửi thất bại (HTTP {response.status_code}): {payload.get('description', 'Unknown error')}")
    except (requests.RequestException, ValueError) as exc:
        print(f"[Telegram] Không gửi được: {exc}")
    return False


def show_chat_ids():
    """In chat ID từ các tin nhắn gửi đến bot gần đây."""
    token, _ = _credentials()
    if not token:
        print("Hãy đặt biến TELEGRAM_BOT_TOKEN trước.")
        return False
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates", timeout=10
        )
        payload = response.json()
        if not payload.get("ok"):
            print(f"Telegram báo lỗi: {payload.get('description', response.status_code)}")
            return False
        chats = {}
        for update in payload.get("result", []):
            message = (update.get("message") or update.get("edited_message")
                       or update.get("channel_post"))
            if message and message.get("chat"):
                chat = message["chat"]
                chats[str(chat["id"])] = chat.get("title") or chat.get("first_name") or "Không có tên"
        if not chats:
            print("Chưa có tin nhắn. Hãy vào Telegram nhắn /start cho bot, sau đó chạy lại.")
            return False
        for chat_id, display_name in chats.items():
            print(f"Chat ID: {chat_id} | {display_name}")
        return True
    except (requests.RequestException, ValueError) as exc:
        print(f"Không lấy được chat ID: {exc}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--get-chat-id":
        show_chat_ids()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = send_telegram("🧪 Kiểm thử MMTNC: kết nối Telegram thành công!")
        print("Gửi thành công" if success else "Gửi thất bại")
    else:
        print("Cách dùng: python notifier.py --get-chat-id hoặc --test")
