ĐỒ ÁN QUẢN TRỊ MẠNG NÂNG CAO - PYTHON/SNMP/TELEGRAM
==================================================

Môi trường xác nhận theo máy người dùng:
- Python 3.13 + pysnmp-lextudio==5.0.34, pyasn1==0.4.8, requests
- Ubuntu SNMP IP: 192.168.10.128 / Community: labMmtnc2026
- CPU >80%, RAM >85%, interface DOWN; kiểm tra mỗi 60 giây.

1. Giải nén 4 file .py vào D:\k1\MMT_NC\DoAn\Python
2. Trong PowerShell Windows:
   cd D:\k1\MMT_NC\DoAn\Python
   .\.venv\Scripts\python.exe collector.py
   (Phải nhận CPU, RAM và interface.)

3. Mở Telegram, tìm bot chính thức @BotFather, nhắn /newbot và làm theo chỉ dẫn.
   Nhận mã token. Không gửi token vào chat nhóm, không chụp token.
   Mở bot vừa tạo và gửi /start.

4. Trong CÙNG cửa sổ PowerShell:
   $env:TELEGRAM_BOT_TOKEN = Read-Host "Dan Telegram bot token"
   .\.venv\Scripts\python.exe notifier.py --get-chat-id
   (Copy Chat ID trả về, điền ở bước sau.)
   $env:TELEGRAM_CHAT_ID = Read-Host "Nhap Chat ID"
   .\.venv\Scripts\python.exe notifier.py --test
   (Bot Telegram phải nhận được tin kiểm thử.)

5. Giám sát (trong cùng PowerShell):
   .\.venv\Scripts\python.exe main.py
   Dừng bằng Ctrl+C.

6. Chạy một chu kỳ nếu cần thử nhanh:
   .\.venv\Scripts\python.exe main.py --once

Không chia sẻ TELEGRAM_BOT_TOKEN; đây là thông tin bí mật.
Dự án dùng đúng 4 module của báo cáo: collector/analyzer/notifier/main.
Tác động lên interface để kiểm thử có thể làm gián đoạn kết nối, chỉ thao tác
trên máy ảo lab sau khi xác định đúng tên interface và đường SNMP Host-only.
