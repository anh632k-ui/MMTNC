# MMTNC – NHẬT KÝ DỰNG HỆ THỐNG NMS MONITOR TỪ CON SỐ 0

> **Môn học:** Mạng máy tính nâng cao (MMTNC)  
> **Đề tài:** Hệ thống giám sát trạng thái thiết bị mạng và gửi cảnh báo qua Telegram/Slack  
> **Người thực hiện phần triển khai này:** Bùi Thế Anh – MSSV 1250080004  
> **Mốc triển khai/kiểm thử được ghi nhận:** 02/11/2026  
> **Repository:** https://github.com/anh632k-ui/MMTNC  
> **Phạm vi tài liệu:** Hướng dẫn dựng lại toàn bộ môi trường, lệnh thực hành, lỗi từng gặp, nguyên nhân và minh chứng; không chỉ là hướng dẫn chạy chương trình.

**Cách đọc:** Các mục **[ĐÃ KIỂM THỬ]** là thao tác/kết quả đã được xác nhận qua đầu ra và hình chụp trong quá trình thực hiện. Các mục **[DỰNG LẠI]** là cấu hình tái dựng để một thành viên khác có thể thiết lập hệ thống từ đầu; cần so với cấu hình đang lưu trong GNS3 vì không phải mọi lệnh lịch sử đều có bản ghi văn bản đầy đủ. Tuyệt đối không đưa token Telegram, SNMP community thực tế, mật khẩu hoặc khóa SSH lên GitHub Public.

---

## MỤC LỤC

1. [Kết quả cuối cùng và hệ thống giám sát gì](#1-kết-quả-cuối-cùng-và-hệ-thống-giám-sát-gì)
2. [Môi trường, công cụ và cấu trúc mã nguồn](#2-môi-trường-công-cụ-và-cấu-trúc-mã-nguồn)
3. [Giai đoạn 0 – Kiến trúc mạng và kế hoạch IP](#3-giai-đoạn-0--kiến-trúc-mạng-và-kế-hoạch-ip)
4. [Giai đoạn 1 – Tạo topology GNS3 từ đầu](#4-giai-đoạn-1--tạo-topology-gns3-từ-đầu)
5. [Giai đoạn 2 – Gán IP và định tuyến OSPF trên từng router](#5-giai-đoạn-2--gán-ip-và-định-tuyến-ospf-trên-từng-router)
6. [Giai đoạn 3 – Kết nối VMware/Windows và kiểm tra ping](#6-giai-đoạn-3--kết-nối-vmwarewindows-và-kiểm-tra-ping)
7. [Giai đoạn 4 – Cấu hình SNMP trên ba router Cisco](#7-giai-đoạn-4--cấu-hình-snmp-trên-ba-router-cisco)
8. [Giai đoạn 5 – Cấu hình SNMP trên Ubuntu VMware](#8-giai-đoạn-5--cấu-hình-snmp-trên-ubuntu-vmware)
9. [Giai đoạn 6 – Chuẩn bị dự án Python trên Windows](#9-giai-đoạn-6--chuẩn-bị-dự-án-python-trên-windows)
10. [Giai đoạn 7 – Kết nối Telegram và cấu hình cảnh báo](#10-giai-đoạn-7--kết-nối-telegram-và-cấu-hình-cảnh-báo)
11. [Giai đoạn 8 – Chạy Dashboard và giải thích từng thành phần](#11-giai-đoạn-8--chạy-dashboard-và-giải-thích-từng-thành-phần)
12. [Giai đoạn 9 – Tích hợp Lab 4 HTTP và Lab 5 TCP](#12-giai-đoạn-9--tích-hợp-lab-4-http-và-lab-5-tcp)
13. [Giai đoạn 10 – Thay HTTP demo bằng Nginx tự khởi động](#13-giai-đoạn-10--thay-http-demo-bằng-nginx-tự-khởi-động)
14. [Giai đoạn 11 – Kiểm thử toàn bộ tình huống và Telegram](#14-giai-đoạn-11--kiểm-thử-toàn-bộ-tình-huống-và-telegram)
15. [Giai đoạn 12 – Dashboard V2 và xuất báo cáo V3](#15-giai-đoạn-12--dashboard-v2-và-xuất-báo-cáo-v3)
16. [Giai đoạn 13 – Đưa Python và GNS3 lên GitHub](#16-giai-đoạn-13--đưa-python-và-gns3-lên-github)
17. [Khởi động lại toàn bộ hệ thống sau khi tắt máy](#17-khởi-động-lại-toàn-bộ-hệ-thống-sau-khi-tắt-máy)
18. [Bảng lỗi đã gặp và cách sửa](#18-bảng-lỗi-đã-gặp-và-cách-sửa)
19. [Giải thích cơ chế, giới hạn và câu hỏi thuyết trình](#19-giải-thích-cơ-chế-giới-hạn-và-câu-hỏi-thuyết-trình)
20. [Danh sách kiểm tra trước khi nộp](#20-danh-sách-kiểm-tra-trước-khi-nộp)

---

## 1. KẾT QUẢ CUỐI CÙNG VÀ HỆ THỐNG GIÁM SÁT GÌ

**[ĐÃ KIỂM THỬ]** Máy Windows thực làm trung tâm NMS, giám sát:

| Đối tượng | Địa chỉ / vị trí | Phương pháp | Thông số |
| --- | --- | --- | --- |
| Máy Windows thật | Máy chạy Python | psutil | CPU, RAM, card mạng, lưu lượng gửi/nhận |
| Ubuntu VMware | 192.168.10.128 | SNMP v2c + ICMP | CPU, RAM, ens33/ens34, RX/TX, RTT, tình trạng kết nối |
| Cisco R1 (GNS3) | 192.168.10.11 | SNMP v2c + ICMP | CPU, RAM, FastEthernet0/0, 0/1, 1/0, RX/TX, RTT |
| Cisco R2 (GNS3) | 192.168.10.12 | SNMP v2c + ICMP | Tương tự R1 |
| Cisco R3 (GNS3) | 192.168.10.13 | SNMP v2c + ICMP | Tương tự R1 |
| Google DNS | 8.8.8.8 | ICMP ping | Online, RTT, mất gói của mỗi lần đo |
| Cloudflare | 1.1.1.1 | ICMP ping | Online, RTT, mất gói của mỗi lần đo |
| NMS Dashboard | 127.0.0.1:5055 | HTTP + TCP | HTTP 200, độ trễ, cổng TCP 5055 |
| Ubuntu Nginx | 192.168.10.128:80 | HTTP + TCP | Website có phản hồi 200, chậm/lỗi, cổng 80 mở/đóng |
| Ubuntu SSH | 192.168.10.128:22 | TCP | Cổng SSH 22 có chấp nhận kết nối không |
| Telegram | Bot do nhóm quản lý | Telegram Bot API | Cảnh báo khi sự cố xuất hiện và thông báo khi khôi phục |

**Điều cần hiểu:** CPU/RAM router và Ubuntu lấy từ SNMP; CPU/RAM Windows lấy trực tiếp bằng psutil. ICMP ping không phải SNMP. HTTP và TCP là hai phép kiểm tra dịch vụ khác nhau. Slack có code trong notifier nhưng **chưa bật/không xác nhận đã demo**; không trình bày Slack đã chạy thật.

**[ĐÃ KIỂM THỬ]** Tình huống đã làm: cảnh báo RAM vượt ngưỡng, Nginx dừng/khởi động lại gây cảnh báo/khôi phục HTTP và TCP, router R1 FastEthernet0/0 DOWN rồi UP, Telegram và nhật ký Dashboard ghi đủ hai chiều.

---

## 2. MÔI TRƯỜNG, CÔNG CỤ VÀ CẤU TRÚC MÃ NGUỒN

### 2.1. Công cụ

- Windows 11: chạy GNS3, VMware Workstation, Visual Studio Code, PowerShell và ứng dụng NMS Python.
- GNS3: mô phỏng 3 router Cisco 3660 (Dynamips), switch Ethernet và Cloud.
- Cisco IOS do người thực hiện tự chuẩn bị hợp pháp. Topology trong repository tham chiếu image Cisco 3660 12.4(15)T14; **repository không nên phân phối IOS image**.
- VMware: Ubuntu Desktop, hai mạng NAT (VMnet8) và Host-only (VMnet1).
- Python + môi trường ảo .venv; các thư viện theo requirements.txt.
- Git/GitHub để bàn giao dự án; trình duyệt để mở Dashboard và Telegram Web.
- Bộ công cụ thực hành Buổi 5 (Mininet/WSL) là cơ sở tái sử dụng ý tưởng ICMP, HTTP, TCP, bắt gói, Dashboard. **Đồ án cuối dùng GNS3 + Ubuntu VMware thật**, không cần chạy Mininet mỗi lần demo.

### 2.2. Các đường dẫn đã dùng

~~~text
D:\k1\MMT_NC\DoAn\
├── GNS3\
│   └── NMS-Monitor-Anh\
├── nms-monitor\                 # BẢN CHẠY CHÍNH
├── Python\                      # bản thử SNMP/collector trước đó
├── BaoCao\
├── MinhChung\
└── VMware\

D:\k1\MMT_NC\GNS3_Export\
└── NMS-Monitor-Anh.gns3project

D:\k1\MMT_NC\MMTNC_Push_NMS\   # thư mục clone GitHub dùng để push
~~~

**Phân biệt:** Thư mục Python cũ, WSL Buổi 5 và nms-monitor là các giai đoạn/bộ code khác nhau. Chương trình NMS chính trên Windows chạy từ <code>nms-monitor</code>; không đặt nhầm lệnh tại <code>DoAn</code>.

### 2.3. Cấu trúc trên GitHub

~~~text
MMTNC/
├── Python/                         # mã nguồn giai đoạn đầu
├── GNS3/
│   ├── NMS-Monitor-Anh.gns3
│   └── NMS-Monitor-Anh.gns3project
├── nms-monitor/
│   ├── collector.py                 # số liệu cục bộ Windows và ping
│   ├── monitor.py                   # vòng giám sát, ngưỡng, lịch sử, cảnh báo
│   ├── notifier.py                  # Telegram / Slack
│   ├── snmp_lite.py                 # giao tiếp SNMP v2c
│   ├── snmp_utils.py                # OID Cisco/Ubuntu và interface
│   ├── service_checks.py            # HTTP và TCP
│   ├── web.py                       # Flask Dashboard/API
│   ├── nms_report.py                # báo cáo HTML + biểu đồ SVG
│   ├── demo_http_lab4.py            # web demo tùy chọn
│   ├── router_sim.py                # router mô phỏng bằng Python, không cần khi đã có GNS3
│   ├── requirements.txt
│   └── config.example.yaml         # chỉ chứa placeholder
├── .gitignore
└── README.md                        # tài liệu này
~~~

Những file sinh lúc chạy (không push): <code>config.yaml</code>, <code>state.json</code>, <code>nms_alerts.jsonl</code>, <code>nms_history.jsonl</code>, <code>nms_services.jsonl</code>, <code>.nms-monitor.lock</code>, <code>.venv/</code> và <code>__pycache__/</code>.

---

## 3. GIAI ĐOẠN 0 – KIẾN TRÚC MẠNG VÀ KẾ HOẠCH IP

### 3.1. Sơ đồ vật lý/logical

~~~text
                     R1
                 /   |   \
                /    |    \
              R2-----+-----R3          <- 3 kết nối router-router
               \     |     /
                \    |    /
                  Switch2
                     |
                   Cloud1
                     |
              Windows VMnet1
                  192.168.10.1
                     |
        ┌────────────┴────────────┐
        |                         |
  Windows chạy NMS          Ubuntu VMware (ens34)
  python web.py             192.168.10.128
                            SNMP 161 / SSH 22 / Nginx 80
~~~

Ba cổng quản lý của R1, R2, R3 cùng cắm Switch2 và đi qua Cloud1 gắn với **VMware Network Adapter VMnet1**. Switch2 e3 chỉ nối **một lần** sang Cloud1. Không cần hai đường VMnet1; không gán trực tiếp IP cho Ethernet switch mặc định của GNS3.

### 3.2. Bảng IP đã sử dụng

| Thiết bị | Interface | IP | Kết nối |
| --- | --- | --- | --- |
| R1 | FastEthernet0/0 | 10.0.12.1 | R2 f0/0 |
| R2 | FastEthernet0/0 | 10.0.12.2 | R1 f0/0 |
| R1 | FastEthernet0/1 | 10.0.13.1 | R3 f0/0 |
| R3 | FastEthernet0/0 | 10.0.13.2 | R1 f0/1 |
| R2 | FastEthernet0/1 | 10.0.23.1 | R3 f0/1 |
| R3 | FastEthernet0/1 | 10.0.23.2 | R2 f0/1 |
| R1 | FastEthernet1/0 | 192.168.10.11 | Switch2 e0 |
| R2 | FastEthernet1/0 | 192.168.10.12 | Switch2 e1 |
| R3 | FastEthernet1/0 | 192.168.10.13 | Switch2 e2 |
| Cloud1 | VMnet1 | Cầu nối L2 | Switch2 e3 |
| Windows VMnet1 | Adapter host-only | 192.168.10.1/24 | NMS |
| Ubuntu ens34 | Host-only VMnet1 | 192.168.10.128/24 | Thiết bị Ubuntu |
| Ubuntu ens33 | NAT VMnet8 | 192.168.126.x/24 (địa chỉ theo DHCP) | Internet/cài package |

**[ĐÃ XÁC NHẬN]** Tên cổng và IP trên R1/R2/R3 đã có đầu ra <code>show ip interface brief</code>; VMnet1 Windows là <code>192.168.10.1/24</code>; Ubuntu ens34 là <code>192.168.10.128/24</code> trong phiên chạy.  
**[DỰNG LẠI]** Các liên kết 10.0.12.x, 10.0.13.x và 10.0.23.x có thể dùng subnet /30 (255.255.255.252) theo các cặp IP đã chọn. Nếu project gốc lưu mặt nạ khác, ưu tiên kiểm tra bằng <code>show running-config</code>.

---

## 4. GIAI ĐOẠN 1 – TẠO TOPOLOGY GNS3 TỪ ĐẦU

### Bước 4.1 – Tạo project

1. Mở GNS3 trên Windows → **File → New blank project**.
2. Đặt tên **NMS-Monitor-Anh**; ưu tiên lưu trên ổ D, ví dụ <code>D:\k1\MMT_NC\DoAn\GNS3</code>.
3. Chuẩn bị template router Cisco 3660 (thiết bị Dynamips đã có sẵn trên máy triển khai).
4. Trong bản topology trên GitHub, router dùng chassis 3660, slot0 có 2 FastEthernet, slot1 có 1 FastEthernet; cần đủ ba cổng <code>f0/0</code>, <code>f0/1</code>, <code>f1/0</code>.

### Bước 4.2 – Kéo thiết bị ra canvas

Kéo 3 router, đổi tên thành R1, R2, R3; kéo **Ethernet switch**, đổi tên Switch2; kéo **Cloud**, đổi tên Cloud1. Với template Ethernet switch GNS3, switch này hoạt động như switch Ethernet đơn giản, không phải IOS switch cấu hình qua console.

### Bước 4.3 – Nối đúng từng cổng

Chọn biểu tượng **Add a Link** (hình dây nối), nhấp thiết bị đầu và cổng, rồi thiết bị đích và cổng:

~~~text
R1 f0/0   <--> R2 f0/0
R1 f0/1   <--> R3 f0/0
R2 f0/1   <--> R3 f0/1

R1 f1/0   <--> Switch2 e0
R2 f1/0   <--> Switch2 e1
R3 f1/0   <--> Switch2 e2

Switch2 e3 <--> Cloud1: VMware Network Adapter VMnet1
~~~

Đây là bảng kết nối **đã đối chiếu trực tiếp file GNS3 trên repository**.

### Bước 4.4 – Cấu hình Cloud1 đúng

- Nhấp phải **Cloud1 → Configure**.
- Chọn adapter **VMware Network Adapter VMnet1** (Host-only), thêm vào Ethernet interfaces/ports nếu chưa hiện.
- Nhấn **Apply/OK** khi chưa có đường nối đến Cloud.
- Chỉ nối **một** cổng Switch2 e3 đến VMnet1. Không gán cùng cổng e3 hai lần.
- Nếu GNS3 báo **Cannot modify a cloud that is already connected**, hãy xóa đường link Cloud–Switch trước rồi sửa Cloud, sau đó nối lại.
- Nếu báo **Cannot connect to itself**, bạn đã chọn hai đầu nối cùng một node hoặc thao tác link sai.
- Nếu báo **destination port is not free**, chọn cổng còn trống, không đè lên link đang tồn tại.
- Nếu báo link ID không tồn tại, đóng/mở project hoặc xóa các link hỏng để tạo lại; không cố tiếp tục trên cổng lỗi.

### Bước 4.5 – Chạy thiết bị

Nhấn nút **Start/Play** màu xanh trong GNS3; chờ R1, R2, R3 khởi động (chấm xanh). Nhấp phải **R1 → Console** để mở cửa sổ Cisco CLI (R2, R3 làm tương tự).

Lưu topology qua **File → Save**. Cấu hình IOS của mỗi router cần lưu riêng bằng <code>write memory</code>.

---

## 5. GIAI ĐOẠN 2 – GÁN IP VÀ ĐỊNH TUYẾN OSPF TRÊN TỪNG ROUTER

> **[DỰNG LẠI theo IP/topology đã được kiểm tra]** Các khối lệnh dưới đây giúp cấu hình từ một router trống. Các địa chỉ interface đã xác minh; phần network mask /30 và OSPF nên đối chiếu với <code>show running-config</code> của project portable khi tái sử dụng. Trước khi dán, nhìn prompt: <code>R1&gt;</code>, <code>R1#</code>, <code>R1(config)#</code>, <code>R1(config-if)#</code> tương ứng các chế độ khác nhau.

### Bước 5.1 – Mở Console R1, gán ba địa chỉ

~~~cisco
enable
configure terminal
hostname R1

interface FastEthernet0/0
description LINK-R1-R2
ip address 10.0.12.1 255.255.255.252
no shutdown
exit

interface FastEthernet0/1
description LINK-R1-R3
ip address 10.0.13.1 255.255.255.252
no shutdown
exit

interface FastEthernet1/0
description MANAGEMENT-VMNET1
ip address 192.168.10.11 255.255.255.0
no shutdown
exit

end
write memory
show ip interface brief
~~~

Đầu ra cần thấy địa chỉ <code>10.0.12.1</code>, <code>10.0.13.1</code>, <code>192.168.10.11</code> và trạng thái các cổng nối là <code>up/up</code> sau khi peer đã bật.

### Bước 5.2 – Mở Console R2, gán ba địa chỉ

~~~cisco
enable
configure terminal
hostname R2

interface FastEthernet0/0
description LINK-R2-R1
ip address 10.0.12.2 255.255.255.252
no shutdown
exit

interface FastEthernet0/1
description LINK-R2-R3
ip address 10.0.23.1 255.255.255.252
no shutdown
exit

interface FastEthernet1/0
description MANAGEMENT-VMNET1
ip address 192.168.10.12 255.255.255.0
no shutdown
exit

end
write memory
show ip interface brief
~~~

### Bước 5.3 – Mở Console R3, gán ba địa chỉ

~~~cisco
enable
configure terminal
hostname R3

interface FastEthernet0/0
description LINK-R3-R1
ip address 10.0.13.2 255.255.255.252
no shutdown
exit

interface FastEthernet0/1
description LINK-R3-R2
ip address 10.0.23.2 255.255.255.252
no shutdown
exit

interface FastEthernet1/0
description MANAGEMENT-VMNET1
ip address 192.168.10.13 255.255.255.0
no shutdown
exit

end
write memory
show ip interface brief
~~~

### Bước 5.4 – Kiểm tra trực tiếp hai đầu link

Console R1:

~~~cisco
ping 10.0.12.2
ping 10.0.13.2
~~~

Console R2:

~~~cisco
ping 10.0.12.1
ping 10.0.23.2
~~~

Console R3:

~~~cisco
ping 10.0.13.1
ping 10.0.23.1
~~~

Lần ping đầu có thể chưa đạt 5/5 vì ARP đang học MAC, sau đó thử lại. **[ĐÃ KIỂM THỬ]** Trước đây R1 ping <code>10.0.12.2</code> đạt 4/5 (80%) rồi liên kết hoạt động.

### Bước 5.5 – Cấu hình OSPF (phục dựng để demo đường đi)

Trên R1:

~~~cisco
configure terminal
router ospf 1
network 10.0.12.0 0.0.0.3 area 0
network 10.0.13.0 0.0.0.3 area 0
network 192.168.10.0 0.0.0.255 area 0
end
write memory
show ip ospf neighbor
~~~

Trên R2:

~~~cisco
configure terminal
router ospf 1
network 10.0.12.0 0.0.0.3 area 0
network 10.0.23.0 0.0.0.3 area 0
network 192.168.10.0 0.0.0.255 area 0
end
write memory
show ip ospf neighbor
~~~

Trên R3:

~~~cisco
configure terminal
router ospf 1
network 10.0.13.0 0.0.0.3 area 0
network 10.0.23.0 0.0.0.3 area 0
network 192.168.10.0 0.0.0.255 area 0
end
write memory
show ip ospf neighbor
~~~

Kiểm tra thêm:

~~~cisco
show ip route
show running-config | section router ospf
show ip ospf neighbor
~~~

**[ĐÃ QUAN SÁT]** Console R1 từng xuất hiện neighbor <code>192.168.10.12</code> và <code>192.168.10.13</code>, rồi log OSPF chuyển neighbor sang FULL. OSPF là phần minh họa định tuyến của topology; SNMP quản lý ba IP <code>192.168.10.11–13</code> không phụ thuộc hoàn toàn vào OSPF vì chúng nằm chung mạng quản lý.

---

## 6. GIAI ĐOẠN 3 – KẾT NỐI VMWARE/WINDOWS VÀ KIỂM TRA PING

### Bước 6.1 – Windows phải có VMnet1

Windows PowerShell:

~~~powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.InterfaceAlias -like "*VMnet1*" } |
  Select-Object InterfaceAlias,IPAddress,PrefixLength
~~~

**[ĐÃ KIỂM THỬ]** Kết quả đã có: <code>VMware Network Adapter VMnet1 192.168.10.1 /24</code>. Nếu không có: mở VMware Virtual Network Editor, kiểm tra VMnet1 là **Host-only**, subnet <code>192.168.10.0/24</code>. Tránh trùng subnet với Wi-Fi hoặc VPN khác.

### Bước 6.2 – Cấu hình card mạng Ubuntu VMware

Trong VMware: **VM → Settings → Network Adapter**:

- Adapter 1: **NAT / VMnet8** để Ubuntu có Internet.
- Adapter 2: **Host-only / VMnet1** để Ubuntu cùng mạng với GNS3/Windows.

Mở Ubuntu Terminal:

~~~bash
ip -br a
ip route
~~~

**[ĐÃ KIỂM THỬ]** Ubuntu có <code>ens33</code> NAT và <code>ens34</code> Host-only; <code>ens34 = 192.168.10.128/24</code>. Nếu IP chưa đúng, thiết lập qua Ubuntu Settings → Network → card Host-only → IPv4 Manual <code>192.168.10.128/24</code>, không đặt gateway mặc định thứ hai cho ens34. Phần NAT ens33 giữ DHCP.

### Bước 6.3 – Ping từ Windows

~~~powershell
ping 192.168.10.11
ping 192.168.10.12
ping 192.168.10.13
ping 192.168.10.128
~~~

**[ĐÃ KIỂM THỬ]** Windows đã ping đủ 3 router, 4/4 gói nhận cho từng router; Ubuntu cũng ping tới ba router thành công. Trước đó chạy ping từ WSL bị 100% packet loss do WSL2 đi qua mạng ảo riêng <code>172.21.x.x</code>; **đó là lý do chuyển NMS chính sang PowerShell Windows**, không phải đổi IP router.

### Bước 6.4 – Ping từ Ubuntu

~~~bash
ping -c 3 192.168.10.11
ping -c 3 192.168.10.12
ping -c 3 192.168.10.13
~~~

Kỳ vọng 3 received, 0% packet loss. Nếu không được: kiểm tra ens34, VMnet1 và Cloud1 trước khi đụng code Python.

---

## 7. GIAI ĐOẠN 4 – CẤU HÌNH SNMP TRÊN BA ROUTER CISCO

### Bước 7.1 – Hiểu Community và ACL

- SNMP v2c dùng **community string**: máy NMS phải gửi cùng giá trị mà router đang cấu hình.
- <code>RO</code> là Read Only (chỉ đọc), không cho ghi cấu hình.
- ACL 10 có nhiệm vụ chỉ cho những IP quản trị được phép hỏi SNMP.
- **Không dùng community ba ký tự cho hệ thống công khai**. Trong phòng lab riêng có thể đã dùng community ngắn để thử, nhưng bản bàn giao phải dùng giá trị do nhóm tự chọn và giữ ngoài repository.
- Dùng một community thống nhất giữa router và <code>config.yaml</code>, hoặc khai báo riêng từng router nếu cần.

### Bước 7.2 – Cấu hình cho R1

Ví dụ dưới đây dùng chữ thay thế <code>COMMUNITY_RIENG</code> — **tự thay bằng chuỗi riêng**. Cho phép Windows NMS <code>192.168.10.1</code> và máy Ubuntu quản trị <code>192.168.10.128</code> để tiện kiểm tra:

~~~cisco
enable
configure terminal
access-list 10 permit 192.168.10.1
access-list 10 permit 192.168.10.128
snmp-server community COMMUNITY_RIENG RO 10
end
write memory
show access-lists 10
show running-config | include snmp-server
show snmp
~~~

Nếu có community cũ muốn thay, phải xác định **đúng giá trị cũ** trước rồi ở chế độ config dùng <code>no snmp-server community TEN_CU</code>, sau đó thêm community mới. **Không paste nguyên các chữ ví dụ** như <code>TEN_COMMUNITY_RIENG</code> vào router, vì Cisco sẽ coi đó là community thật.

Nếu chỉ dùng Windows chạy NMS, ACL phải cho phép **Windows 192.168.10.1**. Trong quá trình làm đã từng chỉ permit <code>192.168.10.128</code> cho Ubuntu kiểm tra SNMP; cấu hình ACL như vậy có thể chặn Windows. Hai IP trên giúp cả hai máy kiểm thử được trong mạng Host-only.

### Bước 7.3 – Làm tương tự trên R2 và R3

Mở Console R2:

~~~cisco
enable
configure terminal
access-list 10 permit 192.168.10.1
access-list 10 permit 192.168.10.128
snmp-server community COMMUNITY_RIENG RO 10
end
write memory
show snmp
~~~

Mở Console R3:

~~~cisco
enable
configure terminal
access-list 10 permit 192.168.10.1
access-list 10 permit 192.168.10.128
snmp-server community COMMUNITY_RIENG RO 10
end
write memory
show snmp
~~~

*Ghi chú:* Nếu Router đã có ACL 10 hoặc SNMP cấu hình khác, kiểm tra <code>show running-config</code> để tránh thêm trùng/lệch trước khi thay. SNMP v2c không mã hóa community; chỉ sử dụng trên mạng lab riêng.

### Bước 7.4 – Kiểm thử SNMP từ Ubuntu

Ubuntu Terminal:

~~~bash
sudo apt update
sudo apt install -y snmp
read -rsp "SNMP Community: " SNMP_COMMUNITY; echo

snmpget -v2c -c "$SNMP_COMMUNITY" 192.168.10.11 1.3.6.1.2.1.1.5.0
snmpget -v2c -c "$SNMP_COMMUNITY" 192.168.10.12 1.3.6.1.2.1.1.5.0
snmpget -v2c -c "$SNMP_COMMUNITY" 192.168.10.13 1.3.6.1.2.1.1.5.0
~~~

**[ĐÃ KIỂM THỬ]** Đầu ra thực tế tương ứng <code>STRING: "R1"</code>, <code>"R2"</code>, <code>"R3"</code>.

### Bước 7.5 – Lấy tên interface và ifIndex

~~~bash
for ip in 192.168.10.11 192.168.10.12 192.168.10.13; do
    echo "========== ROUTER $ip =========="
    echo "--- TEN INTERFACE ---"
    snmpwalk -v2c -c "$SNMP_COMMUNITY" -On "$ip" 1.3.6.1.2.1.2.2.1.2
    echo "--- TRANG THAI INTERFACE ---"
    snmpwalk -v2c -c "$SNMP_COMMUNITY" -On "$ip" 1.3.6.1.2.1.2.2.1.8
done
~~~

**[ĐÃ KIỂM THỬ]** Cả ba router có: ifIndex **1 = FastEthernet0/0**, **2 = FastEthernet0/1**, **3 = FastEthernet1/0**, **5 = Null0**. Giá trị <code>ifOperStatus = 1</code> là UP; <code>2</code> là DOWN. Vì vậy trong YAML dùng <code>interfaces: [1, 2, 3]</code>, không cần theo dõi Null0.

### Bước 7.6 – Một số lệnh xác nhận khác

~~~bash
snmpget -v2c -c "$SNMP_COMMUNITY" 192.168.10.11 1.3.6.1.4.1.9.9.109.1.1.1.1.7.1
snmpget -v2c -c "$SNMP_COMMUNITY" 192.168.10.11 1.3.6.1.4.1.9.9.48.1.1.1.5.1
snmpget -v2c -c "$SNMP_COMMUNITY" 192.168.10.11 1.3.6.1.4.1.9.9.48.1.1.1.6.1
~~~

Theo thứ tự đây là OID CPU Cisco, bộ nhớ đã dùng và bộ nhớ còn trống. Giá trị có thể thay đổi theo thiết bị/IOS; không nên mặc định mọi IOS hỗ trợ mọi OID. Nếu OID không có dữ liệu, giao diện nên hiển thị không có dữ liệu, không được tự giả số liệu.

---

## 8. GIAI ĐOẠN 5 – CẤU HÌNH SNMP TRÊN UBUNTU VMWARE

### Bước 8.1 – Cài SNMP và snmpd

~~~bash
sudo apt update
sudo apt install -y snmp snmpd
sudo systemctl status snmpd --no-pager
~~~

### Bước 8.2 – Sửa snmpd.conf

~~~bash
sudo cp /etc/snmp/snmpd.conf /etc/snmp/snmpd.conf.bak
sudo nano /etc/snmp/snmpd.conf
~~~

Trong file, kiểm tra/điều chỉnh các mục tương đương:

~~~conf
agentAddress udp:127.0.0.1:161,udp:192.168.10.128:161
rocommunity COMMUNITY_RIENG 192.168.10.0/24 -V systemonly
~~~

**Quan trọng:** Đây là **ví dụ cú pháp cần điều chỉnh**, không phải toàn bộ file cấu hình đã dùng. Trong quá trình triển khai, cấu hình Ubuntu thực tế dùng một view đọc được cả các OID cần cho CPU/RAM/interface (ví dụ <code>labview</code>). Nếu dùng <code>-V systemonly</code> mà view bị giới hạn vào nhánh system, CPU/RAM và interface sẽ không đọc được. Phải xác nhận view chứa các OID yêu cầu hoặc cấu hình view đúng như bên dưới:

~~~conf
view labview included .1
rocommunity COMMUNITY_RIENG 192.168.10.0/24 -V labview
~~~

Không để **hai dòng rocommunity trùng community** với view mâu thuẫn; chọn cách cấu hình phù hợp. Giới hạn nguồn về mạng Host-only, không mở agent SNMP ra Internet.

Lưu file Nano: **Ctrl + O**, Enter, **Ctrl + X**. Khởi động lại:

~~~bash
sudo systemctl restart snmpd
sudo systemctl enable snmpd
sudo ss -lunp | grep ':161'
~~~

**[ĐÃ KIỂM THỬ]** snmpd lắng nghe <code>127.0.0.1:161</code> và <code>192.168.10.128:161</code>.

### Bước 8.3 – Test hostname, CPU/RAM Ubuntu

~~~bash
read -rsp "SNMP Community: " SNMP_COMMUNITY; echo
snmpget -v2c -c "$SNMP_COMMUNITY" 192.168.10.128 1.3.6.1.2.1.1.5.0

# CPU idle
snmpget -v2c -c "$SNMP_COMMUNITY" 192.168.10.128 1.3.6.1.4.1.2021.11.11.0

# RAM total/free/buffer/cache
snmpget -v2c -c "$SNMP_COMMUNITY" 192.168.10.128 \
  1.3.6.1.4.1.2021.4.5.0 \
  1.3.6.1.4.1.2021.4.6.0 \
  1.3.6.1.4.1.2021.4.14.0 \
  1.3.6.1.4.1.2021.4.15.0
~~~

**[ĐÃ KIỂM THỬ]** Các OID CPU idle và memory trên Ubuntu đã trả giá trị. Phần code <code>snmp_utils.py</code> lấy CPU (%) = 100 - CPU idle; RAM (%) = (total - free - buffers - cached)/total × 100, có giới hạn về 0–100%. Nhiệt độ trả <code>None</code> nếu không có OID/cảm biến tương ứng.

### Bước 8.4 – Lấy ifIndex của Ubuntu

~~~bash
snmpwalk -v2c -c "$SNMP_COMMUNITY" -On 192.168.10.128 1.3.6.1.2.1.2.2.1.2
~~~

**[ĐÃ KIỂM THỬ]** <code>1 = lo</code>, <code>2 = ens33</code>, <code>3 = ens34</code>. Vì vậy cấu hình NMS theo dõi Ubuntu <code>interfaces: [2, 3]</code>.

---

## 9. GIAI ĐOẠN 6 – CHUẨN BỊ DỰ ÁN PYTHON TRÊN WINDOWS

### Bước 9.1 – Mở mã nguồn

Mở Visual Studio Code → **File → Open Folder**:

~~~text
D:\k1\MMT_NC\DoAn\nms-monitor
~~~

Hoặc nếu máy thành viên lấy từ GitHub, mở thư mục <code>MMTNC\nms-monitor</code> trong clone.

Trong VS Code: **Terminal → New Terminal → PowerShell**. Xem prompt có đúng đường dẫn trên.

### Bước 9.2 – Tạo .venv (chỉ lần đầu)

~~~powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

**[ĐÃ KIỂM THỬ]** Các package đã cài thành công: psutil, pyyaml, requests, flask và phụ thuộc. VS Code chọn interpreter tại <code>nms-monitor\.venv\Scripts\python.exe</code> qua **Python: Select Interpreter → Enter interpreter path** nếu chưa tự nhận.

Nếu đã có .venv hợp lệ thì không cần tạo lại. Nếu PowerShell chặn activate, không cần sửa policy toàn hệ thống; chạy trực tiếp:

~~~powershell
.\.venv\Scripts\python.exe web.py
~~~

Hoặc bật venv trong terminal nếu được:

~~~powershell
.\.venv\Scripts\Activate.ps1
python web.py
~~~

### Bước 9.3 – Tạo config.yaml từ file mẫu

~~~powershell
Copy-Item .\config.example.yaml .\config.yaml
~~~

Mở <code>config.yaml</code> và thay các placeholder bằng giá trị **chỉ lưu trên máy của nhóm**. Ví dụ cấu trúc:

~~~yaml
interval: 10
interfaces: []
targets:
  - {name: Google DNS, host: 8.8.8.8}
  - {name: Cloudflare, host: 1.1.1.1}

thresholds:
  cpu: 80
  ram: 85
  temp: 70

notify:
  telegram:
    enabled: false
    token: "DIEN_TOKEN_RIENG"
    chat_id: "DIEN_CHAT_ID_SO"
  slack:
    enabled: false
    webhook: "DIEN_WEBHOOK_NEU_DUNG"

devices:
  - name: R1
    ip: 192.168.10.11
    snmp_community: "COMMUNITY_RIENG"
    interfaces: [1, 2, 3]
  - name: R2
    ip: 192.168.10.12
    snmp_community: "COMMUNITY_RIENG"
    interfaces: [1, 2, 3]
  - name: R3
    ip: 192.168.10.13
    snmp_community: "COMMUNITY_RIENG"
    interfaces: [1, 2, 3]
  - name: Ubuntu-VM
    ip: 192.168.10.128
    snmp_community: "COMMUNITY_RIENG"
    interfaces: [2, 3]

services:
  http:
    - name: NMS-Dashboard-HTTP
      url: http://127.0.0.1:5055/
      expected_status: 200
      max_response_seconds: 3
      timeout: 6
    - name: Ubuntu-HTTP
      url: http://192.168.10.128/
      expected_status: 200
      max_response_seconds: 3
      timeout: 6
  tcp:
    - name: NMS-Dashboard-TCP
      host: 127.0.0.1
      port: 5055
      timeout: 2
    - name: Ubuntu-SSH
      host: 192.168.10.128
      port: 22
      timeout: 2
    - name: Ubuntu-HTTP-Port
      host: 192.168.10.128
      port: 80
      timeout: 2
~~~

Lưu ý: chỉ có **một** mục <code>services:</code> và **một** mục <code>devices:</code>; thụt lề YAML bằng spaces, không dùng tab. Giai đoạn đầu từng có <code>devices: []</code> rồi bổ sung R1/R2/R3/Ubuntu khi SNMP hoạt động. Khi hoàn tất mới bật Telegram.

### Bước 9.4 – Vì sao không chạy app trong WSL?

Lúc đầu code được thử qua WSL Ubuntu với <code>ip route get 192.168.100.11</code> và ping không thành công; WSL đang có <code>eth0=172.21.x.x</code>, không cùng đường mạng Host-only VMnet1. Sau khi chuyển chạy Python trên Windows, Windows <code>192.168.10.1</code> ping router được. **Không cần chuyển cả NMS sang Ubuntu VMware**: Ubuntu là máy được giám sát; Windows là máy giám sát. Các lệnh Ubuntu Terminal chỉ để cấu hình/test thiết bị Ubuntu.

---

## 10. GIAI ĐOẠN 7 – KẾT NỐI TELEGRAM VÀ CẤU HÌNH CẢNH BÁO

### Bước 10.1 – Tạo bot

1. Mở Telegram, tìm tài khoản có xác minh **@BotFather**.
2. Gửi <code>/start</code>, sau đó <code>/newbot</code>.
3. Nhập tên hiển thị và username bot kết thúc bằng <code>bot</code>.
4. BotFather trả một **Bot Token bí mật**. Không chia sẻ token qua ảnh hoặc commit Git.
5. Mở chat **với bot vừa tạo** (không phải BotFather), bấm **Start** hoặc gửi <code>/start</code>.

### Bước 10.2 – Lấy chat_id đúng

- <code>@ten_bot</code> là username, **không phải chat ID**.
- Chat ID của cuộc trò chuyện cá nhân thường là số nguyên; nhóm có thể có ID âm.
- Nếu ghi <code>chat_id: "@ten_bot"</code>, Telegram sẽ báo <code>403 Forbidden: the bot can't send messages to the bot</code>. Đây là lỗi đã gặp.

Sau khi gửi <code>/start</code> cho bot, có thể mở API <code>getUpdates</code> bằng công cụ thử API của bạn hoặc đoạn PowerShell sau (chỉ chạy trên máy riêng, không chia sẻ output có token):

~~~powershell
$token = Read-Host "Nhap Telegram Bot Token"
$reply = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getUpdates"
$reply.result | Select-Object -Last 5 | ConvertTo-Json -Depth 12
~~~

Tìm <code>message.chat.id</code>. Nếu API chưa có update, gửi một tin mới tới bot rồi chạy lại. Với bot dùng webhook, getUpdates có thể không trả lịch sử như mong đợi; khi đó kiểm tra cấu hình webhook trước.

### Bước 10.3 – Bật Telegram trong config.yaml

~~~yaml
notify:
  telegram:
    enabled: true
    token: "TOKEN_THAT_CHI_LUU_TREN_MAY"
    chat_id: "CHAT_ID_DUNG"
  slack:
    enabled: false
    webhook: "DIEN_NEU_CAN"
~~~

### Bước 10.4 – Kiểm tra

Khi chạy NMS, bot gửi thông báo <code>NMS Monitor đã khởi động</code>. **[ĐÃ KIỂM THỬ]** Bot đã nhận được thông báo kết nối, cảnh báo và khôi phục. Nếu thay token, phải thay đúng trong config.yaml trên máy đang chạy, không dùng token bị thu hồi.

**Bảo mật:** Token cũ từng xuất hiện trên ảnh. Nên **revoke và tạo token mới** trong BotFather; không đăng file config.yaml lên GitHub, không chụp ảnh làm lộ token.

---

## 11. GIAI ĐOẠN 8 – CHẠY DASHBOARD VÀ GIẢI THÍCH TỪNG THÀNH PHẦN

### Bước 11.1 – Lệnh chạy ngắn

Tại Terminal PowerShell đang đứng trong <code>nms-monitor</code> với venv hoạt động:

~~~powershell
python web.py
~~~

Nếu chưa activate:

~~~powershell
.\.venv\Scripts\python.exe web.py
~~~

Có thể chỉ rõ host/port:

~~~powershell
python web.py --host 127.0.0.1 --port 5055
~~~

Mở trình duyệt: **http://127.0.0.1:5055/** hoặc **http://localhost:5055/**.

**Chỉ chạy một chương trình chính**. <code>web.py</code> tự khởi động vòng giám sát nền trong cùng tiến trình. Không mở thêm <code>python monitor.py</code> cùng thư mục vì có thể trùng hoạt động; code hiện có khóa tiến trình <code>.nms-monitor.lock</code> để phòng ngừa.

### Bước 11.2 – Dashboard có những mục gì?

- **Tổng quan**: tình trạng thiết bị, CPU, RAM, interface, dịch vụ HTTP/TCP, nhật ký gần nhất.
- **Biểu đồ hiệu suất**: CPU, RAM, RTT, lưu lượng mạng và tình trạng mất gói theo mẫu thời gian.
- **Danh sách thiết bị**: Windows, Ubuntu, R1/R2/R3, các đích ping.
- **Dịch vụ HTTP/TCP**: website và các cổng đã khai báo, trạng thái OK/lỗi.
- **Lịch sử cảnh báo**: các sự kiện warning và recovered đã lưu.
- **Mở Telegram**: mở cuộc trò chuyện bot, không hiển thị Bot Token.
- **Xuất báo cáo HTML**: file báo cáo độc lập có biểu đồ.

Các mục ở sidebar là các anchor trên cùng trang: <code>#overview</code>, <code>#charts</code>, <code>#devices</code>, <code>#services</code>, <code>#alerts</code>. Không nhầm <code>#services</code> với endpoint Flask riêng <code>/services</code>.

### Bước 11.3 – Các API và file lưu trữ

- <code>GET /api/metrics</code>: trạng thái thiết bị, dịch vụ, lịch sử và alerts.
- <code>GET /report</code>: xem báo cáo HTML.
- <code>GET /report/download</code>: tải báo cáo HTML.
- <code>GET /report/alerts.csv</code>: xuất lịch sử cảnh báo dạng CSV.
- <code>nms_history.jsonl</code>: chuỗi số liệu CPU/RAM/RTT/RX/TX.
- <code>nms_services.jsonl</code>: kết quả kiểm tra HTTP/TCP.
- <code>nms_alerts.jsonl</code>: cảnh báo và khôi phục.
- <code>state.json</code>: nhớ trạng thái để không gửi cùng cảnh báo lặp vô hạn.
- <code>.nms-monitor.lock</code>: file khóa vòng Monitor.

**Giải thích:** Mỗi vòng lấy mẫu sẽ đọc Windows cục bộ, ping đích, hỏi SNMP trên Ubuntu/router, tính tốc độ RX/TX từ chênh lệch bộ đếm, kiểm tra HTTP/TCP và lưu trạng thái. Hệ thống chỉ gửi sự kiện khi điều kiện đổi từ bình thường sang lỗi hoặc ngược lại.

---

## 12. GIAI ĐOẠN 9 – TÍCH HỢP LAB 4 HTTP VÀ LAB 5 TCP

### Bước 12.1 – Trước khi tích hợp

Bộ code Buổi 5 từng có Lab 4 giám sát HTTP/HTTPS và Lab 5 quét cổng TCP. Trên NMS bản đầu, mới chỉ tự kiểm tra:

~~~text
NMS-Dashboard-HTTP -> http://127.0.0.1:5055/
NMS-Dashboard-TCP  -> 127.0.0.1:5055
~~~

Hai kiểm tra này đều trỏ vào **chính Windows** và không chứng minh được khả năng giám sát dịch vụ độc lập trên Ubuntu.

### Bước 12.2 – Bật SSH trên Ubuntu (để NMS kiểm tra cổng 22)

Ubuntu Terminal:

~~~bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo systemctl status ssh --no-pager
sudo ss -lntp | grep ':22'
~~~

Windows PowerShell:

~~~powershell
Test-NetConnection 192.168.10.128 -Port 22
~~~

Kỳ vọng <code>TcpTestSucceeded : True</code>. Kết quả này nghĩa là cổng 22 chấp nhận kết nối TCP, **không** có nghĩa đã xác thực đăng nhập SSH thành công.

### Bước 12.3 – Dùng file demo HTTP lúc đầu (để hiểu cơ chế)

Từ thư mục Windows <code>nms-monitor</code>:

~~~powershell
scp .\demo_http_lab4.py anh@192.168.10.128:~/
~~~

Tại Ubuntu (tài khoản đúng theo máy của nhóm):

~~~bash
# Sửa địa chỉ bind trong file thành 192.168.10.128 nếu code còn bind 127.0.0.1
python3 ~/demo_http_lab4.py
~~~

Các endpoint demo được dùng:

~~~text
http://192.168.10.128:8765/ok     -> HTTP 200
http://192.168.10.128:8765/error  -> HTTP 503
http://192.168.10.128:8765/slow   -> phản hồi chậm khoảng 4 giây
~~~

Lưu ý: tập tin phải bind đúng IP Ubuntu hoặc <code>0.0.0.0</code> (chỉ khi có firewall phù hợp); chỉ mở trình duyệt ở localhost Ubuntu là **chưa chứng minh được Windows truy cập**. Khi demo, giữ terminal web test chạy; bấm Ctrl+C để dừng.

### Bước 12.4 – Cấu hình NMS theo dõi các dịch vụ riêng

Đã đưa vào mục <code>services</code> trong config.yaml:

~~~yaml
services:
  http:
    - name: NMS-Dashboard-HTTP
      url: http://127.0.0.1:5055/
      expected_status: 200
      max_response_seconds: 3
      timeout: 6
    - name: Ubuntu-HTTP
      url: http://192.168.10.128:8765/ok
      expected_status: 200
      max_response_seconds: 3
      timeout: 6
  tcp:
    - name: NMS-Dashboard-TCP
      host: 127.0.0.1
      port: 5055
      timeout: 2
    - name: Ubuntu-SSH
      host: 192.168.10.128
      port: 22
      timeout: 2
    - name: Ubuntu-HTTP-Port
      host: 192.168.10.128
      port: 8765
      timeout: 2
~~~

Sau khi lưu, dừng rồi chạy lại <code>python web.py</code> để đọc YAML mới. Kỳ vọng **5/5 dịch vụ hoạt động** nếu server HTTP và SSH đang mở.

### Bước 12.5 – Các kiểm thử đã làm

- Dừng file web demo Ubuntu → <code>Ubuntu-HTTP</code> lỗi, <code>Ubuntu-HTTP-Port</code> lỗi.
- Mở lại demo → cả hai hồi phục.
- **[ĐÃ KIỂM THỬ]** Telegram nhận cả hai cảnh báo và cả hai thông báo hồi phục.
- Trước đây lỗi được hiển thị dài dạng <code>WinError 10061</code>; file <code>service_checks.py</code> được chỉnh để diễn giải thân thiện (ví dụ: dịch vụ không chấp nhận kết nối / hết thời gian chờ).

**Phân biệt kỹ thuật:** HTTP kiểm tra mã 200, 503 và thời gian phản hồi; TCP chỉ kiểm tra có mở kết nối tới host:port được hay không. Một dịch vụ HTTP chết có thể tạo **hai cảnh báo khác loại** (HTTP và TCP), không phải lỗi gửi trùng Telegram.

---

## 13. GIAI ĐOẠN 10 – THAY HTTP DEMO BẰNG NGINX TỰ KHỞI ĐỘNG

Lý do: script demo chỉ chạy khi mở Terminal và gọi Python; không thích hợp giám sát lâu dài. Web server Nginx trên Ubuntu được cấu hình khởi động cùng hệ điều hành.

### Bước 13.1 – Cài và bật Nginx Ubuntu

~~~bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable --now nginx
sudo systemctl status nginx --no-pager
sudo ss -lntp | grep ':80'
~~~

Từ Windows mở **http://192.168.10.128/**. Thấy trang **Welcome to nginx!** hoặc HTTP 200 là web Ubuntu đã hoạt động.

Nếu bật UFW, chỉ cần cho phép truy cập từ máy NMS trong mạng lab, ví dụ:

~~~bash
sudo ufw status
sudo ufw allow from 192.168.10.1 to any port 80 proto tcp
~~~

Đừng bật UFW/tự thay firewall tùy tiện nếu máy Ubuntu có các dịch vụ khác cần sử dụng. SNMP 161/UDP và SSH 22/TCP cũng phải được cho phép từ nguồn quản trị phù hợp nếu firewall đang hoạt động.

### Bước 13.2 – Đổi config.yaml từ demo 8765 sang Nginx cổng 80

~~~yaml
services:
  http:
    - name: NMS-Dashboard-HTTP
      url: http://127.0.0.1:5055/
      expected_status: 200
      max_response_seconds: 3
      timeout: 6
    - name: Ubuntu-HTTP
      url: http://192.168.10.128/
      expected_status: 200
      max_response_seconds: 3
      timeout: 6
  tcp:
    - name: NMS-Dashboard-TCP
      host: 127.0.0.1
      port: 5055
      timeout: 2
    - name: Ubuntu-SSH
      host: 192.168.10.128
      port: 22
      timeout: 2
    - name: Ubuntu-HTTP-Port
      host: 192.168.10.128
      port: 80
      timeout: 2
~~~

Sau khi lưu, khởi động lại <code>python web.py</code> ở Windows. **[ĐÃ KIỂM THỬ]** Dashboard có 5/5 dịch vụ hoạt động, Ubuntu HTTP trả 200, Ubuntu SSH cổng 22 hoạt động.

### Bước 13.3 – Test dừng và khôi phục Nginx

Ở Ubuntu:

~~~bash
sudo systemctl stop nginx
~~~

Không dừng NMS Windows. Chờ vòng kiểm tra mới; kỳ vọng HTTP và TCP:80 báo lỗi, Telegram gửi cảnh báo.

~~~bash
sudo systemctl start nginx
~~~

Chờ vòng kiểm tra; kỳ vọng Dashboard về 5/5, Telegram gửi hai thông báo phục hồi.

**[ĐÃ KIỂM THỬ]** Hình Telegram ghi nhận cảnh báo Ubuntu-HTTP và Ubuntu-HTTP-Port lúc khoảng 22:25 và phục hồi sau đó. Như vậy **Lab 4 + Lab 5 đã test thực tế trên Ubuntu**.

Từ nay khi mở Ubuntu, Nginx và SSH có thể tự chạy nhờ <code>systemctl enable</code>. **Windows vẫn phải khởi động NMS** qua <code>python web.py</code>. Không cần chạy <code>demo_http_lab4.py</code> nữa trừ khi làm demo riêng cho mã 503 hoặc phản hồi chậm.

---

## 14. GIAI ĐOẠN 11 – KIỂM THỬ TOÀN BỘ TÌNH HUỐNG VÀ TELEGRAM

### 14.1. Kiểm thử RAM vượt ngưỡng

Mặc định trong config.yaml:

~~~yaml
thresholds:
  cpu: 80
  ram: 85
  temp: 70
~~~

Để kiểm thử **không cần làm máy thật quá tải**, có thể thay tạm ngưỡng RAM xuống 60% cho máy có RAM đo được trên 60%, lưu config rồi chạy lại NMS. Khi điều kiện từ bình thường chuyển sang vượt ngưỡng, bot gửi cảnh báo; đưa ngưỡng về 85% và chạy lại để kiểm tra khôi phục khi số liệu nằm dưới 85%.

**[ĐÃ KIỂM THỬ]** Telegram đã nhận cảnh báo <code>Ubuntu-VM RAM 60,8% (ngưỡng 60%)</code> và cảnh báo Windows vượt ngưỡng RAM 85%. **Sau khi thử phải trả ngưỡng về đúng giá trị đề tài và không tiếp tục duy trì ngưỡng 60% cho sản phẩm.**

### 14.2. Test HTTP/TCP trên Ubuntu

Các lệnh:

~~~bash
sudo systemctl stop nginx    # tạo lỗi
sudo systemctl start nginx   # phục hồi
~~~

Kiểm tra trên Windows:

~~~powershell
Test-NetConnection 192.168.10.128 -Port 80
Test-NetConnection 192.168.10.128 -Port 22
~~~

Quan sát Dashboard mục dịch vụ HTTP/TCP + Telegram + nhật ký. **[ĐÃ KIỂM THỬ]** Cả hai chiều đã hoạt động.

### 14.3. Test interface DOWN/UP của router R1

**Chỉ thao tác trên router GNS3 của chính nhóm.** Chọn **FastEthernet0/0** nối R1–R2, **không shutdown FastEthernet1/0** vì đó là đường quản lý SNMP về Switch2/VMnet1.

Mở Console R1:

~~~cisco
enable
configure terminal
interface FastEthernet0/0
shutdown
end
show ip interface brief
~~~

Dự kiến <code>FastEthernet0/0</code> chuyển down. Quan sát NMS: R1 vẫn Online (SNMP qua f1/0 còn hoạt động) nhưng interface FastEthernet0/0 hiển thị DOWN màu đỏ, R1 chuyển trạng thái Cảnh báo.

**[ĐÃ KIỂM THỬ]** Telegram lúc **22:30:15 – 02/11/2026** gửi:

~~~text
CẢNH BÁO
R1: interface FastEthernet0/0 DOWN
~~~

Khôi phục trên Console R1:

~~~cisco
configure terminal
interface FastEthernet0/0
no shutdown
end
show ip interface brief
~~~

**[ĐÃ KIỂM THỬ]** Telegram lúc **22:30:43 – 02/11/2026** gửi thông báo R1 interface FastEthernet0/0 trở lại bình thường. Dashboard mục nhật ký có cả sự kiện cảnh báo và khôi phục.

Sau test, nên lưu trạng thái cuối cùng:

~~~cisco
write memory
~~~

### 14.4. Checklist bằng chứng đã có

| Test | Kết quả xác nhận |
| --- | --- |
| Ping Windows ↔ R1/R2/R3 | PASS |
| snmpget tên R1/R2/R3 | PASS |
| snmpwalk interface và ifOperStatus | PASS |
| SNMP Ubuntu CPU/RAM/interface | PASS |
| Dashboard Windows/Ubuntu/router Online | PASS |
| Telegram RAM vượt ngưỡng, khôi phục | PASS |
| HTTP Ubuntu web 200 / mất kết nối / khôi phục | PASS |
| TCP Ubuntu 80 và 22 | PASS (kiểm tra kết nối) |
| R1 FastEthernet0/0 DOWN/UP + Telegram | PASS |
| HTML report với biểu đồ và bảng | PASS |
| Slack thực tế | **Chưa kiểm thử** |
| Các Lab bảo mật 6–9 nhúng vào NMS | **Không thuộc phạm vi đã hoàn tất** |

---

## 15. GIAI ĐOẠN 12 – DASHBOARD V2 VÀ XUẤT BÁO CÁO V3

### 15.1. Các phiên bản đã cải tiến

1. Dashboard ban đầu chỉ là bảng trạng thái CPU/RAM/interface.
2. Dashboard V2: nền tối, thanh điều hướng, biểu đồ lịch sử, bảng chi tiết thiết bị, Telegram, nhật ký cảnh báo.
3. Báo cáo HTML đầu tiên chỉ có bảng, không có biểu đồ → chưa phù hợp để nộp cuối kỳ.
4. NMS Report V3: báo cáo HTML offline, thêm **6 biểu đồ** theo thời gian (CPU, RAM, RTT, RX, TX, Packet Loss), bảng thiết bị, bảng HTTP/TCP và lịch sử cảnh báo.
5. Tích hợp Lab 4/5: bổ sung bảng dịch vụ và sự kiện HTTP/TCP vào Dashboard và báo cáo.

### 15.2. Địa chỉ xem và xuất

~~~text
http://127.0.0.1:5055/
http://127.0.0.1:5055/#charts
http://127.0.0.1:5055/#services
http://127.0.0.1:5055/#alerts
http://127.0.0.1:5055/report
http://127.0.0.1:5055/report/download
http://127.0.0.1:5055/report/alerts.csv
~~~

Sau khi chỉnh sửa code xuất báo cáo, phải **tải lại báo cáo mới**; các file HTML cũ trong Downloads không tự cập nhật.

### 15.3. Giải thích các biểu đồ

- **CPU (%):** thời gian × %CPU, Windows từ psutil, Ubuntu/router từ SNMP.
- **RAM (%):** thời gian × %RAM.
- **RTT (ms):** độ trễ của từng lần ping. Một lần ping mỗi vòng, không suy ra độ trễ liên tục.
- **RX (KB/s):** tốc độ dữ liệu nhận, tính từ chênh lệch bộ đếm octets giữa hai lần đo; mẫu đầu có thể chưa tính được.
- **TX (KB/s):** tốc độ dữ liệu gửi, tính tương tự.
- **Packet Loss (%):** mỗi vòng chỉ gửi một echo ICMP cho từng thiết bị, nên mỗi mẫu có thể là 0% hoặc 100%; **không phải** ước lượng mất gói dài hạn từ hàng trăm gói.

**[ĐÃ KIỂM THỬ]** Báo cáo HTML cuối đã có thống kê thiết bị, dịch vụ và sự kiện, cùng các biểu đồ. Các số liệu biến động theo thời điểm; không ghi cố định 7/7 hay 5/5 thành bảo đảm vĩnh viễn.

### 15.4. Giới hạn cần trình bày trung thực

- Một số router IOS không hỗ trợ OID nhiệt độ → hiển thị không có dữ liệu.
- RAM router 17,9% xuất hiện tương tự nhau; cần đối chiếu OID với CLI/IOS trước khi khẳng định chính xác tuyệt đối.
- Các biểu đồ có thể nối qua một khoảng trống nếu không có mẫu; khi phân tích nên lưu ý điều này.
- NMS hiện chạy theo tiến trình <code>python web.py</code> trên Windows; nếu tắt tiến trình Windows, việc giám sát tự động ngừng.
- Monitor dùng trạng thái cũ trong <code>state.json</code> để tránh spam cùng sự cố; muốn kiểm tra cảnh báo lần nữa cần tạo chu kỳ **bình thường → lỗi → phục hồi**.

---

## 16. GIAI ĐOẠN 13 – ĐƯA PYTHON VÀ GNS3 LÊN GITHUB

Repository chính: **https://github.com/anh632k-ui/MMTNC**. Thời điểm chốt đã thấy các thư mục <code>Python</code>, <code>nms-monitor</code>, <code>GNS3</code> trên nhánh <code>main</code>.

### 16.1. Sao chép code NMS sang repo clone sạch

~~~powershell
cd D:\k1\MMT_NC
git clone https://github.com/anh632k-ui/MMTNC.git MMTNC_Push_NMS
cd MMTNC_Push_NMS
git pull --ff-only origin main
~~~

Nếu thư mục clone đã tồn tại thì **không clone lần hai**, chỉ <code>cd</code> vào rồi <code>git pull --ff-only</code>.

Để sao chép mã nguồn vào thư mục clone (chỉ khi cần cập nhật):

~~~powershell
$src = "D:\k1\MMT_NC\DoAn\nms-monitor"
$dest = "D:\k1\MMT_NC\MMTNC_Push_NMS\nms-monitor"
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item "$src\*.py" $dest -Force
Copy-Item "$src\requirements.txt" $dest -Force
~~~

**Không chép config.yaml đang chứa token**; chỉ dùng <code>config.example.yaml</code> với placeholder. Kiểm tra .gitignore trước khi stage.

~~~powershell
git status
git add .gitignore nms-monitor/
git diff --cached --name-only
git commit -m "Add NMS Monitor V2 dashboard SNMP HTTP TCP Telegram"
git push origin main
~~~

**[ĐÃ XÁC NHẬN]** Commit mã nguồn NMS đã xuất hiện trên GitHub.

### 16.2. Xuất project GNS3 portable

1. Mở Console R1/R2/R3, chạy <code>write memory</code>.
2. Trên GNS3 bấm **Stop All Nodes** (nút vuông đỏ); phải dừng hết router.
3. Chọn **File → Export portable project**.
4. Bỏ tùy chọn đóng gói base IOS image/snapshots không cần thiết.
5. Xuất sang thư mục **khác** thư mục project đang chạy:

~~~text
D:\k1\MMT_NC\GNS3_Export\NMS-Monitor-Anh.gns3project
~~~

**[ĐÃ GẶP LỖI]** Xuất khi router vẫn chạy → <code>Project must be stopped in order to export it</code>. Xuất vào project đang mở/trùng file → <code>Permission denied [Errno 13]</code> và file 0 KB. Sửa bằng cách Stop router rồi xuất sang <code>GNS3_Export</code> riêng.

**[ĐÃ KIỂM THỬ]** File portable đã xuất thành công, kích thước khoảng **53 KB**, sau đó đã push lên GitHub.

Có thể kiểm tra archive:

~~~powershell
py -c "import zipfile; p=r'D:\k1\MMT_NC\GNS3_Export\NMS-Monitor-Anh.gns3project'; print('FILE HOP LE' if zipfile.is_zipfile(p) else 'FILE KHONG HOP LE')"
~~~

**Bảo mật và bản quyền:** Trước khi chia sẻ public, mở archive bằng 7-Zip/giải nén kiểm tra các cấu hình router, credentials, NVRAM và image. Không phát tán image Cisco có bản quyền. Nếu archive đã công khai và chứa bí mật, phải thay/thu hồi bí mật; chỉ xóa file khỏi commit mới là **không đủ** để xóa khỏi lịch sử Git.

### 16.3. Push GNS3

~~~powershell
cd D:\k1\MMT_NC\MMTNC_Push_NMS
git pull --ff-only origin main
New-Item -ItemType Directory -Force .\GNS3 | Out-Null
Copy-Item "D:\k1\MMT_NC\DoAn\GNS3\NMS-Monitor-Anh\NMS-Monitor-Anh.gns3" ".\GNS3\"
Copy-Item "D:\k1\MMT_NC\GNS3_Export\NMS-Monitor-Anh.gns3project" ".\GNS3\"
git add GNS3/
git status
git commit -m "Add GNS3 topology and portable project"
git push origin main
~~~

**Chỉ chạy lệnh Copy portable archive sau khi đã rà soát an toàn.** File portable và topology đã được ghi nhận trên GitHub. Để lấy về từ máy khác: clone repo, import <code>.gns3project</code> qua GNS3 và tự chuẩn bị image/router template hợp pháp tương thích.

---

## 17. KHỞI ĐỘNG LẠI TOÀN BỘ HỆ THỐNG SAU KHI TẮT MÁY

Dùng đúng thứ tự dưới đây để tránh trạng thái giả Offline khi các thiết bị chưa bật:

1. **Windows:** kiểm tra card <code>VMware Network Adapter VMnet1</code> còn IP <code>192.168.10.1/24</code>.
2. **VMware:** bật Ubuntu; chờ <code>ens34 = 192.168.10.128/24</code>. snmpd, ssh, nginx đã đặt tự khởi động.
3. **GNS3:** mở NMS-Monitor-Anh, nhấn Start cho R1/R2/R3; kiểm tra cổng xanh.
4. **Windows PowerShell:** ping 192.168.10.11/.12/.13 và .128.
5. **VS Code:** mở thư mục <code>D:\k1\MMT_NC\DoAn\nms-monitor</code>.
6. **Terminal PowerShell** đã activate venv: chạy **<code>python web.py</code>**.
7. Trình duyệt: mở **http://localhost:5055**.
8. Kiểm tra giao diện Online, dịch vụ HTTP/TCP 5/5 (nếu tất cả hoạt động), biểu đồ có dữ liệu; xác nhận bot nhận khởi động nếu bật Telegram.
9. Demo tình huống Nginx stop/start hoặc R1 f0/0 shutdown/no shutdown, rồi **đưa mọi dịch vụ về trạng thái bình thường**.
10. Xuất báo cáo mới qua <code>/report/download</code> và lưu ảnh minh chứng.

**Lệnh ngắn duy nhất cần nhớ khi tất cả đã bật:** <code>python web.py</code>. Không chạy file demo HTTP mỗi ngày; Nginx phục vụ HTTP tự khởi động. **Không nhầm chạy <code>python web.py</code> trong Ubuntu VMware** nếu bản NMS chính được thiết kế chạy trên Windows.

---

## 18. BẢNG LỖI ĐÃ GẶP VÀ CÁCH SỬA

| Hiện tượng | Vì sao | Cách xử lý |
| --- | --- | --- |
| GNS3 báo <code>Cannot connect to itself</code> | Nối nhầm một node với chính nó | Chọn đúng hai node, đúng cổng |
| <code>destination port is not free</code> | Cổng đã có link | Xóa link sai, dùng cổng trống |
| <code>Cannot modify a cloud that is already connected</code> | Cloud đang có link | Tháo link trước, sửa Cloud rồi nối lại |
| Cloud/VMnet1 bị lặp 2 cổng | Chọn trùng adapter/port | Dùng một đường Switch2 e3 ↔ Cloud1 VMnet1 |
| WSL ping router 100% packet loss | WSL2 có mạng riêng 172.21.x.x | Chạy NMS Windows VMnet1; không sửa bừa router |
| Ubuntu ping được nhưng <code>snmpget</code> timeout | Community, ACL, SNMP service/view hoặc firewall không khớp | So sánh community; <code>show snmp</code>, <code>show access-lists</code>, <code>ss -lunp</code> |
| Cisco <code>Unknown community name</code> | Gửi sai community | Thống nhất community trên router và client; tránh copy chuỗi ví dụ |
| Chỉ permit Ubuntu mà Windows NMS không hỏi SNMP được | ACL thiếu 192.168.10.1 | Permit đúng IP manager Windows trong ACL |
| Dashboard Ubuntu Online nhưng CPU/RAM rỗng | OID/view SNMP Linux không được đọc | Kiểm tra UCD-SNMP OID, <code>snmpd.conf</code>, <code>snmp_utils.py</code> |
| Telegram báo <code>403 bot can't send messages to the bot</code> | Dùng username bot làm chat_id | Gửi <code>/start</code>; dùng ID số của chat |
| Telegram không có cảnh báo mới dù RAM đang cao | Điều kiện vẫn đang ở trạng thái cảnh báo, tránh spam | Tạo chu kỳ bình thường → lỗi → khôi phục |
| Hai tin HTTP và TCP cùng xuất hiện | Một service chết được phát hiện qua 2 giao thức | Đây là 2 điều kiện khác nhau, không phải cùng một alert bị lặp |
| <code>WinError 10061</code> HTTP | Server Ubuntu không lắng nghe cổng 8765/80 | Bật server demo hoặc Nginx; kiểm tra bind, firewall |
| Nginx phải chạy tay? | Nếu chưa enable service | <code>sudo systemctl enable --now nginx</code> |
| Dashboard web không mở, socket access forbidden | Port bị chiếm hoặc Windows chặn bind | Kiểm tra tiến trình, sử dụng cổng 5055; chỉ chạy một web |
| Venv interpreter hiển thị broken | VS Code đang chọn venv khác/hỏng | Chọn lại <code>.venv\Scripts\python.exe</code> của project |
| Report HTML cũ không có biểu đồ | File xuất trước khi nâng cấp Report V3 | Khởi động code mới, xuất lại báo cáo |
| GNS3 export ra file 0 KB | Project đang chạy hoặc Permission denied | Stop all, xuất sang GNS3_Export mới |
| GNS3 import được nhưng router không chạy | Thiếu IOS image/template tương thích | Cung cấp image hợp pháp từ nguồn có quyền, chọn đúng platform/slots |
| Windows máy khác có IP khác | VMnet1 hoặc DHCP khác | Điều chỉnh config YAML, ACL, Ubuntu IP và Cloud tương ứng |

---

## 19. GIẢI THÍCH CƠ CHẾ, GIỚI HẠN VÀ CÂU HỎI THUYẾT TRÌNH

### 19.1. Trả lời “Hệ thống em giám sát cái gì?”

> Máy Windows chạy NMS Monitor thu thập tài nguyên CPU/RAM/interface và lưu lượng qua SNMP từ Ubuntu VMware và ba router Cisco GNS3. Hệ thống dùng ICMP để xác định kết nối/RTT, HTTP để kiểm tra trạng thái website và thời gian phản hồi, TCP để kiểm tra cổng SSH 22 và web 80. Khi vượt ngưỡng hoặc interface/dịch vụ bị lỗi, NMS cập nhật Dashboard, lưu lịch sử và gửi cảnh báo Telegram; khi phục hồi sẽ gửi thông báo khôi phục.

### 19.2. Câu hỏi thường gặp

**Tại sao phải có GNS3?** Để có 3 router Cisco với topology, IP, OSPF và SNMP như thiết bị mạng thật mà không cần phần cứng Cisco.

**Vì sao dùng Ubuntu VMware?** Để có một máy Linux độc lập, chạy snmpd/SSH/Nginx phục vụ các tình huống giám sát, tách khỏi máy Windows chạy NMS.

**SNMP khác ICMP chỗ nào?** SNMP đọc số liệu quản trị/IF-MIB/OID; ICMP ping kiểm tra khả năng phản hồi và đo RTT. Ping thành công không chứng minh SNMP đúng; SNMP trả hostname không chứng minh tất cả OID hoạt động.

**Vì sao có OID?** OID là địa chỉ của mục dữ liệu trong cây MIB. Ví dụ sysName <code>1.3.6.1.2.1.1.5.0</code>, ifDescr <code>1.3.6.1.2.1.2.2.1.2</code>, ifOperStatus <code>1.3.6.1.2.1.2.2.1.8</code>.

**Giám sát CPU Cisco và Ubuntu giống nhau không?** Không. Router dùng enterprise OID Cisco; Ubuntu dùng UCD-SNMP-MIB. Code <code>snmp_utils.py</code> có nhánh xử lý riêng.

**Lab 4 và Lab 5 khác nhau?** Lab 4 HTTP xác nhận website trả đúng status và đúng thời gian; Lab 5 TCP xác nhận cổng dịch vụ có thể kết nối. Bản tích hợp định kỳ **chỉ giám sát cổng đã cấu hình**, không làm quét toàn bộ 1–1024 cổng như Lab 5 gốc.

**Tại sao tắt Nginx mà có hai cảnh báo?** HTTP lỗi và TCP:80 không kết nối được là hai điều kiện độc lập; cùng bắt nguồn một sự cố dịch vụ.

**Vì sao chọn shutdown R1 FastEthernet0/0 mà không chọn 1/0?** f0/0 là đường truyền giữa router, có thể kiểm tra DOWN mà vẫn giữ đường quản lý SNMP qua f1/0; nếu shutdown f1/0 thì NMS có thể mất khả năng hỏi SNMP toàn router.

**FCFS hay lottery có liên quan đồ án này không?** Không; đó là đồ án sự kiện/vé miễn phí của môn khác, không đưa vào NMS README.

**Tại sao không làm thêm toàn bộ Lab 6–9?** Buổi 5 dùng để học và tổng hợp kỹ thuật; đề tài NMS chỉ yêu cầu giám sát hiệu suất, trạng thái và cảnh báo. Các Lab bắt gói/ARP/brute-force/firewall là mở rộng bảo mật, hiện không phải tính năng NMS chính đã kiểm thử xuyên suốt.

**Tại sao không giám sát HTTP trên router Cisco?** Router không mặc định chạy web cần giám sát. Phần cần giám sát ở router là CPU, RAM, interface và kết nối. Nếu router có SSH thực sự cấu hình, mới có lý do theo dõi thêm TCP 22.

**Telegram có gửi liên tục mỗi 10 giây không?** Không. Monitor lưu trạng thái và chỉ gửi khi xuất hiện sự cố hoặc phục hồi. Thông báo khởi động là sự kiện riêng.

**Hệ thống có hoạt động nếu tắt Windows không?** Không. Windows là trung tâm NMS; ứng dụng không phải dịch vụ cloud độc lập. Ubuntu SNMPD/Nginx/SSH vẫn có thể tự chạy sau khi Ubuntu boot.

**Lấy số liệu ở đâu và báo cáo có mô phỏng không?** Dữ liệu chính đến từ psutil, SNMP và ICMP/HTTP/TCP thực tế. File demo HTTP và router_sim.py chỉ là công cụ thử nghiệm tùy chọn; số liệu báo cáo NMS V3 lấy từ lịch sử của hệ thống chạy, không dùng số liệu mẫu khi xuất bình thường.

### 19.3. Giới hạn và hướng phát triển

- SNMP v2c không mã hóa community; cần giới hạn nguồn và cân nhắc SNMPv3 trong môi trường thật.
- Bot token cần quản lý qua biến môi trường hoặc secret manager thay vì file dễ chia sẻ.
- Trạng thái gửi cảnh báo có thể dao động nếu RAM gần ngưỡng; có thể bổ sung hysteresis (ngưỡng phục hồi thấp hơn ngưỡng cảnh báo).
- Khi NMS ngừng chạy, không thể giám sát chính nó bằng vòng Monitor nội bộ; muốn giám sát độ sẵn sàng NMS cần watchdog hoặc hệ thống độc lập.
- Nên tăng số gói ICMP nếu cần ước tính packet loss có ý nghĩa thống kê.
- Có thể thêm dashboard xác thực đăng nhập, HTTPS, export CSV/PDF và retention lịch sử.

---

## 20. DANH SÁCH KIỂM TRA TRƯỚC KHI NỘP

- [x] Có topology GNS3 3 router, switch, Cloud VMnet1.
- [x] Gán IP R1/R2/R3 và kiểm tra ping.
- [x] Cấu hình SNMP và đọc được tên/interface của ba router.
- [x] Ubuntu VMware có IP Host-only, SNMP hoạt động.
- [x] Windows NMS đọc được Windows/Ubuntu/router.
- [x] Dashboard V2, biểu đồ và Report V3.
- [x] Telegram nhận cảnh báo RAM và khôi phục.
- [x] Nginx HTTP 200, lỗi/ngắt và phục hồi.
- [x] TCP SSH 22 / web 80 hoạt động.
- [x] R1 FastEthernet0/0 DOWN/UP, Telegram cảnh báo/khôi phục.
- [x] Đã đẩy mã nguồn NMS và file GNS3 lên GitHub.
- [ ] Rà soát archive GNS3 đã public không có credentials/IOS image trái phép.
- [ ] Thay token Telegram cũ đã xuất hiện trong ảnh, cập nhật token mới chỉ ở máy riêng.
- [ ] Kiểm tra lần cuối Report và lưu ảnh bằng chứng vào thư mục MinhChung.
- [ ] Kiểm tra <code>config.example.yaml</code> không chứa secrets, đọc được trên máy nhóm.
- [ ] Chuẩn bị lời thuyết trình, phân công thành viên và kịch bản demo 5–7 phút.
- [ ] Tùy yêu cầu môn học: xác nhận có bắt buộc Slack, nhiệt độ, SSH login hoặc tích hợp Lab bảo mật khác hay không.

### Nhật ký các mốc đã hoàn thành

- **Buổi 1–4 và Buổi 5:** học GNS3/WSL/Mininet/SSH/SNMP/Scapy/Flask và tổng hợp Lab 1–10; chọn những kỹ thuật hữu ích cho NMS.
- **Ngày 02/11/2026 buổi chiều:** dựng GNS3 ba router, gán IP, nối Switch2 → Cloud1 → VMnet1, kiểm tra ping Windows/Ubuntu và SNMP.
- **Ngày 02/11/2026 chiều–tối:** chuyển NMS Python chính sang Windows; cấu hình <code>config.yaml</code>, SNMP router/Ubuntu, Telegram, Dashboard V2 và báo cáo V3.
- **Ngày 02/11/2026 buổi tối:** tích hợp HTTP/TCP; thử web demo Ubuntu, rồi thay bằng Nginx; thử stop/start và xác nhận Telegram.
- **22:30 ngày 02/11/2026:** kiểm thử R1 FastEthernet0/0 DOWN/UP, có cảnh báo và khôi phục trên Telegram/Dashboard.
- **Cuối ngày 02/11/2026:** đẩy <code>nms-monitor</code> và <code>GNS3</code> lên repository GitHub, xuất portable project sau khi khắc phục lỗi GNS3.

---

**Ghi chú cuối:** Tài liệu cố ý mô tả đầy đủ cả việc làm sai và cách sửa. Khi triển khai trên máy khác, hãy ưu tiên **file GNS3 portable đã lưu và mã nguồn thật trong repository**; nếu phiên bản/cấu hình máy khác khác với hướng dẫn, hãy kiểm tra bằng các lệnh hiển thị trạng thái trước khi thay đổi IP/ACL. Dự án được thiết kế cho môi trường mạng lab được phép quản lý, không dành cho giám sát máy/hệ thống không có quyền.
