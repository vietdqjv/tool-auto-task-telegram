# Tổng quan Codebase

Tài liệu này cung cấp cái nhìn tổng quan về cấu trúc codebase của dự án.

## Cấu trúc dự án
Dự án được tổ chức theo cấu trúc module, với các thành phần chính được phân tách rõ ràng.

```
src/
├── main.py                    # Điểm vào chính của ứng dụng
├── core/
│   └── config.py              # Cấu hình hệ thống (giờ làm việc, múi giờ, khoảng thời gian nhắc nhở)
├── database/
│   ├── models/
│   │   ├── task.py            # Mô hình tác vụ (bao gồm các trường cho tác vụ nhóm)
│   │   └── user.py            # Mô hình người dùng
│   └── repositories/          # Lớp truy cập dữ liệu (DAL)
├── services/
│   ├── working-hours.py       # Dịch vụ xác thực giờ làm việc theo múi giờ VN
│   ├── group-task-service.py  # Dịch vụ CRUD và quy trình làm việc cho tác vụ nhóm
│   ├── task-service.py        # Dịch vụ cho tác vụ cá nhân
│   └── notification.py        # Dịch vụ thông báo Telegram
├── scheduler/
│   ├── manager.py             # Singleton quản lý APScheduler
│   └── jobs/
│       ├── notify.py          # Nhắc nhở tác vụ cá nhân
│       └── group-task-reminder.py  # Nhắc nhở tác vụ nhóm, phát hiện quá hạn, dọn dẹp
└── bot/
    ├── handlers/
    │   ├── commands.py        # Xử lý các lệnh chung (/start, /help, /status)
    │   ├── tasks.py           # Xử lý các tác vụ cá nhân
    │   ├── group-tasks.py     # Xử lý các lệnh tác vụ nhóm (/mytasks, /tasks, /done, /verify, /reject, /rep, /reassign)
    │   └── group-task-fsm.py  # Máy trạng thái hữu hạn (FSM) cho quy trình tạo tác vụ nhiều bước
    ├── keyboards/
    │   ├── inline.py          # Bàn phím inline chung
    │   └── group-task-keyboards.py  # Bàn phím cho tác vụ nhóm
    └── middlewares/           # Middleware (giới hạn tốc độ, xác thực, phiên)
```

## Tính năng chính
-   **Quản lý tác vụ cá nhân**: Tạo, xem, hoàn thành, xóa tác vụ.
-   **Quản lý tác vụ nhóm**: Giao, nhắc nhở, gửi, xác minh, từ chối tác vụ.
-   **Thực thi giờ làm việc**: Áp dụng giờ làm việc tại Việt Nam (8:30-12:00, 13:30-17:30).
-   **Nhắc nhở định kỳ**: Gửi nhắc nhở trong giờ làm việc.
-   **Phát hiện quá hạn tự động**: Tự động đánh dấu tác vụ quá hạn.
-   **Dọn dẹp tác vụ đã hoàn thành**: Xóa các tác vụ đã hoàn thành sau 30 ngày.

## Công nghệ sử dụng (Tech Stack)
-   **Framework Bot**: aiogram 3.x
-   **ORM/Database**: SQLAlchemy 2.x (async)
-   **Scheduler**: APScheduler 3.x
-   **Cache/FSM**: Redis
-   **Database**: SQLite/PostgreSQL
-   **Cấu hình**: pydantic-settings
