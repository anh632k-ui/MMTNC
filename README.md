# NHÁNH CỦA MÁY TAO — HƯỚNG DẪN MỞ LẠI TOÀN BỘ ĐỒ ÁN NMS SAU KHI TẮT MÁY

**Đồ án Mạng máy tính nâng cao (MMTNC): Hệ thống giám sát thiết bị mạng và cảnh báo qua Telegram/Slack**  
**Người triển khai máy chính:** Bùi Thế Anh  
**Máy chính:** Windows, tên từng hiển thị `DESKTOP-97SL3ND`  
**Dành riêng cho nhánh:** `nhanh-cua-may-tao`  
**Ngày chốt trạng thái hoạt động:** 02/11/2026  
**Mục đích:** Sau khi tắt hoàn toàn Windows, VMware, Ubuntu, GNS3 và NMS, chỉ cần đọc từ trên xuống để khôi phục đúng trạng thái đã demo: **7 đối tượng được giám sát, 5 dịch vụ HTTP/TCP, biểu đồ, cảnh báo và phục hồi Telegram, báo cáo HTML**.

> **ĐÂY LÀ SỔ TAY KHỞI ĐỘNG LẠI, KHÔNG PHẢI LỆNH CÀI LẠI TỪ ĐẦU.** Trên đúng máy cũ, không cần tạo lại VM, router, community, bot hay môi trường ảo. Việc quan trọng là mở đúng thứ tự và kiểm tra từng nơi. Nếu cấu hình vẫn được lưu đúng, **không gõ lại lệnh gán IP/OSPF/SNMP trên router mỗi lần**.
>
> **Bảo mật:** Không chia sẻ `config.yaml`, token Telegram, mật khẩu Ubuntu hoặc SNMP community. `config.yaml` bị Git bỏ qua nên *không được phục hồi tự động chỉ bằng git clone*. README này không chứa thông tin xác thực thật.
>
> **Nếu cần dựng từ số 0:** Xem README 1.372 dòng trên nhánh `main`: https://github.com/anh632k-ui/MMTNC/blob/main/README.md

---

## 0. BẢN ĐỒ MÁY — MỞ GÌ Ở ĐÂU?

| Thiết bị/chương trình | Bạn mở ở đâu? | Làm nhiệm vụ gì? | Có phải mở mỗi lần không? |
| --- | --- | --- | --- |
| **Windows thật** | Máy tính chính | Trung tâm mạng VMnet1 và chạy NMS | Có |
| **VMware Workstation** | Trên Windows | Chạy máy ảo Ubuntu | Có |
| **Ubuntu 64-bit** | Trong VMware | Cung cấp SNMPD, SSH, Nginx để Windows giám sát | Có, phải Power On VM |
| **GNS3** | Trên Windows | Chạy ba router Cisco R1/R2/R3 | Có |
| **Switch2 + Cloud1** | Bên trong GNS3 | Nối mạng quản lý Cisco sang VMnet1 | Chỉ cần cấu hình ban đầu; mở project là có |
| **Visual Studio Code** | Trên Windows | Mở mã nguồn NMS và terminal PowerShell | Có (hoặc chạy Python từ PowerShell độc lập) |
| **`python web.py`** | PowerShell trong thư mục `nms-monitor` | **Khởi động Dashboard VÀ toàn bộ monitor** | Có |
| **Trình duyệt** | Trên Windows | Mở Dashboard và báo cáo | Có |
| **Telegram** | Web/app điện thoại | Nhận cảnh báo, thông báo khôi phục | Không cần mở để bot gửi; chỉ mở để xem |
| **`demo_http_lab4.py`** | File demo cũ | Giả lập mã HTTP 200/503/chậm | **Không cần chạy** khi dùng Nginx cổng 80 |
| **`monitor.py` riêng** | NMS Python | Vòng thu thập/cảnh báo | **Không mở thêm** khi đã chạy `web.py` |
| **WSL/Mininet** | Windows/WSL | Thực hành Buổi 5 riêng | **Không cần chạy** để demo đồ án hiện tại |

### Địa chỉ đã thống nhất — phải nhớ

| Thiết bị | Địa chỉ / cổng |
| --- | --- |
| **Windows VMnet1** | `192.168.10.1/24` |
| **Ubuntu ens34 (Host-only VMnet1)** | `192.168.10.128/24` |
| **Ubuntu ens33 (NAT VMnet8)** | DHCP, trước đây `192.168.126.130/24` (có thể thay đổi) |
| **R1 f1/0** | `192.168.10.11/24` |
| **R2 f1/0** | `192.168.10.12/24` |
| **R3 f1/0** | `192.168.10.13/24` |
| **SNMP** | UDP `161` |
| **SSH Ubuntu** | TCP `22` |
| **Nginx Ubuntu** | HTTP/TCP `80` |
| **Dashboard NMS Windows** | `http://localhost:5055/` |
| **Router ↔ Switch** | R1 f1/0 ↔ Switch2 e0; R2 f1/0 ↔ Switch2 e1; R3 f1/0 ↔ Switch2 e2 |
| **Switch ↔ Cloud** | Switch2 e3 ↔ Cloud1 (`VMware Network Adapter VMnet1`) |

**Luồng kết nối:**

```text
                      Windows thật
               [VMnet1: 192.168.10.1]
                    [NMS web.py]
                         |
             +-----------+-----------+
             |                       |
      VMware Ubuntu              Cloud1 (GNS3)
   ens34=192.168.10.128               |
    ├─ SNMPD :161                   Switch2
    ├─ SSH   :22                /      |       \
    └─ Nginx :80              R1       R2      R3
                          10.11     10.12    10.13
                           \___________________/
                           Các đường nối tam giác
                           (10.0.12.x / 13.x / 23.x)
```

**Giám sát cái gì?** Windows: CPU/RAM/Network I/O bằng psutil. Ubuntu + R1/R2/R3: SNMP lấy CPU/RAM/trạng thái interface/RX/TX. Ping lấy RTT/packet loss. HTTP thử website 200/độ trễ. TCP kiểm tra cổng 22/80/5055. Sự cố gửi Telegram và lưu nhật ký. **Nhiệt độ chỉ hiện khi thiết bị thực sự cung cấp dữ liệu**.

---

## 1. HÔM NAY TRƯỚC KHI TẮT MÁY — LÀM MỘT LẦN

**Đây là checklist quan trọng nhất để mai không phải cấu hình lại.**

### 1.1. Lưu config của 3 router trong GNS3

Mở GNS3 nếu đang chạy, nhấp phải **R1 → Console**. Trong CLI:

```cisco
enable
show ip interface brief
show running-config | include snmp-server
show ip ospf neighbor
write memory
```

Lặp lại trên **R2**, **R3** (mỗi router là một cửa sổ Console riêng).

Khi `write memory` thành công, phải thấy `Building configuration...` và `[OK]`. Đây là lưu cấu hình IOS (địa chỉ IP, OSPF, SNMP...) vào bộ nhớ router ảo. **Không phải chỉ nhấn Save trong GNS3 là mọi cấu hình IOS đều được lưu.**

> Không cần nhập lại lệnh `interface FastEthernet...`, `ip address...`, `snmp-server community...` khi chuẩn bị tắt. Chỉ **kiểm tra và lưu**. Nếu có một cổng tắt do test, khôi phục nó trước khi lưu (xem 1.2).

### 1.2. Đưa thiết bị về trạng thái bình thường

Trên R1, R2, R3:

```cisco
show ip interface brief
```

Các cổng thực sự đang được dùng phải `up/up` (đặc biệt **FastEthernet1/0** trên mỗi router để NMS còn hỏi SNMP). Nếu trước đó đã thử **shutdown FastEthernet0/0 của R1**, khôi phục:

```cisco
configure terminal
interface FastEthernet0/0
no shutdown
end
write memory
```

Chỉ dùng block trên khi **đúng là R1 f0/0 đang shutdown**; không tùy tiện thay đổi các interface của topology.

### 1.3. Lưu project GNS3

GNS3 → **File → Save** (hoặc Ctrl+S). Đảm bảo project vẫn tên **NMS-Monitor-Anh**.

Project đã tạo trên Windows nằm gần:

```text
D:\k1\MMT_NC\DoAn\GNS3\NMS-Monitor-Anh\
    NMS-Monitor-Anh.gns3
    project-files\
```

File portable dự phòng đã xuất:

```text
D:\k1\MMT_NC\GNS3_Export\NMS-Monitor-Anh.gns3project
```

**Không phải export portable lại mỗi ngày.** Dùng project gốc trên máy này để tiếp tục. Portable chỉ để khôi phục/chuyển máy, và còn phụ thuộc template/IOS Cisco hợp pháp.

### 1.4. Đảm bảo code và config NMS đang có

Mở File Explorer, dán vào thanh địa chỉ:

```text
D:\k1\MMT_NC\DoAn\nms-monitor
```

Cần thấy tối thiểu:

```text
web.py
monitor.py
collector.py
snmp_utils.py
snmp_lite.py
service_checks.py
notifier.py
nms_report.py
requirements.txt
config.yaml                <- RẤT QUAN TRỌNG, file cấu hình RIÊNG
.venv\Scripts\python.exe   <- môi trường Python trên máy này
```

**Chú ý:** `config.yaml` phải còn tên thiết bị/IP/community/Telegram, ngưỡng CPU 80%, RAM 85%, dịch vụ HTTP và TCP đúng. File này bị `.gitignore` loại khỏi GitHub vì có bí mật. Nếu muốn dự phòng, hãy sao lưu riêng vào nơi an toàn có kiểm soát quyền truy cập; **không upload file chứa token lên repository Public**.

Có thể kiểm tra file tồn tại trong PowerShell:

```powershell
cd D:\k1\MMT_NC\DoAn\nms-monitor
Test-Path .\config.yaml
Test-Path .\.venv\Scripts\python.exe
```

Cả hai nên là `True`.

### 1.5. Trả ngưỡng RAM về 85% sau khi demo

Mở `config.yaml`, tìm:

```yaml
thresholds:
  cpu: 80
  ram: 85
  temp: 70
```

**Không giữ RAM=60** vì đó là ngưỡng đặt tạm để thử cảnh báo.

### 1.6. Trên Ubuntu, cài chế độ tự bật service (nếu chưa làm)

Mở Ubuntu Terminal trong VMware:

```bash
sudo systemctl enable snmpd
sudo systemctl enable ssh
sudo systemctl enable nginx
systemctl is-enabled snmpd ssh nginx
```

Mong đợi các service đều `enabled`; nếu chỉ có service không tồn tại thì xem mục 6.3. Khi Ubuntu mở lại, ba service có thể tự hoạt động mà **không cần chạy `demo_http_lab4.py`**.

### 1.7. Tắt máy đúng thứ tự

1. Ở Terminal đang chạy `python web.py` trên Windows, nhấn **Ctrl+C** để dừng NMS.
2. Trên GNS3, lưu project, **Stop All Nodes** rồi đóng GNS3. Nếu cần lưu cấu hình IOS, phải `write memory` **trước** bước này.
3. Trong Ubuntu, có thể mở Terminal chạy `sudo shutdown -h now` hoặc dùng menu nguồn Ubuntu → **Power Off**. Chờ máy ảo thực sự dừng.
4. Đóng VMware Workstation (không cần xóa VM/snapshot). Không chọn **Delete from disk**, **Remove** hoặc **Reset**.
5. Tắt Windows qua **Start → Power → Shut down**.

Nếu Windows tự cài update/reboot, chờ VM/routers tắt an toàn. **Không xóa `.venv`, `config.yaml`, VM file hoặc `project-files`.**

---

## 2. NGÀY MAI / BẤT KỲ LÚC NÀO MỞ LẠI — CỨ LÀM THEO ĐÚNG THỨ TỰ

**Thứ tự chuẩn: Windows → VMware Ubuntu → GNS3 Cisco → kiểm tra kết nối → VS Code NMS → Dashboard → Telegram.**  
Không cần bật WSL, Mininet, router_sim.py hoặc file HTTP demo.

### BƯỚC 1 — Bật máy Windows thật

1. Bấm nút nguồn laptop/PC, đăng nhập Windows.
2. **Chưa mở Python NMS vội.**
3. Kiểm tra Wi-Fi/Internet nếu muốn ping Google DNS/Cloudflare và gửi Telegram. **Mạng VMnet1 vẫn có thể giám sát thiết bị nội bộ ngay cả khi Internet tạm mất**.
4. Mở **Windows PowerShell**: nhấn Win, gõ `PowerShell`, mở ứng dụng (không phải Ubuntu WSL).

Chạy:

```powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.InterfaceAlias -like "*VMnet1*" } |
  Select-Object InterfaceAlias,IPAddress,PrefixLength
```

**Kết quả mong muốn:**

```text
InterfaceAlias                   IPAddress       PrefixLength
VMware Network Adapter VMnet1    192.168.10.1    24
```

- **Đúng:** chuyển sang BƯỚC 2.
- **Không thấy VMnet1:** xem mục 6.1, chưa vội sửa router.
- **IP VMnet1 khác 192.168.10.1:** xem VMware Virtual Network Editor và thông số mạng của máy cũ. Không đổi hàng loạt IP nếu chưa xác định nguồn lỗi.

### BƯỚC 2 — Mở VMware Workstation và bật Ubuntu

**Trên Windows:**

1. Nhấp **Start** → tìm **VMware Workstation** → mở.
2. Ở trang **Home / Library**, chọn máy ảo tên **Ubuntu 64-bit**.
3. **Nếu VM đã có trong Library, không tạo máy ảo mới, không tải ISO lại.**
4. Trước khi bật, nếu cần kiểm tra: nhấp **VM → Settings**.
5. Chọn **Network Adapter** thứ nhất: **NAT / VMnet8**.
6. Chọn **Network Adapter** thứ hai: **Host-only / VMnet1** (hoặc **Custom: Specific virtual network → VMnet1** tùy bản VMware).
7. Không đổi nhầm NAT thành Bridged hoặc gán cả hai adapter vào VMnet8.
8. Nhấp **Power on this virtual machine** (tam giác xanh).
9. Chờ giao diện Ubuntu Desktop xuất hiện, đăng nhập bằng tài khoản/mật khẩu của chính máy ảo.

Nếu VMware hỏi **I moved it / I copied it** khi mở VM từ vị trí mới, đó là thao tác chuyển VM khác với việc mở lại VM cũ; trên máy đã lưu đúng không cần chọn lại mỗi lần.

### BƯỚC 3 — Kiểm tra Ubuntu đã có hai card mạng

**Bên trong cửa sổ Ubuntu Desktop:**

1. Nhấn **Ctrl+Alt+T** để mở Terminal (nếu VMware giữ tổ hợp phím, mở biểu tượng Terminal ở thanh ứng dụng).
2. Gõ:

```bash
ip -br a
```

**Phải có dạng:**

```text
lo      UNKNOWN  127.0.0.1/8
ens33   UP       192.168.126.xxx/24
ens34   UP       192.168.10.128/24
```

**Quan trọng:**
- `ens33` là NAT (ra Internet), có thể đổi số IP theo DHCP.
- `ens34` là Host-only (đường nối router/Windows), **cần giữ 192.168.10.128/24** để khớp config NMS.
- Nếu cả ens33/ens34 đều UP nhưng ens34 không có `192.168.10.128`, xem mục 6.2.
- Không cần cài lại Ubuntu, không cần chạy `sudo apt update` mỗi lần mở máy.

Kiểm tra Internet tùy chọn:

```bash
ping -c 2 1.1.1.1
```

Không có Internet chưa chắc đồng nghĩa SNMP nội bộ sai; tiếp tục kiểm tra VMnet1 riêng.

### BƯỚC 4 — Kiểm tra SNMPD, SSH và Nginx trên Ubuntu

**Vẫn trong Ubuntu Terminal:**

```bash
systemctl is-active snmpd
systemctl is-active ssh
systemctl is-active nginx
```

**Cả ba dòng phải trả `active`.**

Giải thích:
- **snmpd**: cho Windows NMS đọc CPU/RAM/interface Ubuntu qua UDP 161.
- **ssh**: cho Windows NMS kiểm tra TCP 22.
- **nginx**: cho Windows NMS kiểm tra HTTP 200 và TCP 80.

Nếu có service `inactive` hoặc `failed`, hãy khởi động đúng service đó:

```bash
sudo systemctl start snmpd
sudo systemctl start ssh
sudo systemctl start nginx
```

Muốn lần sau tự bật:

```bash
sudo systemctl enable snmpd
sudo systemctl enable ssh
sudo systemctl enable nginx
```

Xác nhận các cổng:

```bash
sudo ss -lunp | grep ':161'
sudo ss -lntp | grep -E ':(22|80)\b'
```

Kết quả mong muốn:
- UDP 161 lắng nghe ở `192.168.10.128:161` (có thể kèm `127.0.0.1:161`).
- TCP 22 có SSHD lắng nghe.
- TCP 80 có Nginx lắng nghe.

**Kiểm tra Nginx ngay trên Ubuntu:**

```bash
curl -I http://127.0.0.1/
```

Mong đợi HTTP 200. Nhưng **chỉ kiểm tra localhost Ubuntu chưa chứng minh Windows kết nối được**; đến BƯỚC 8 sẽ kiểm tra từ Windows.

**Không chạy các lệnh sau nếu không có mục đích kiểm thử:**

```text
sudo systemctl stop nginx   <- làm Ubuntu HTTP đỏ
sudo systemctl stop snmpd   <- làm Ubuntu không trả SNMP
sudo systemctl stop ssh     <- làm cổng SSH báo lỗi
```

### BƯỚC 5 — Mở GNS3 và chạy lại R1, R2, R3

**Quay lại Windows (không đóng máy ảo Ubuntu):**

1. Nhấn Win → gõ **GNS3** → mở GNS3.
2. Nếu GNS3 tự mở lại project **NMS-Monitor-Anh**, kiểm tra đúng tên trên thanh tiêu đề.
3. Nếu ra trang trống: GNS3 → **File → Open Project**, chọn **NMS-Monitor-Anh** trong danh sách dự án đã lưu.
4. Nếu không thấy, dùng **File → Open...** hoặc mở file project gốc:

```text
D:\k1\MMT_NC\DoAn\GNS3\NMS-Monitor-Anh\NMS-Monitor-Anh.gns3
```

5. **Không nhấn New Blank Project**, không tạo R1/R2/R3 mới, không import portable nếu project hiện tại vẫn còn.
6. Nhìn canvas: phải có **R1, R2, R3, Switch2, Cloud1**. Trong file topology trên GitHub có thể còn **Switch1 cũ không sử dụng**; **Switch2** là switch quản lý đang nối ba router.
7. Nhấn nút **Start/Play màu xanh** để chạy các thiết bị cần thiết.
8. Chờ đèn ở R1, R2, R3 chuyển xanh; Cloud/Switch2 giữ liên kết.
9. Kiểm tra **Cloud1 ↔ Switch2 e3** vẫn là **VMware Network Adapter VMnet1**.
10. Đừng tạo thêm đường Cloud1–Switch2 khác. Mỗi cổng chỉ nối một lần.

**Sơ đồ cổng đúng của project:**

```text
R1 f0/0 <-> R2 f0/0
R1 f0/1 <-> R3 f0/0
R2 f0/1 <-> R3 f0/1
R1 f1/0 <-> Switch2 e0
R2 f1/0 <-> Switch2 e1
R3 f1/0 <-> Switch2 e2
Switch2 e3 <-> Cloud1 (VMware Network Adapter VMnet1)
```

### BƯỚC 6 — Mở Console của ba router, CHỈ KIỂM TRA, KHÔNG GÁN LẠI IP

**Trên GNS3:**

1. Nhấp phải **R1** → **Console**.
2. Cửa sổ đen xuất hiện; nếu có `Press RETURN to get started!`, nhấn **Enter**.
3. Nếu prompt là `R1>`, gõ `enable` (để vào `R1#`).
4. Gõ lần lượt:

```cisco
show ip interface brief
show ip ospf neighbor
show running-config | include snmp-server
```

**Kỳ vọng trên R1:**

```text
FastEthernet0/0  10.0.12.1      up/up
FastEthernet0/1  10.0.13.1      up/up
FastEthernet1/0  192.168.10.11  up/up
```

5. Đóng cửa sổ Console R1 hoặc để đó; **đóng Console không có nghĩa tắt router**.
6. Nhấp phải **R2 → Console**, Enter, `enable` nếu cần:

```cisco
show ip interface brief
show ip ospf neighbor
show running-config | include snmp-server
```

**Kỳ vọng R2:**

```text
FastEthernet0/0  10.0.12.2      up/up
FastEthernet0/1  10.0.23.1      up/up
FastEthernet1/0  192.168.10.12  up/up
```

7. Nhấp phải **R3 → Console**, Enter, `enable` nếu cần:

```cisco
show ip interface brief
show ip ospf neighbor
show running-config | include snmp-server
```

**Kỳ vọng R3:**

```text
FastEthernet0/0  10.0.13.2      up/up
FastEthernet0/1  10.0.23.2      up/up
FastEthernet1/0  192.168.10.13  up/up
```

Nếu có cổng `administratively down`, tức đã bị `shutdown`. Chỉ mở lại đúng cổng cần dùng **sau khi kiểm tra cáp tương ứng**:

```cisco
configure terminal
interface FastEthernet0/0
no shutdown
end
write memory
```

*Đó chỉ là ví dụ cho f0/0. Không dán trên f1/0 một cách mù quáng và không thay địa chỉ IP khi `show` đã đúng.*

Nếu cổng là `up/down` hoặc `down/down`, kiểm tra đầu kia đã Start trong GNS3 và cáp có nối đúng chưa. OSPF có thể cần một khoảng để phát hiện hàng xóm. Trên mạng đa truy cập, trạng thái `2WAY` của một số hàng xóm có thể bình thường; tập trung xác minh các đường nối cần dùng và SNMP.

> **Quan trọng:** Sau reboot, chỉ chạy `show` và ping. **Không phải lần nào cũng vào `configure terminal` rồi paste lại tất cả cấu hình**. Nếu IP bị mất, xem mục 6.5 về lưu NVRAM trước khi phục dựng.

### BƯỚC 7 — Test ping trên Windows thật

**Để GNS3 và Ubuntu đang chạy.** Mở **Windows PowerShell** (không dùng terminal WSL):

```powershell
ping 192.168.10.11
ping 192.168.10.12
ping 192.168.10.13
ping 192.168.10.128
```

Kỳ vọng từng thiết bị có câu:

```text
Reply from 192.168.10.xx: bytes=32 time=...ms TTL=...
```

Lần đầu có thể có một gói lỗi do ARP khởi động, hãy chạy lại và xem kết quả tổng. Nếu router hoặc Ubuntu mất 100%, **đừng chạy NMS ngay**, chuyển đến mục 6.1/6.2/6.4.

Dùng lệnh này để xem cổng dịch vụ Ubuntu:

```powershell
Test-NetConnection 192.168.10.128 -Port 80
Test-NetConnection 192.168.10.128 -Port 22
```

Cần thấy `TcpTestSucceeded : True`.

**Không dùng `Test-NetConnection -Port 161` để kiểm tra SNMP**, vì SNMP đang dùng **UDP 161**, còn `-Port` là kiểm tra TCP.

Kiểm tra HTTP từ Windows:

```powershell
(Invoke-WebRequest -Uri "http://192.168.10.128/" -UseBasicParsing -TimeoutSec 5).StatusCode
```

Kỳ vọng `200`.

### BƯỚC 8 — Mở VS Code đúng thư mục NMS

**Trên Windows:**

1. Mở **Visual Studio Code**.
2. Chọn **File → Open Folder...**.
3. Dán đúng đường dẫn:

```text
D:\k1\MMT_NC\DoAn\nms-monitor
```

4. Nhấn **Select Folder**.
5. Nhìn bên trái phải thấy `web.py`, `monitor.py`, `config.yaml`, `requirements.txt`.
6. Chọn **Terminal → New Terminal**.
7. Nhìn prompt, cần là **PowerShell Windows** dạng:

```text
PS D:\k1\MMT_NC\DoAn\nms-monitor>
```

8. Nếu terminal là Ubuntu WSL (`anhanh@DESKTOP...`), bấm dấu mũi tên bên cạnh nút **+** trong Terminal → chọn **PowerShell** → mở terminal mới, hoặc chọn **Terminal: Select Default Profile → PowerShell**.

**Tuyệt đối không chạy file Windows .venv trong WSL.** Bản đồ án chính đang chạy trên Windows thật vì VMnet1 đã nối trực tiếp được đến router.

### BƯỚC 9 — Kiểm tra config và môi trường Python (KHÔNG CÀI LẠI)

Tại **PowerShell Windows** trong nms-monitor:

```powershell
Test-Path .\config.yaml
Test-Path .\.venv\Scripts\python.exe
```

Hai kết quả phải là `True`.

Sau đó, nếu muốn kiểm tra nhanh thư viện:

```powershell
.\.venv\Scripts\python.exe -c "import flask, psutil, yaml, requests; print('Python OK')"
```

Nếu kết quả `Python OK` thì **không cần chạy lại** `py -m venv .venv` hay `pip install`.

**Các điều phải có trong config.yaml:**

- `devices`: R1 = `192.168.10.11`, R2 = `192.168.10.12`, R3 = `192.168.10.13`, Ubuntu-VM = `192.168.10.128`.
- `interfaces`: router `[1,2,3]`; Ubuntu `[2,3]`.
- `snmp_community`: đúng chuỗi riêng đã cấu hình trên thiết bị (có thể khác nhau giữa Cisco và Ubuntu), **không gửi vào chat/GitHub**.
- `notify.telegram.enabled: true`, token và `chat_id` **đúng**, `chat_id` không phải `@username_bot`.
- `thresholds.cpu: 80`, `thresholds.ram: 85` (không để 60 do test).
- HTTP Ubuntu = `http://192.168.10.128/` (Nginx cổng 80); TCP Ubuntu SSH `22`, web `80`.
- Dashboard Windows mặc định cổng `5055`.

**Không tự động tạo lại `config.yaml` từ mẫu nếu file cũ vẫn còn**, vì file mẫu chỉ có placeholder nên sẽ mất thiết lập bot/community đã hoạt động.

### BƯỚC 10 — CHỈ CẦN MỘT LỆNH ĐỂ CHẠY TOÀN BỘ NMS

Đây là **lệnh chính xác, ngắn nhất và chắc chắn dùng đúng venv**:

```powershell
.\.venv\Scripts\python.exe web.py
```

Hoặc nếu Terminal hiện `(.venv)` (đã activate):

```powershell
python web.py
```

**Chỉ chạy 1 terminal chứa lệnh này.** Để cửa sổ terminal mở trong suốt quá trình giám sát. Không nhấn Ctrl+C khi muốn tiếp tục chạy. Đừng chạy thêm `monitor.py` trong terminal khác.

**Kết quả mong muốn có dòng:**

```text
Dashboard: http://127.0.0.1:5055
 * Serving Flask app 'web'
 * Debug mode: off
```

Sau đó cứ mỗi vòng NMS sẽ ghi trạng thái thiết bị/dịch vụ vào terminal, còn Flask cung cấp giao diện web.

**Phân biệt:**
- `web.py`: vừa chạy Flask, vừa khởi động thread `monitor.loop` trong cùng chương trình.
- `monitor.py`: không phải một tiến trình bắt buộc mở riêng.
- `demo_http_lab4.py`: không cần chạy vì Ubuntu đã dùng Nginx tự khởi động.
- `router_sim.py`: không cần vì đã có ba router Cisco trong GNS3.
- `--source`: là chế độ Dashboard đọc dữ liệu máy khác; **không dùng** trong cấu hình Windows giám sát chính.

### BƯỚC 11 — Mở Dashboard trong trình duyệt Windows

Mở Chrome/Edge, nhập:

**http://localhost:5055/**

Các mục cần xem:
1. **Tổng quan**: trạng thái mạng và thiết bị.
2. **Biểu đồ hiệu suất**: CPU/RAM/RTT/Network I/O/Packet Loss theo thời gian.
3. **Danh sách thiết bị**: Windows, Ubuntu, R1, R2, R3, Google DNS, Cloudflare.
4. **Dịch vụ HTTP/TCP**: 5 dịch vụ.
5. **Lịch sử cảnh báo**: thông báo sự cố/khôi phục.
6. **Xuất báo cáo HTML** và **Mở Telegram** (nút có trên Dashboard).

**Kỳ vọng số lượng với cấu hình đã demo:**

```text
7 đối tượng:
  1 Windows thật
  1 Ubuntu-VM
  3 Router Cisco (R1, R2, R3)
  2 đích ping (Google DNS và Cloudflare)

5 dịch vụ HTTP/TCP:
  NMS-Dashboard-HTTP    127.0.0.1:5055
  NMS-Dashboard-TCP     127.0.0.1:5055
  Ubuntu-HTTP           192.168.10.128:80
  Ubuntu-HTTP-Port      192.168.10.128:80
  Ubuntu-SSH            192.168.10.128:22
```

**Kết quả lý tưởng:** tất cả thiết bị đang Online, các interface theo dõi UP, mục Dịch vụ hiện **5/5 hoạt động**; không có cảnh báo CPU/RAM hiện tại.

**Quan trọng:** Đừng chỉ nhìn dòng "Monitoring Active" bên trái; hãy kiểm tra **thời điểm cập nhật số liệu phải đang tiến lên**. Nếu thời gian không đổi, có thể chỉ đang xem lịch sử cũ trong trình duyệt.

### BƯỚC 12 — Xác minh API NMS thật sự đang lấy dữ liệu

Trong một cửa sổ PowerShell Windows **mới** (không tắt terminal đang chạy `python web.py`):

```powershell
$api = Invoke-RestMethod http://127.0.0.1:5055/api/metrics
$api.generated_at
$api.devices.PSObject.Properties.Name
$api.services.PSObject.Properties.Name
```

Kỳ vọng có thời gian mới và các tên thiết bị/dịch vụ. Kiểm tra lại sau một vài vòng lấy mẫu xem thời gian/số liệu thay đổi.

Nếu `Invoke-RestMethod` thất bại, chuyển mục 6.6 (port/process Flask).

### BƯỚC 13 — Mở Telegram để kiểm tra (không cần tạo bot mới)

1. Mở Telegram Desktop / Telegram Web / điện thoại.
2. Chọn chat bot NMS đã dùng trong buổi demo (bot `mmt` mà nhóm đã thử).
3. Sau khi NMS khởi động thành công, nếu Telegram đang bật và mạng Internet bình thường, có thể thấy tin **“NMS Monitor đã khởi động”**.
4. Nếu chưa có tin, **không được tự kết luận NMS thất bại**: đối chiếu terminal, config Telegram, kết nối Internet và log (mục 6.8).
5. Khi giám sát bình thường, NMS **không gửi cảnh báo lặp liên tục**. Tin mới chủ yếu xuất hiện khi có sự cố hoặc phục hồi.

**Cảnh báo thực tế đã được chứng minh trước khi tắt máy:**
- Ubuntu-VM RAM vượt ngưỡng thử nghiệm.
- Ubuntu Nginx HTTP và TCP 80 dừng → Telegram cảnh báo; chạy lại → thông báo khôi phục.
- R1 FastEthernet0/0 DOWN → cảnh báo; UP → thông báo khôi phục.

### BƯỚC 14 — Mở lại phần báo cáo (nếu chuẩn bị thuyết trình)

Trình duyệt Windows:

```text
http://localhost:5055/report
http://localhost:5055/report/download
http://localhost:5055/report/alerts.csv
```

**Mở `/report`** để xem trước; **`/report/download`** để lưu HTML mới. File báo cáo xuất mới sẽ lấy dữ liệu/lịch sử đang có, gồm thiết bị, HTTP/TCP, sự kiện và 6 biểu đồ: CPU, RAM, RTT, RX, TX, mất gói.

Chỉ gửi **báo cáo HTML** nếu muốn gửi thống kê; không gửi các file YAML bí mật.

---

## 3. BẢNG ĐÁNH DẤU — MỞ LẠI XONG CHƯA?

Mỗi khi khởi động lại, tick trực tiếp theo trình tự:

- [ ] Windows đăng nhập, VMnet1 = **192.168.10.1/24**.
- [ ] VMware Workstation mở đúng **Ubuntu 64-bit** và đã Power On.
- [ ] Ubuntu đăng nhập, `ens33` NAT **UP**, `ens34` Host-only = **192.168.10.128/24**.
- [ ] Ubuntu: `systemctl is-active snmpd ssh nginx` cả 3 **active**.
- [ ] Ubuntu: HTTP `curl -I http://127.0.0.1/` trả **200**.
- [ ] GNS3 mở đúng **NMS-Monitor-Anh**, không phải blank project.
- [ ] R1, R2, R3 đều **Started**, cáp Switch2–Cloud1 VMnet1 còn nguyên.
- [ ] R1 f1/0 `192.168.10.11`; R2 f1/0 `192.168.10.12`; R3 f1/0 `192.168.10.13`; các interface quản lý **up/up**.
- [ ] Windows ping `.11`, `.12`, `.13`, `.128` thành công.
- [ ] Windows thử `192.168.10.128:80` và `:22` thành công.
- [ ] VS Code mở **`D:\k1\MMT_NC\DoAn\nms-monitor`**.
- [ ] PowerShell (KHÔNG PHẢI WSL), có `config.yaml`, `.venv\Scripts\python.exe`.
- [ ] Đã chạy **duy nhất** `.\.venv\Scripts\python.exe web.py`.
- [ ] Trình duyệt mở **http://localhost:5055/**.
- [ ] Các thiết bị hiện đúng; **không có dữ liệu cũ/stale**.
- [ ] Dịch vụ **5/5** hoạt động.
- [ ] Telegram bot có thể nhận tin từ NMS, không cần tạo bot mới.
- [ ] Báo cáo `/report` mở được và có biểu đồ.
- [ ] Đã để nguyên ba chương trình **GNS3 + VMware Ubuntu + NMS PowerShell** chạy khi demo.

Nếu chưa tick hết, sang mục 6 để tìm đúng lỗi, đừng cấu hình lại từ đầu.

---

## 4. LỆNH "NHỚ ÍT THÔI" — MỞ LẠI THẬT NHANH

### 4.1. Ubuntu — chỉ cần 2 lệnh kiểm tra

```bash
ip -br a
systemctl is-active snmpd ssh nginx
```

Nếu service inactive, chỉ cần:

```bash
sudo systemctl start snmpd ssh nginx
```

### 4.2. GNS3 — không cần paste cấu hình

**Open Project NMS-Monitor-Anh → Start → R1/R2/R3 → Console →**:

```cisco
enable
show ip interface brief
```

Kiểm tra trạng thái up/up, chỉ sửa nếu phát hiện lỗi.

### 4.3. Windows — lệnh kiểm tra ngắn

```powershell
ping 192.168.10.11
ping 192.168.10.12
ping 192.168.10.13
ping 192.168.10.128
```

### 4.4. NMS — hai dòng duy nhất

```powershell
cd D:\k1\MMT_NC\DoAn\nms-monitor
.\.venv\Scripts\python.exe web.py
```

**Dashboard:** http://localhost:5055/

### 4.5. Telegram

Mở chat bot NMS → xem tin khởi động/cảnh báo. **Không chạy bot bằng lệnh riêng**: `notifier.py` tự được NMS gọi.

---

## 5. KIỂM TRA DEMO NẾU MUỐN CHỨNG MINH TRƯỚC LỚP (KHÔNG BẮT BUỘC MỖI LẦN)

**Chỉ thực hiện trên máy ảo/GNS3 nhóm sở hữu và được phép cấu hình. Sau khi test phải phục hồi.**

### 5.1. Test sự cố dịch vụ Ubuntu HTTP

Mở **Ubuntu Terminal**:

```bash
sudo systemctl stop nginx
```

Windows NMS vẫn đang chạy. Khi đến vòng lấy mẫu kế tiếp, Dashboard sẽ báo lỗi **Ubuntu-HTTP** và **Ubuntu-HTTP-Port**; bot Telegram gửi cảnh báo riêng cho HTTP và TCP.

Khôi phục ngay:

```bash
sudo systemctl start nginx
```

Dashboard về 5/5, Telegram có tin **ĐÃ PHỤC HỒI DỊCH VỤ**.

### 5.2. Test R1 mất một interface (giữ SNMP hoạt động)

GNS3 → **R1 → Console**:

```cisco
enable
configure terminal
interface FastEthernet0/0
shutdown
end
show ip interface brief
```

Chờ NMS cập nhật: R1 vẫn reachable qua **FastEthernet1/0 quản lý**, nhưng FastEthernet0/0 hiện DOWN và Telegram cảnh báo.

Khôi phục:

```cisco
configure terminal
interface FastEthernet0/0
no shutdown
end
write memory
```

**KHÔNG tắt f1/0 để thử interface**, vì có thể cắt luôn đường SNMP và làm R1 chuyển Offline. Không tắt Router/Ubuntu đang phục vụ demo người khác.

### 5.3. Test RAM: không cần làm máy quá tải

Chỉ thử nếu thật cần minh chứng cảnh báo RAM:

1. Ghi nhớ ngưỡng gốc `ram: 85`.
2. Tạm đặt `ram: 60` **chỉ khi số liệu RAM hiện tại đã trên 60%**.
3. Khởi động lại `web.py` để đọc config mới.
4. Thấy tin cảnh báo.
5. Khôi phục `ram: 85`, khởi động lại `web.py`; khi dữ liệu RAM dưới ngưỡng này, hệ thống báo phục hồi.
6. Không để lại RAM 60% khi kết thúc bài.

**Không tạo tải bất thường để tăng RAM/CPU.** Đây chỉ là điều chỉnh ngưỡng cảnh báo thử nghiệm.

---

## 6. KHI MỞ LẠI MÀ HỆ THỐNG BỊ ĐỎ / KHÔNG CHẠY — SỬA TỪNG VẤN ĐỀ

### 6.1. Không thấy VMnet1 hoặc Windows không có 192.168.10.1

1. Mở **VMware Workstation** trên Windows.
2. Chọn **Edit → Virtual Network Editor** (có thể cần quyền admin).
3. Tìm **VMnet1**.
4. Kiểm tra **Host-only**, subnet **192.168.10.0**, mask **255.255.255.0**.
5. Kiểm tra Windows adapter **VMware Network Adapter VMnet1** đã bật và IP 192.168.10.1/24.
6. Mở lại PowerShell:

```powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.InterfaceAlias -like "*VMnet1*" } |
  Select-Object InterfaceAlias,IPAddress,PrefixLength
```

Nếu VMware không hiện VMnet1 hoặc bị xung đột, kiểm tra VMware Network Adapter trong Windows Network Connections. Không tự Reset toàn bộ virtual networks nếu đang có VM khác dùng chung cấu hình.

### 6.2. Ubuntu bị đổi IP, ens34 không có 192.168.10.128

Trong Ubuntu:

```bash
ip -br a
ip route
```

Nếu adapter Host-only bị DHCP đổi IP, mở **Settings → Network** trong Ubuntu, chọn đúng card **ens34 / Host-only** → IPv4 Manual:
- Address: `192.168.10.128`
- Netmask: `255.255.255.0`
- Gateway: để trống cho card Host-only này.
- DNS: có thể để trống cho ens34, NAT ens33 xử lý Internet.

Tắt/bật kết nối ens34 từ giao diện Network hoặc khởi động lại Ubuntu khi cấu hình đã lưu. **Không gán gateway mặc định thứ hai trên ens34**. Cần kiểm tra không trùng IP với VM khác.

### 6.3. Ubuntu SNMPD / SSH / Nginx không tự chạy

```bash
systemctl status snmpd --no-pager
systemctl status ssh --no-pager
systemctl status nginx --no-pager
```

Thử:

```bash
sudo systemctl restart snmpd ssh nginx
sudo systemctl enable snmpd ssh nginx
```

Nếu một service báo `Unit ... not found`, xác định đúng tên dịch vụ và package; không cài đè bừa. Với Ubuntu 22.04, các gói thường là `snmpd`, `openssh-server`, `nginx`.

Nếu Nginx bị lỗi cấu hình:

```bash
sudo nginx -t
sudo journalctl -u nginx -n 30 --no-pager
```

Nếu SNMPD lỗi:

```bash
sudo journalctl -u snmpd -n 30 --no-pager
sudo ss -lunp | grep ':161'
```

Nếu SSH lỗi:

```bash
sudo journalctl -u ssh -n 30 --no-pager
sudo ss -lntp | grep ':22'
```

### 6.4. Windows ping router không được nhưng router chấm xanh

Kiểm tra theo thứ tự:
1. R1/R2/R3 thực sự đã **Start** và `show ip interface brief` còn IP không?
2. R1/R2/R3 **f1/0** có up/up không? Có cắm Switch2 e0/e1/e2 không?
3. Switch2 e3 có nối đúng **Cloud1 VMnet1** không?
4. Windows VMnet1 có 192.168.10.1/24 không?
5. GNS3 Cloud có đúng adapter Windows **VMware Network Adapter VMnet1** không (không phải VMnet8)?
6. Nếu GNS3 hiện `port is not free` hoặc `Cannot modify a cloud that is already connected`, phải tháo link sai trước khi sửa — không nối trùng Cloud e3.

**Đừng sửa địa chỉ 192.168.10.11/12/13 khi giao diện đã đúng**.

### 6.5. Router mở lại nhưng IP, OSPF hoặc community SNMP bị mất

Chỉ xử lý nếu `show ip interface brief` chứng minh cấu hình đã không còn.

1. Kiểm tra đang mở **đúng project NMS-Monitor-Anh** chứ không phải tạo project trống mới.
2. Console Cisco:

```cisco
show startup-config
show running-config
```

3. Nếu startup-config có thông tin nhưng running-config không đúng, xác định vì sao NVRAM không nạp (không dùng `configure replace` hoặc erase ngẫu nhiên).
4. Nếu không có cấu hình đã lưu, xem hướng dẫn dựng đầy đủ trên **main/README.md** để khôi phục IP, OSPF, SNMP. Đây không phải tình huống khởi động bình thường.
5. Sau khi sửa, nhớ `write memory` từng router.

**Không lấy một file GNS3 .gns3 27KB làm bằng chứng chứa đầy đủ NVRAM**; topology JSON chủ yếu lưu thiết bị/liên kết. Portable project có thể có dữ liệu cấu hình đi kèm nhưng cần kiểm chứng sau import.

### 6.6. Terminal báo port 5055 bị chiếm hoặc "socket access forbidden"

Kiểm tra tiến trình nào đang nghe trên 5055 bằng **PowerShell Windows**:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 5055 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,OwningProcess
```

Lấy PID và xem chương trình:

```powershell
Get-Process -Id <PID>
```

Trong PowerShell, thay `<PID>` bằng **số PID thật** (không gõ nguyên dấu ngoặc nhọn/nhọn). Chỉ dừng tiến trình nếu xác định chính xác đây là NMS cũ của bạn. Nếu NMS cũ đang chạy và Dashboard có số liệu mới, **không mở bản thứ hai**.

Nếu web.py chạy nhưng trình duyệt không thấy gì, kiểm tra:

```powershell
Invoke-WebRequest http://127.0.0.1:5055/ -UseBasicParsing
```

Trình duyệt nên mở `http://localhost:5055/`, không phải cổng 5000 hay port 8765 của demo cũ.

**Lưu ý:** `web.py` có khóa chống chạy Monitor trùng, nhưng vẫn có thể phát sinh lỗi khi mở hai Flask cùng cổng; đừng chạy nhiều terminal.

### 6.7. Dashboard Ubuntu/R1/R2/R3 Online nhưng CPU/RAM hoặc interface không có dữ liệu

- Ping chỉ chứng minh ICMP; muốn có CPU/RAM phải hỏi SNMP thành công.
- Router cần community đúng, ACL cho phép **Windows `192.168.10.1`** (nếu có ACL).
- Ubuntu SNMPD cần listen ở **192.168.10.128:161** và SNMP view phải cho phép đọc các OID CPU/RAM/interface.

**Test bằng script NMS trên Windows mà không in community:**

```powershell
cd D:\k1\MMT_NC\DoAn\nms-monitor
.\.venv\Scripts\python.exe -c "import yaml; from snmp_lite import snmp_get; c=yaml.safe_load(open('config.yaml',encoding='utf-8-sig')); [(print(d['name'],snmp_get(d['ip'],d['snmp_community'],'1.3.6.1.2.1.1.5.0',port=d.get('port',161)))) for d in c.get('devices',[])]"
```

Mong đợi trả tên hostname cho từng router/Ubuntu. Nếu `None` hoặc timeout, kiểm tra trước `show snmp`, `show access-lists 10` và cấu hình cộng đồng **tại chính thiết bị**; không paste community thật lên GitHub/chat.

Nếu hostname trả được nhưng chỉ RAM CPU không có: cần so sánh OID phù hợp thiết bị, không tự giả dữ liệu. Trên Ubuntu xem `snmpd.conf` và view; trên router kiểm tra hỗ trợ enterprise MIB Cisco.

### 6.8. Telegram không có thông báo sau khi mở lại

1. Windows NMS phải vẫn chạy; Dashboard phải có số liệu mới.
2. Windows cần có Internet truy cập Telegram Bot API.
3. `config.yaml` phải có `notify.telegram.enabled: true`, token hợp lệ và chat_id đúng.
4. `chat_id` không phải username `@tên_bot` (lỗi cũ **403 can't send messages to the bot**).
5. Bạn đã bấm **Start** với bot hoặc chat bot còn khả năng gửi tin.
6. Không có cảnh báo khi mọi thứ bình thường là điều bình thường; NMS **không spam cùng lỗi**.

**Không công khai token để hỏi lỗi.** Nếu bot token đã bị lộ qua ảnh, vào BotFather thu hồi token và tạo token mới, cập nhật riêng ở config.yaml.

### 6.9. Dashboard hiển thị 5/5 nhưng Telegram không nhận cảnh báo hoặc cảnh báo cũ vẫn còn

NMS có file `state.json` lưu điều kiện lỗi để tránh spam. Các file lịch sử không bị xóa khi tắt máy. Một cảnh báo cũ trong mục lịch sử **không có nghĩa hệ thống đang lỗi ngay bây giờ**.

- Đánh giá **thời gian cập nhật**, trạng thái hiện tại và log mới.
- Kiểm thử thật phải tạo chu kỳ **bình thường → lỗi → khôi phục**.
- Không xóa `state.json` chỉ để ép gửi lại cảnh báo, vì có thể gây lặp thông báo.
- RAM 85% là ngưỡng vận hành; 60% là ngưỡng đã chỉnh tạm khi demo.

### 6.10. GNS3 thông báo thiếu IOS image sau khi import portable

Trên **máy cũ** ưu tiên mở project gốc: `D:\k1\MMT_NC\DoAn\GNS3\NMS-Monitor-Anh\NMS-Monitor-Anh.gns3`. File portable đã push lên GitHub dùng dự phòng. Nếu import từ GitHub sang **máy khác**, có thể cần template Cisco 3660 và IOS image hợp pháp phù hợp; vì GitHub không chứa IOS image. Không vì thế mà tạo blank project và nối lại từ đầu trên máy cũ.

### 6.11. Nếu phải phục hồi code từ GitHub

**Chỉ khi thư mục NMS trên ổ D bị mất**; không clone đè lên thư mục NMS đang chạy:

```powershell
cd D:\k1\MMT_NC
git clone -b nhanh-cua-may-tao https://github.com/anh632k-ui/MMTNC.git MMTNC_KhoiPhuc
cd .\MMTNC_KhoiPhuc\nms-monitor
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .\config.example.yaml .\config.yaml
```

Sau đó **khôi phục bằng tay** địa chỉ, community riêng, Bot Token/chat_id từ bản sao lưu an toàn trước khi chạy. File mẫu **không có** secrets thật. Điều chỉnh địa chỉ nếu môi trường VMware/GNS3 trên máy mới khác.

**Đừng dùng `git reset --hard` hoặc `git clean -fdx`** trên thư mục đồ án đang có config và lịch sử, tránh làm mất dữ liệu quan trọng.

---

## 7. CÁCH PHÂN BIỆT MỖI THÀNH PHẦN ĐANG CHẠY Ở MÁY NÀO

### 7.1. Trên Windows thật

- **GNS3:** chỉ là chương trình giả lập router và Cloud.
- **VMware:** chạy Ubuntu thật trong máy ảo.
- **Python NMS:** lấy dữ liệu cục bộ Windows bằng `psutil`, hỏi SNMP UDP 161 đến IP router/Ubuntu, ping ICMP, kiểm tra HTTP/TCP, gửi Telegram.
- **Dashboard Flask:** web `http://localhost:5055/` chỉ cần chạy `web.py`.
- **Mọi cấu hình thiết bị giám sát** đặt ở `D:\k1\MMT_NC\DoAn\nms-monitor\config.yaml`.

### 7.2. Trong Ubuntu VMware

- **Không cần copy/chạy NMS Python Windows sang Ubuntu để giám sát.**
- Ubuntu là **đối tượng được giám sát**.
- SNMPD đọc thông tin CPU/RAM/interface Ubuntu, trả yêu cầu UDP 161.
- Nginx cung cấp website HTTP 80.
- SSHD cung cấp kết nối TCP 22.
- Ubuntu có NAT `ens33` cho Internet và Host-only `ens34` cho NMS.
- Khi reboot, ba service có thể tự chạy nhờ `systemctl enable`.

### 7.3. Trong GNS3

- R1, R2, R3 là ba router Cisco 3660 giả lập.
- Trên mỗi router đã có IP 192.168.10.11/.12/.13 trên **FastEthernet1/0**.
- SNMP router trả CPU/RAM/interface/status/counters.
- Switch2–Cloud1–VMnet1 nối router đến Windows/Ubuntu.
- Không cần SSH vào router để NMS chạy nếu đã dùng SNMP.
- Không cần gõ lại các lệnh SNMP/OSPF nếu cấu hình NVRAM đã lưu.

### 7.4. Trên Telegram

- Bot Telegram **không phải chương trình chạy trên Ubuntu**.
- Bot hoạt động thông qua Telegram API; `notifier.py` trên **Windows** gửi HTTP request khi cần cảnh báo.
- Token và chat_id do **config.yaml trên Windows** quản lý.
- Chỉ mở Telegram để xem tin, không phải bật Telegram Web liên tục thì mới nhận được thông báo trên điện thoại.

---

## 8. CHẾ ĐỘ "CHẠY MƯỢT NHƯ HÔM NAY" — NGUYÊN TẮC CẦN GIỮ

1. **Không thay IP khi không cần**: Windows VMnet1 `.1`, Ubuntu `.128`, R1 `.11`, R2 `.12`, R3 `.13`.
2. **Không chuyển NMS sang WSL** khi WSL2 chưa có đường mạng VMnet1; Windows hiện chạy ổn nhất.
3. **Không mở hai NMS song song** từ hai terminal.
4. **Không chạy file demo HTTP 8765** khi Nginx cổng 80 đã thay thế.
5. **Không stop snmpd/ssh/nginx** sau khi demo mà quên start lại.
6. **Không giữ ngưỡng RAM 60%** sau test; ngưỡng chính là 85%.
7. **Không xóa lịch sử** chỉ vì còn sự kiện cũ; báo cáo cần lịch sử này.
8. **Không push token/community riêng** từ `config.yaml` lên GitHub.
9. **Không copy đè `.gns3project` lên project đang chạy** khi chỉ muốn khởi động lại.
10. Nếu GNS3/router thiếu cấu hình, **kiểm tra project/startup-config trước**, không paste các block cấu hình vào router một cách mù quáng.
11. **Ảnh màn hình sau khởi động:** chụp GNS3 router xanh, Ubuntu IP+service, Dashboard tổng quan, biểu đồ, HTTP/TCP 5/5, Telegram (che bí mật), báo cáo HTML.
12. **Chỉ trình bày điều thực sự giám sát:** Windows cục bộ, Ubuntu SNMP, R1/R2/R3 SNMP, ICMP, HTTP/TCP và Telegram. Slack đang tắt thì ghi là tính năng tùy chọn/chưa demo.

---

## 9. TÓM TẮT "TẮT HẾT RỒI BẬT LẠI" — PHIÊN BẢN DÁN GẦN BÀN MÁY

```text
TRƯỚC KHI TẮT HÔM NAY
  1) GNS3 R1/R2/R3 -> write memory
  2) GNS3 -> File > Save, sau đó Stop All Nodes
  3) Kiểm tra config.yaml + .venv vẫn còn, threshold RAM=85
  4) Windows Terminal web.py -> Ctrl+C
  5) Ubuntu -> Power Off đúng cách
  6) Windows -> Shut down

KHI BẬT LẠI
  1) Mở Windows -> PowerShell xem VMnet1 192.168.10.1
  2) Mở VMware Workstation -> Power On Ubuntu 64-bit
  3) Ubuntu Ctrl+Alt+T:
       ip -br a
       systemctl is-active snmpd ssh nginx
     Đảm bảo ens34=192.168.10.128
  4) Mở GNS3 -> Open Project NMS-Monitor-Anh -> Start
     Mở Console R1/R2/R3, "show ip interface brief"
     R1=.11, R2=.12, R3=.13, f1/0 up/up
  5) Trên Windows PowerShell:
       ping 192.168.10.11
       ping 192.168.10.12
       ping 192.168.10.13
       ping 192.168.10.128
  6) Mở VS Code -> Open Folder:
       D:\k1\MMT_NC\DoAn\nms-monitor
     Terminal POWERSHELL (không WSL):
       .\.venv\Scripts\python.exe web.py
  7) Mở trình duyệt:
       http://localhost:5055/
     Kiểm tra 7 thiết bị + 5/5 HTTP/TCP + biểu đồ mới
  8) Mở Telegram bot "mmt" kiểm tra
  9) Khi cần báo cáo:
       http://localhost:5055/report
       http://localhost:5055/report/download

KHÔNG CẦN:
  x Tạo lại router
  x Gán lại IP / SNMP / OSPF nếu vẫn lưu
  x Cài lại Ubuntu/Python/.venv mỗi lần
  x Chạy WSL / Mininet
  x Chạy demo_http_lab4.py hoặc router_sim.py
  x Chạy thêm monitor.py trong terminal khác
```

---

## 10. THÔNG TIN REPOSITORY / NHÁNH

- **Repository:** https://github.com/anh632k-ui/MMTNC
- **Nhánh code và hướng dẫn dựng từ đầu:** `main` — [README đầy đủ](https://github.com/anh632k-ui/MMTNC/blob/main/README.md).
- **Nhánh dành cho máy của Anh:** `nhanh-cua-may-tao` — README này, chuyên giải thích bật lại dự án **sau khi đã cài thành công**.
- **Nhánh Git kế thừa các file từ main:** nhánh này **không xóa code GNS3/Python**; chỉ viết README tập trung khởi động lại. Hai nhánh giữ nội dung README khác nhau.

**Điểm mấu chốt:** Cấu hình IOS đã `write memory`, Ubuntu services đã `enable`, IP VMnet1 vẫn giữ và file `config.yaml` trên Windows còn nguyên → **không phải cài lại hay cấu hình toàn bộ**. Chỉ bật đúng chương trình và chạy `.\.venv\Scripts\python.exe web.py` là tiếp tục giám sát như buổi demo 02/11/2026.
