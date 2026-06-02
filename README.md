# Insurance Management System

**Tên tiếng Việt:** Hệ thống quản lý bảo hiểm

Insurance Management System là nền tảng quản lý nghiệp vụ bảo hiểm theo mô hình nhiều vai trò, gồm quản trị viên, nhân viên và khách hàng. Hệ thống hỗ trợ quản lý gói bảo hiểm, hợp đồng, phân công chăm sóc, hồ sơ bồi thường, lịch hẹn, trò chuyện nội bộ và trợ lý AI dựa trên tài liệu công ty.

Mục tiêu của dự án là mô phỏng một hệ thống SaaS bảo hiểm hiện đại, có phân quyền rõ ràng, dữ liệu demo thực tế, giao diện tiếng Việt và kiến trúc full-stack dễ mở rộng.

## Tính năng chính

### Quản trị viên

- Quản lý người dùng, vai trò và trạng thái tài khoản
- Quản lý nhân viên
- Quản lý khách hàng
- Phân công khách hàng cho nhân viên chăm sóc
- Quản lý gói bảo hiểm
- Quản lý quy trình bảo hiểm và các bước xử lý
- Quản lý hợp đồng bảo hiểm
- Quản lý hồ sơ bồi thường
- Quản lý lịch hẹn
- Quản lý tài liệu AI
- Xem dashboard thống kê

### Nhân viên

- Xem khách hàng được phân công
- Xem hợp đồng của khách hàng được phân công
- Xử lý hồ sơ bồi thường
- Xem chứng từ khách hàng gửi
- Cập nhật trạng thái hồ sơ bồi thường
- Trò chuyện với khách hàng
- Quản lý lịch hẹn
- Ghi chú chăm sóc khách hàng

### Khách hàng

- Xem thông tin hồ sơ cá nhân
- Xem hợp đồng bảo hiểm
- Báo cáo sự cố
- Tải ảnh/PDF chứng từ bồi thường
- Theo dõi hồ sơ bồi thường
- Trò chuyện với nhân viên phụ trách
- Đặt lịch hẹn
- Hỏi trợ lý AI dựa trên tài liệu nội bộ công ty

## Công nghệ sử dụng

- Frontend: Next.js App Router, TypeScript, Tailwind CSS, Recharts, Lucide React
- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic
- Database: PostgreSQL
- Authentication: JWT, Role-Based Access Control
- AI: Gemini API, Graph RAG, PDF ingestion, local retrieval fallback
- DevOps: Docker Compose

## Kiến trúc dự án

```text
INSURANCE_APP/
├── api/
│   ├── app/
│   │   ├── api/routers/        # FastAPI routers
│   │   ├── core/               # cấu hình, bảo mật, auth dependency
│   │   ├── db/                 # session, seed data
│   │   ├── models/             # SQLAlchemy models
│   │   ├── repositories/       # truy vấn database
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # nghiệp vụ
│   │   └── utils/              # helper dùng chung
│   ├── alembic/                # database migrations
│   └── uploads/claims/         # lưu chứng từ bồi thường trong môi trường local
├── web/
│   ├── app/                    # Next.js routes
│   ├── components/             # UI components
│   ├── hooks/                  # auth/role hooks
│   ├── lib/                    # formatter, label, auth storage
│   ├── services/               # API clients
│   └── types/                  # TypeScript types
├── docs/                       # tài liệu demo/PDF mẫu
├── docker-compose.yml
└── README.md
```

## Module hệ thống

- Auth/RBAC: đăng nhập, JWT, phân quyền ADMIN/EMPLOYEE/CUSTOMER
- Insurance management: gói bảo hiểm, quy trình, bước xử lý
- Customer/employee management: nhân viên, khách hàng, phân công chăm sóc
- Subscriptions: hợp đồng bảo hiểm, trạng thái thanh toán
- Claims: báo cáo sự cố, xử lý bồi thường, ghi chú thẩm định
- Attachments: tải ảnh/PDF chứng từ và xem preview
- Chat: trò chuyện customer-employee bằng REST polling
- Appointments: đặt lịch, duyệt lịch, đổi trạng thái lịch hẹn
- Dashboard: thống kê theo từng vai trò
- Graph RAG chatbot: trợ lý AI trả lời từ tài liệu nội bộ

## Cài đặt và chạy dự án

Tạo file môi trường:

```powershell
cd C:\Projects\INSURANCE_APP
Copy-Item .env.example .env
```

Chạy hệ thống bằng Docker:

```powershell
docker compose up --build
```

Mở terminal thứ hai, chạy migration và tạo dữ liệu demo:

```powershell
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed --reseed
```

Truy cập:

- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

## Tài khoản demo

| Vai trò | Email | Mật khẩu |
| --- | --- | --- |
| Admin | `admin@insurance.local` | `11111111` |
| Nhân viên | `nhanvien001@insurance.local` | `11111111` |
| Khách hàng | `customer001@customer.insurance.local` | `11111111` |

## Lệnh hữu ích

Chạy backend tests:

```powershell
docker compose exec api pytest
```

Kiểm tra cấu hình Docker Compose:

```powershell
docker compose --env-file .env.example config --quiet
```

Chạy frontend local:

```powershell
cd C:\Projects\INSURANCE_APP\web
npm install
npm run dev
```

Kiểm tra TypeScript:

```powershell
cd C:\Projects\INSURANCE_APP\web
npm run type-check
```

Dọn dữ liệu demo nhưng giữ tài khoản admin:

```powershell
docker compose exec api python -m app.db.seed --clean
```

Dọn và tạo lại toàn bộ dữ liệu demo:

```powershell
docker compose exec api python -m app.db.seed --reseed
```

## Biến môi trường quan trọng

Không commit giá trị bí mật thật lên repository.

| Biến | Ý nghĩa |
| --- | --- |
| `DATABASE_URL` | Chuỗi kết nối PostgreSQL cho backend |
| `SECRET_KEY` | Khóa ký JWT, tương đương JWT secret trong hệ thống |
| `JWT_ALGORITHM` | Thuật toán ký JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Thời gian hết hạn access token |
| `SEED_ADMIN_EMAIL` | Email tài khoản admin khi seed |
| `SEED_ADMIN_PASSWORD` | Mật khẩu admin khi seed |
| `GEMINI_API_KEY` | API key dùng cho Gemini |
| `GEMINI_MODEL` | Model Gemini, mặc định `gemini-1.5-flash` |
| `AI_PROVIDER` | Nhà cung cấp AI, hiện hỗ trợ cấu hình `gemini` và fallback local |
| `RAG_TOP_K` | Số đoạn tài liệu ưu tiên khi truy xuất RAG |
| `RAG_MIN_SCORE` | Ngưỡng điểm tối thiểu để coi đoạn tài liệu là liên quan |
| `CLAIM_UPLOAD_DIR` | Thư mục lưu chứng từ bồi thường local |
| `CLAIM_UPLOAD_MAX_BYTES` | Dung lượng tối đa mỗi file upload |

## Graph RAG chatbot

Trợ lý AI được thiết kế để trả lời khách hàng dựa trên tài liệu nội bộ công ty, không trả lời từ kiến thức chung.

Luồng hoạt động:

1. Admin tải lên PDF/TXT/Markdown trong trang Tài liệu AI.
2. Backend trích xuất nội dung văn bản.
3. Hệ thống chia tài liệu thành các đoạn nhỏ.
4. Graph RAG ingestion trích xuất thực thể và quan hệ từ từng đoạn.
5. Các đoạn tài liệu, thực thể và quan hệ được lưu vào database.
6. Khách hàng đặt câu hỏi trong trang Trợ lý bảo hiểm AI.
7. Hệ thống truy xuất đoạn tài liệu, thực thể và quan hệ liên quan.
8. Gemini nhận ngữ cảnh đã truy xuất và tạo câu trả lời tiếng Việt.
9. Nếu tài liệu không có thông tin phù hợp, chatbot từ chối lịch sự:

```text
Xin lỗi, thông tin này chưa có trong tài liệu nội bộ của công ty. Vui lòng liên hệ nhân viên phụ trách để được hỗ trợ thêm.
```

Nếu chưa cấu hình `GEMINI_API_KEY`, hệ thống vẫn có fallback local để demo truy xuất tài liệu an toàn, nhưng chất lượng câu trả lời sẽ đơn giản hơn.

## Luồng tải chứng từ bồi thường

Khách hàng có thể tải chứng từ khi báo cáo sự cố, ví dụ:

- Hóa đơn viện phí
- Ảnh tai nạn
- Biên lai sửa chữa
- Hóa đơn gara
- Giấy ra viện hoặc tài liệu y tế liên quan

Quy định upload:

- Định dạng hỗ trợ: JPG, PNG, WEBP, PDF
- Dung lượng tối đa: 5MB mỗi file
- Môi trường local lưu file tại `api/uploads/claims/`
- Nhân viên và admin có thể xem chứng từ trong màn hình xử lý bồi thường
- Khách hàng chỉ có thể xóa chứng từ khi hồ sơ còn ở trạng thái chờ xử lý hoặc cần bổ sung hồ sơ

## Dữ liệu demo

Lệnh `--reseed` tạo bộ dữ liệu tiếng Việt gồm:

- 15 nhân viên
- 80 khách hàng
- 12 gói bảo hiểm
- Quy trình và bước xử lý bảo hiểm
- 120 hợp đồng bảo hiểm
- 60 hồ sơ bồi thường
- 40 lịch hẹn
- Chat rooms và tin nhắn demo
- Ghi chú chăm sóc khách hàng
- Lịch sử đăng nhập và nhật ký hoạt động
- Tài liệu RAG và document chunks

## Kiểm thử nhanh thủ công

1. Đăng nhập customer.
2. Vào Báo cáo sự cố.
3. Chọn hợp đồng bảo hiểm.
4. Nhập thông tin sự cố.
5. Tải lên 1 ảnh và 1 PDF.
6. Gửi hồ sơ bồi thường.
7. Mở chi tiết hồ sơ để kiểm tra preview chứng từ.
8. Đăng nhập employee.
9. Vào Xử lý bồi thường.
10. Chọn hồ sơ và kiểm tra chứng từ khách hàng đã gửi.
11. Vào Trợ lý bảo hiểm AI và hỏi câu liên quan đến tài liệu nội bộ.

## Screenshots

Coming soon.

## Roadmap

- WebSocket cho chat thời gian thực
- Lưu file upload trên S3 hoặc Cloudinary
- Email notifications cho lịch hẹn, bồi thường và hợp đồng
- Dashboard phân tích nâng cao
- Triển khai production với Nginx/HTTPS
- pgvector để cải thiện truy xuất embedding
- Audit log nâng cao và export báo cáo

## Ghi chú bảo mật

- Không commit `.env`
- Không commit file upload của người dùng
- Đổi `SECRET_KEY` trước khi deploy production
- Không dùng mật khẩu demo trong môi trường thật
- Cấu hình CORS theo domain production

## License / Author

Author: **Pham Tan Duc**
