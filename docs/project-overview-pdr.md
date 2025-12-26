# Tổng quan dự án và Yêu cầu phát triển sản phẩm (PDR)

## 1. Tổng quan dự án

Dự án "Telegram Bot Automation Tool" là một bot Telegram đa năng được thiết kế để hỗ trợ người dùng quản lý tác vụ cá nhân và tác vụ nhóm một cách hiệu quả thông qua giao diện trò chuyện. Bot tích hợp các tính năng lập lịch, nhắc nhở và quản lý dữ liệu bền vững.

## 2. Mục tiêu dự án

Mục tiêu chính của dự án là cung cấp một công cụ tự động hóa mạnh mẽ, dễ sử dụng cho:
-   **Người dùng cá nhân**: Quản lý các tác vụ hàng ngày, nhận nhắc nhở kịp thời.
-   **Nhóm làm việc**: Phân công, theo dõi và quản lý các tác vụ nhóm, đảm bảo tiến độ công việc.
-   **Tự động hóa**: Giảm thiểu công việc thủ công, tăng cường năng suất thông qua các tính năng tự động như nhắc nhở định kỳ và phát hiện tác vụ quá hạn.

## 3. Các tính năng chính

### 3.1. Quản lý tác vụ cá nhân
-   **Tạo tác vụ**: Người dùng có thể tạo tác vụ mới với mô tả, thời hạn.
-   **Xem tác vụ**: Xem danh sách các tác vụ đang chờ xử lý, đã hoàn thành hoặc quá hạn.
-   **Hoàn thành/Xóa tác vụ**: Đánh dấu tác vụ là hoàn thành hoặc xóa khỏi danh sách.
-   **Nhắc nhở**: Nhận thông báo nhắc nhở theo lịch trình đã đặt.

### 3.2. Quản lý tác vụ nhóm (Mới triển khai - Cập nhật ngày 25/12/2025)
-   **Giao tác vụ**: Admin có thể giao tác vụ cho các thành viên trong nhóm thông qua lệnh \`/assign\` hoặc người có quyền có thể giao tác vụ cho các thành viên trong nhóm.
-   **Theo dõi trạng thái**: Theo dõi trạng thái của các tác vụ nhóm (đã giao, đang thực hiện, đã nộp, cần xác minh, bị từ chối, đã hoàn thành).
-   **Nhắc nhở tác vụ nhóm**: Gửi nhắc nhở định kỳ cho các thành viên về tác vụ nhóm.
-   **Phê duyệt/Từ chối**: Admin có thể xác minh và phê duyệt hoặc từ chối tác vụ đã nộp.
-   **Tái phân công**: Khả năng tái phân công tác vụ nhóm.

## 4. Công nghệ sử dụng (Tech Stack)

-   **Bot Framework**: aiogram 3.x
-   **ORM/Database**: SQLAlchemy 2.x (async)
-   **Scheduler**: APScheduler 3.x
-   **Cache/FSM**: Redis
-   **Database**: SQLite (phát triển) / PostgreSQL (sản phẩm)
-   **Cấu hình**: pydantic-settings

## 5. Yêu cầu phát triển sản phẩm (PDRs)

### 5.1. Yêu cầu chức năng (Functional Requirements)
-   **FR1**: Bot phải cho phép người dùng tạo, xem, chỉnh sửa, hoàn thành và xóa tác vụ cá nhân.
-   **FR2**: Bot phải hỗ trợ các lệnh để quản lý tác vụ nhóm, bao gồm giao (đặc biệt là lệnh \`/assign\` cho admin), theo dõi, xác minh, từ chối và tái phân công.
-   **FR3**: Bot phải gửi nhắc nhở định kỳ cho cả tác vụ cá nhân và tác vụ nhóm trong giờ làm việc được định cấu hình.
-   **FR4**: Hệ thống phải tự động phát hiện và đánh dấu các tác vụ quá hạn.
-   **FR5**: Bot phải hỗ trợ quy trình tạo tác vụ nhiều bước thông qua FSM (Finite State Machine).
-   **FR6**: Bot phải cung cấp các bàn phím (inline keyboards) để tương tác dễ dàng với các tác vụ.

### 5.2. Yêu cầu phi chức năng (Non-functional Requirements)
-   **NFR1 - Hiệu suất**: Các phản hồi của bot phải nhanh chóng (<1 giây cho hầu hết các thao tác).
-   **NFR2 - Khả năng mở rộng**: Hệ thống phải có khả năng mở rộng để xử lý số lượng người dùng và tác vụ tăng lên.
-   **NFR3 - Độ tin cậy**: Scheduler phải đảm bảo các nhắc nhở và tác vụ tự động được thực hiện đáng tin cậy.
-   **NFR4 - Bảo mật**: Dữ liệu người dùng và tác vụ phải được bảo vệ. Bot cần có cơ chế xác thực và phân quyền phù hợp.
-   **NFR5 - Khả năng bảo trì**: Mã nguồn phải sạch, dễ đọc và dễ bảo trì theo các tiêu chuẩn mã hóa.
-   **NFR6 - Khả năng sử dụng**: Giao diện người dùng bot (thông qua Telegram) phải trực quan và dễ sử dụng.

### 5.3. Tiêu chí chấp nhận và chỉ số thành công
-   **AC1**: Tất cả các tính năng quản lý tác vụ cá nhân và nhóm đều hoạt động như mong đợi trong môi trường thử nghiệm.
-   **AC2**: Tỷ lệ gửi nhắc nhở thành công đạt 99%.
-   **AC3**: Không có lỗi nghiêm trọng nào được báo cáo trong quá trình sử dụng thông thường trong giai đoạn thử nghiệm.
-   **MS1**: Tỷ lệ giữ chân người dùng hàng tháng đạt 70%.
-   **MS2**: Thời gian phản hồi trung bình của bot dưới 500ms.
-   **MS3**: Tỷ lệ hoàn thành tác vụ nhóm tăng 20% sau khi triển khai tính năng.

## 6. Lịch sử thay đổi

-   **2025-12-26**: Hoàn thành tái cấu trúc mẫu phản hồi cho bot.
    -   Tất cả các phản hồi trong nhóm chat hiện sử dụng `message.reply()` + `mention_html()`.
    -   Các phản hồi trong chat riêng/DM vẫn giữ `message.answer()`.
    -   Thêm `parse_mode='HTML'` để định dạng tin nhắn đúng cách.
-   **2025-12-25**: Hoàn thành triển khai tính năng Quản lý tác vụ nhóm (Group Task Management).
    -   Giai đoạn 1: Nền tảng cơ sở dữ liệu và cấu hình (`TaskStatus.SUBMITTED`, `OVERDUE`, các trường tác vụ nhóm).
    -   Giai đoạn 2: Các dịch vụ (`working-hours.py`, `group-task-service.py`).
    -   Giai đoạn 3: Scheduler (`group-task-reminder.py` - nhắc nhở định kỳ, phát hiện quá hạn, dọn dẹp).
    -   Giai đoạn 4: Giao diện Bot (`group-task-keyboards.py`, `group-task-fsm.py`).
    -   Giai đoạn 5: Handlers (`group-tasks.py` với các lệnh `/mytasks`, `/tasks`, `/done`, `/verify`, `/reject`, `/reassign`, `/assign`).
