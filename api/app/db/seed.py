import argparse
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.audit import ActivityLog, LoginHistory
from app.models.claim import (
    Claim,
    ClaimAttachment,
    ClaimIncidentType,
    ClaimPriority,
    ClaimStatus,
)
from app.models.communication import (
    Appointment,
    AppointmentStatus,
    ChatMessage,
    ChatRoom,
)
from app.models.customer_management import (
    AssignmentStatus,
    Customer,
    CustomerAssignment,
    Employee,
    FollowUpNote,
)
from app.models.insurance import (
    InsurancePackage,
    InsuranceProcess,
    InsuranceStatus,
    ProcessStep,
)
from app.models.rag import (
    Document,
    DocumentChunk,
    RagChatLog,
    RagEntity,
    RagRelationship,
)
from app.models.subscription import (
    CustomerInsuranceSubscription,
    PaymentStatus,
    SubscriptionStatus,
)
from app.models.user import User, UserRole, UserStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.insurance_repository import InsurancePackageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.rag_service import LocalEmbeddingService, _chunk_text, _tokens
from app.services.graph_rag_ingestion_service import GraphRagIngestionService

DEFAULT_PASSWORD = "11111111"

DEMO_EMPLOYEE_DOMAIN = "insurance.local"
DEMO_CUSTOMER_DOMAIN = "customer.insurance.local"

PACKAGE_DEFINITIONS = [
    ("SK-CB", "Bảo hiểm sức khỏe cơ bản", "Bảo hiểm sức khỏe", "Gói bảo hiểm hỗ trợ điều trị nội trú, cấp cứu và khám sức khỏe định kỳ. Quyền lợi gồm viện phí, xe cấp cứu và tư vấn ngoại trú trong hạn mức.", "1800000.00", "50000000.00", 12),
    ("SK-CC", "Bảo hiểm sức khỏe cao cấp", "Bảo hiểm sức khỏe", "Gói chăm sóc y tế cao cấp tại bệnh viện tư nhân. Quyền lợi gồm phẫu thuật, bác sĩ chuyên khoa, thuốc điều trị và phòng bệnh tiêu chuẩn cao.", "5200000.00", "250000000.00", 12),
    ("SK-GD", "Bảo hiểm sức khỏe gia đình", "Bảo hiểm sức khỏe", "Gói bảo vệ sức khỏe cho cha mẹ và con cái. Quyền lợi gồm điều trị nội trú gia đình, nhi khoa và khám phòng ngừa.", "9800000.00", "500000000.00", 12),
    ("XM", "Bảo hiểm xe máy", "Bảo hiểm xe cơ giới", "Bảo hiểm tai nạn xe máy và trách nhiệm dân sự. Hỗ trợ sửa chữa, bồi thường tai nạn và cứu hộ kéo xe.", "350000.00", "30000000.00", 12),
    ("OTO-TC", "Bảo hiểm ô tô tiêu chuẩn", "Bảo hiểm xe cơ giới", "Bảo hiểm va chạm và trách nhiệm dân sự cho ô tô. Hỗ trợ sửa chữa gara, cứu hộ đường bộ và trách nhiệm với bên thứ ba.", "4200000.00", "300000000.00", 12),
    ("OTO-TD", "Bảo hiểm ô tô toàn diện", "Bảo hiểm xe cơ giới", "Bảo hiểm ô tô toàn diện cho va chạm, mất cắp, ngập nước và kính xe. Có gara chính hãng, xe thay thế và hotline 24/7.", "8500000.00", "800000000.00", 12),
    ("DL-TN", "Bảo hiểm du lịch trong nước", "Bảo hiểm du lịch", "Bảo hiểm tai nạn, y tế và chậm hành lý cho chuyến đi trong nước. Hỗ trợ gián đoạn hành trình và mất hành lý.", "180000.00", "80000000.00", 1),
    ("DL-QT", "Bảo hiểm du lịch quốc tế", "Bảo hiểm du lịch", "Bảo hiểm y tế du lịch quốc tế và hỗ trợ khẩn cấp. Bao gồm viện phí nước ngoài, hồi hương y tế và hỗ trợ mất hộ chiếu.", "680000.00", "1000000000.00", 1),
    ("NT-CB", "Bảo hiểm nhân thọ cơ bản", "Bảo hiểm nhân thọ", "Bảo vệ tài chính cơ bản cho gia đình trước rủi ro tử vong hoặc thương tật. Có quyền lợi tiết kiệm linh hoạt.", "3600000.00", "500000000.00", 60),
    ("NT-CC", "Bảo hiểm nhân thọ cao cấp", "Bảo hiểm nhân thọ", "Bảo vệ dài hạn với hạn mức cao, quyền lợi bệnh hiểm nghèo và thưởng duy trì hợp đồng.", "12000000.00", "2000000000.00", 120),
    ("NO", "Bảo hiểm nhà ở", "Bảo hiểm tài sản", "Bảo vệ nhà ở trước cháy nổ, ngập nước và trộm cắp. Hỗ trợ sửa chữa, nơi ở tạm thời và xử lý khẩn cấp.", "2500000.00", "700000000.00", 12),
    ("TSDN", "Bảo hiểm tài sản doanh nghiệp", "Bảo hiểm tài sản", "Bảo hiểm tài sản cho cửa hàng, văn phòng và thiết bị doanh nghiệp. Bao gồm cháy nổ, hư hỏng thiết bị và gián đoạn kinh doanh.", "7800000.00", "1500000000.00", 12),
]

SEEDED_PACKAGE_CODES = [item[0] for item in PACKAGE_DEFINITIONS] + [
    "PKG-DEMO-HEALTH"
]

EMPLOYEE_DATA = [
    ("Nguyễn Văn An", "Chăm sóc khách hàng", "Chuyên viên chăm sóc cao cấp", "0905001001"),
    ("Trần Thị Bích", "Chăm sóc khách hàng", "Chuyên viên dịch vụ khách hàng", "0905001002"),
    ("Lê Minh Châu", "Chăm sóc khách hàng", "Điều phối viên dịch vụ", "0905001003"),
    ("Phạm Quốc Dũng", "Xử lý bồi thường", "Chuyên viên thẩm định bồi thường", "0905001004"),
    ("Hoàng Thị Hạnh", "Xử lý bồi thường", "Trưởng nhóm bồi thường", "0905001005"),
    ("Võ Thanh Khoa", "Xử lý bồi thường", "Chuyên viên giám định tổn thất", "0905001006"),
    ("Đặng Ngọc Linh", "Kinh doanh bảo hiểm", "Tư vấn viên kinh doanh", "0905001007"),
    ("Bùi Anh Minh", "Kinh doanh bảo hiểm", "Quản lý khách hàng doanh nghiệp", "0905001008"),
    ("Đỗ Thị Nguyệt", "Kinh doanh bảo hiểm", "Trưởng nhóm kinh doanh", "0905001009"),
    ("Phan Thanh Phong", "Bảo hiểm sức khỏe", "Tư vấn bảo hiểm sức khỏe", "0905001010"),
    ("Huỳnh Mai Phương", "Bảo hiểm sức khỏe", "Chuyên viên hồ sơ y tế", "0905001011"),
    ("Ngô Quang Sơn", "Bảo hiểm sức khỏe", "Chuyên viên sản phẩm sức khỏe", "0905001012"),
    ("Trương Thị Thảo", "Bảo hiểm xe cơ giới", "Tư vấn bồi thường xe", "0905001013"),
    ("Lý Gia Bảo", "Bảo hiểm xe cơ giới", "Chuyên viên bảo hiểm xe máy", "0905001014"),
    ("Mai Thanh Tú", "Bảo hiểm xe cơ giới", "Tư vấn bảo hiểm ô tô", "0905001015"),
]

FIRST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Võ", "Đặng", "Bùi", "Đỗ", "Phan",
    "Huỳnh", "Ngô", "Trương", "Lý", "Mai", "Dương", "Cao", "Đinh", "Tạ", "Vũ",
]

MIDDLE_NAMES = [
    "Văn", "Thị", "Minh", "Thanh", "Ngọc", "Quang", "Bảo", "Anh", "Gia", "Hồng",
]

GIVEN_NAMES = [
    "An", "Bình", "Châu", "Dung", "Giang", "Hạnh", "Khánh", "Linh", "Minh", "Nam",
    "Phương", "Quân", "Sơn", "Thảo", "Trang", "Tuấn", "Vy", "Yến", "Nhi", "Long",
]

CITIES = [
    ("Đà Nẵng", "Hải Châu", "Lê Duẩn"),
    ("Hội An", "Minh An", "Trần Phú"),
    ("Huế", "Thuận Hóa", "Lê Lợi"),
    ("Hà Nội", "Cầu Giấy", "Trần Duy Hưng"),
    ("TP. Hồ Chí Minh", "Quận 1", "Nguyễn Thị Minh Khai"),
    ("Cần Thơ", "Ninh Kiều", "Nguyễn Văn Cừ"),
]

CLAIM_SCENARIOS = [
    ("Tai nạn xe máy trên đường đi làm", "Khách hàng báo tai nạn xe máy, đã có hóa đơn sửa chữa và đang bổ sung biên bản hiện trường.", ClaimIncidentType.ACCIDENT),
    ("Nhập viện điều trị sốt xuất huyết", "Khách hàng nhập viện điều trị sốt xuất huyết và yêu cầu chi trả quyền lợi nội trú.", ClaimIncidentType.HOSPITAL),
    ("Va chạm ô tô tại ngã tư", "Hồ sơ va chạm ô tô gồm báo giá gara, hình ảnh hiện trường và thông tin bên thứ ba.", ClaimIncidentType.DAMAGE),
    ("Yêu cầu chi trả phẫu thuật", "Khách hàng đề nghị hoàn trả chi phí phẫu thuật theo lịch hẹn và thuốc sau điều trị.", ClaimIncidentType.HOSPITAL),
    ("Hư hỏng nhà do ngập nước", "Nước mưa làm hư trần và sàn gỗ sau đợt ngập; khách hàng đã gửi dự toán sửa chữa.", ClaimIncidentType.DAMAGE),
    ("Thất lạc hành lý khi đi du lịch", "Khách hàng báo hành lý bị chậm và thất lạc một phần trong chuyến đi.", ClaimIncidentType.OTHER),
]

CHAT_MESSAGES = [
    ("CUSTOMER", "Chào anh chị, tôi muốn hỏi hợp đồng của tôi có chi trả viện phí ngoại trú không?"),
    ("EMPLOYEE", "Chào anh chị, tôi sẽ kiểm tra gói bảo hiểm và phản hồi theo đúng quyền lợi hợp đồng."),
    ("CUSTOMER", "Hồ sơ bồi thường của tôi đã được tiếp nhận chưa?"),
    ("EMPLOYEE", "Hồ sơ đã được tiếp nhận. Anh chị vui lòng bổ sung hóa đơn gốc và hình ảnh hiện trường."),
    ("CUSTOMER", "Tôi có cần đặt lịch để nộp hồ sơ bản giấy không?"),
    ("EMPLOYEE", "Anh chị có thể đặt lịch trên hệ thống hoặc gửi trước bản scan để chúng tôi kiểm tra."),
]

RAG_DOCUMENTS = [
    ("Hướng dẫn quyền lợi bảo hiểm sức khỏe", "huong-dan-bao-hiem-suc-khoe.md", "text/markdown", """
Bảo hiểm sức khỏe cơ bản chi trả điều trị nội trú, cấp cứu và một lần khám sức khỏe định kỳ mỗi năm.
Bảo hiểm sức khỏe cao cấp bổ sung quyền lợi bệnh viện tư, phẫu thuật, bác sĩ chuyên khoa và thuốc điều trị.
Bảo hiểm sức khỏe gia đình áp dụng cho cha mẹ và con cái trong cùng hợp đồng, bao gồm nhi khoa và khám phòng ngừa.
Khách hàng cần nộp giấy ra viện, hóa đơn, đơn thuốc và giấy tờ tùy thân khi yêu cầu bồi thường y tế.
"""),
    ("Quy trình nộp hồ sơ bồi thường", "quy-trinh-boi-thuong.md", "text/markdown", """
Khách hàng nên thông báo sự cố sớm nhất có thể sau tai nạn, nhập viện, va chạm xe, thiệt hại tài sản hoặc mất hành lý.
Hồ sơ bồi thường gồm mẫu yêu cầu, số hợp đồng, giấy tờ tùy thân, mô tả sự kiện, hình ảnh, hóa đơn, hồ sơ y tế và biên bản công an khi cần.
Nhân viên xử lý trạng thái hồ sơ gồm chờ xử lý, đang xem xét, cần bổ sung hồ sơ, đã duyệt, từ chối và hoàn tất.
Nếu thiếu chứng từ, nhân viên sẽ yêu cầu khách hàng bổ sung trước khi trình duyệt.
"""),
    ("Câu hỏi thường gặp về bảo hiểm", "cau-hoi-thuong-gap.md", "text/markdown", """
Hợp đồng đang hiệu lực mới được xem xét bồi thường theo phạm vi quyền lợi và điều khoản loại trừ.
Hợp đồng chờ kích hoạt cần nhân viên xác nhận trước khi quyền lợi đầy đủ có hiệu lực.
Hợp đồng hết hạn hoặc đã hủy không chi trả cho sự cố phát sinh sau ngày kết thúc.
Bảo hiểm xe máy hỗ trợ bồi thường tai nạn, sửa chữa và cứu hộ kéo xe trong hạn mức.
Bảo hiểm nhà ở hỗ trợ cháy nổ, ngập nước, trộm cắp, sửa chữa và nơi ở tạm thời.
"""),
    ("Sổ tay chăm sóc khách hàng", "so-tay-cham-soc-khach-hang.md", "text/markdown", """
Nhân viên cần phản hồi lịch sự, xác minh danh tính khách hàng, kiểm tra trạng thái hợp đồng và giải thích quyền lợi dựa trên tài liệu công ty.
Với khách hàng được phân công, nhân viên có thể tạo ghi chú chăm sóc, quản lý lịch hẹn, xem xét hồ sơ bồi thường và yêu cầu bổ sung chứng từ.
Lịch hẹn có thể ở trạng thái chờ xử lý, đã chấp nhận, từ chối, đổi lịch, đã hủy hoặc hoàn tất.
Khách hàng nên dùng chat để hỏi về trạng thái hồ sơ, phạm vi bảo hiểm, thanh toán và lịch hẹn.
"""),
]

def _delete_all(db: Session, model: type) -> None:
    db.execute(delete(model))


def _slug(value: str) -> str:
    return value.lower().replace(" ", ".")


def _past_datetime(days_back: int, hour: int = 9) -> datetime:
    return datetime.now(UTC) - timedelta(days=days_back, hours=24 - hour)


def _ensure_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: UserRole,
) -> User:
    user = UserRepository.get_by_email(db, email)
    if user:
        user.password_hash = get_password_hash(password)
        user.full_name = full_name
        user.role = role
        user.status = UserStatus.ACTIVE
        return user

    payload = UserCreate(
        email=email,
        password=password,
        full_name=full_name,
        role=role,
        status=UserStatus.ACTIVE,
    )
    user = UserRepository.create_user(db, payload, get_password_hash(password))
    db.flush()
    return user


def seed_admin(db: Session, *, record_activity: bool = True) -> User:
    admin = _ensure_user(
        db,
        email=settings.SEED_ADMIN_EMAIL,
        password=settings.SEED_ADMIN_PASSWORD,
        full_name=settings.SEED_ADMIN_FULL_NAME,
        role=UserRole.ADMIN,
    )
    if record_activity:
        AuditRepository.record_activity(
            db,
            actor_user_id=admin.id,
            action="seed.admin.upsert",
            entity_type="user",
            entity_id=str(admin.id),
            metadata_json={"email": admin.email},
        )
    db.commit()
    return admin


def clean_demo_data(db: Session) -> None:
    _delete_all(db, ChatMessage)
    _delete_all(db, ChatRoom)
    _delete_all(db, Appointment)
    _delete_all(db, FollowUpNote)
    _delete_all(db, ClaimAttachment)
    _delete_all(db, Claim)
    _delete_all(db, CustomerInsuranceSubscription)
    _delete_all(db, CustomerAssignment)
    _delete_all(db, RagChatLog)
    _delete_all(db, RagRelationship)
    _delete_all(db, RagEntity)
    _delete_all(db, DocumentChunk)
    _delete_all(db, Document)
    _delete_all(db, LoginHistory)
    _delete_all(db, ActivityLog)
    _delete_all(db, Customer)
    _delete_all(db, Employee)
    db.execute(delete(InsurancePackage).where(InsurancePackage.code.in_(SEEDED_PACKAGE_CODES)))
    db.execute(
        delete(User).where(User.role.in_([UserRole.EMPLOYEE, UserRole.CUSTOMER]))
    )
    db.commit()


def seed_employees(db: Session) -> list[Employee]:
    employees: list[Employee] = []
    for index, (name, department, position, phone) in enumerate(EMPLOYEE_DATA, start=1):
        user = _ensure_user(
            db,
            email=f"nhanvien{index:03d}@{DEMO_EMPLOYEE_DOMAIN}",
            password=DEFAULT_PASSWORD,
            full_name=name,
            role=UserRole.EMPLOYEE,
        )
        employee = Employee(
            user_id=user.id,
            employee_code=f"EMP{index:03d}",
            department=department,
            position=f"{position} - điện thoại {phone}",
            hire_date=date(2020 + (index % 5), (index % 12) + 1, (index % 24) + 1),
        )
        db.add(employee)
        employees.append(employee)
    db.flush()
    return employees


def seed_customers(db: Session) -> list[Customer]:
    customers: list[Customer] = []
    for index in range(1, 81):
        full_name = (
            f"{FIRST_NAMES[index % len(FIRST_NAMES)]} "
            f"{MIDDLE_NAMES[index % len(MIDDLE_NAMES)]} "
            f"{GIVEN_NAMES[index % len(GIVEN_NAMES)]}"
        )
        city, district, street = CITIES[index % len(CITIES)]
        phone = f"09{index % 10}{(5000000 + index * 137):07d}"[:10]
        user = _ensure_user(
            db,
            email=f"customer{index:03d}@{DEMO_CUSTOMER_DOMAIN}",
            password=DEFAULT_PASSWORD,
            full_name=full_name,
            role=UserRole.CUSTOMER,
        )
        customer = Customer(
            user_id=user.id,
            customer_code=f"CUS{index:04d}",
            date_of_birth=date(1975 + (index % 28), (index % 12) + 1, (index % 26) + 1),
            address=f"{12 + index} {street}, {district}, {city}. Điện thoại: {phone}",
            identity_number=f"0{79 + index:02d}{100000000 + index:09d}",
        )
        db.add(customer)
        customers.append(customer)
    db.flush()
    return customers


def seed_packages_and_processes(db: Session) -> list[InsurancePackage]:
    packages: list[InsurancePackage] = []
    for code, name, package_type, description, premium, coverage, duration in PACKAGE_DEFINITIONS:
        package = InsurancePackage(
            code=code,
            name=name,
            package_type=package_type,
            description=description,
            premium_amount=Decimal(premium),
            coverage_amount=Decimal(coverage),
            duration_months=duration,
            status=InsuranceStatus.ACTIVE,
        )
        db.add(package)
        packages.append(package)
    db.flush()

    for package in packages:
        process = InsuranceProcess(
            package_id=package.id,
            name=f"Quy trình phê duyệt {package.name}",
            description=(
                f"Quy trình chuẩn cho {package.name}: tiếp nhận yêu cầu, "
                "nhân viên thẩm định, quản trị phê duyệt và thông báo khách hàng."
            ),
            status=InsuranceStatus.ACTIVE,
        )
        db.add(process)
        db.flush()
        steps = [
            ("Tiếp nhận yêu cầu khách hàng", UserRole.EMPLOYEE),
            ("Xác minh khách hàng và hợp đồng", UserRole.EMPLOYEE),
            ("Kiểm tra quyền lợi và điều khoản loại trừ", UserRole.EMPLOYEE),
            ("Phê duyệt hoặc từ chối yêu cầu", UserRole.ADMIN),
            ("Thông báo khách hàng và lưu hồ sơ", UserRole.EMPLOYEE),
        ]
        for step_order, (step_name, role) in enumerate(steps, start=1):
            db.add(
                ProcessStep(
                    process_id=process.id,
                    step_order=step_order,
                    name=step_name,
                    description=f"{step_name} cho {package.name}.",
                    required_role=role,
                )
            )
    db.flush()
    return packages


def seed_assignments(
    db: Session,
    *,
    customers: list[Customer],
    employees: list[Employee],
) -> list[CustomerAssignment]:
    assignments: list[CustomerAssignment] = []
    for index, customer in enumerate(customers):
        employee = employees[index % len(employees)]
        assignment = CustomerAssignment(
            customer_id=customer.id,
            employee_id=employee.id,
            status=AssignmentStatus.ACTIVE,
        )
        db.add(assignment)
        assignments.append(assignment)
    db.flush()
    return assignments


def seed_subscriptions(
    db: Session,
    *,
    customers: list[Customer],
    packages: list[InsurancePackage],
) -> list[CustomerInsuranceSubscription]:
    statuses = [
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.PENDING,
        SubscriptionStatus.EXPIRED,
        SubscriptionStatus.CANCELLED,
    ]
    payment_statuses = [PaymentStatus.PAID, PaymentStatus.UNPAID, PaymentStatus.OVERDUE]
    subscriptions: list[CustomerInsuranceSubscription] = []
    for index in range(120):
        customer = customers[index % len(customers)]
        package = packages[(index * 3) % len(packages)]
        status = statuses[index % len(statuses)]
        start = date(2025 + (index % 2), (index % 12) + 1, (index % 25) + 1)
        end = date(start.year + max(1, package.duration_months // 12), start.month, start.day)
        subscription = CustomerInsuranceSubscription(
            customer_id=customer.id,
            package_id=package.id,
            start_date=start,
            end_date=end,
            status=status,
            payment_status=payment_statuses[index % len(payment_statuses)],
            policy_number=f"VN-HD-{start.year}-{index + 1:05d}",
            premium_amount=package.premium_amount,
        )
        db.add(subscription)
        subscriptions.append(subscription)
    db.flush()
    return subscriptions


def seed_claims(
    db: Session,
    *,
    subscriptions: list[CustomerInsuranceSubscription],
    employees: list[Employee],
) -> list[Claim]:
    statuses = [
        ClaimStatus.PENDING,
        ClaimStatus.REVIEWING,
        ClaimStatus.NEED_MORE_DOCUMENTS,
        ClaimStatus.APPROVED,
        ClaimStatus.REJECTED,
        ClaimStatus.COMPLETED,
    ]
    priorities = [ClaimPriority.LOW, ClaimPriority.MEDIUM, ClaimPriority.HIGH, ClaimPriority.URGENT]
    claims: list[Claim] = []
    for index in range(60):
        scenario = CLAIM_SCENARIOS[index % len(CLAIM_SCENARIOS)]
        subscription = subscriptions[index % len(subscriptions)]
        claim = Claim(
            customer_id=subscription.customer_id,
            subscription_id=subscription.id,
            assigned_employee_id=employees[index % len(employees)].id,
            title=scenario[0],
            description=scenario[1],
            incident_type=scenario[2],
            incident_date=(datetime.now(UTC) - timedelta(days=10 + index * 3)).date(),
            location=CITIES[index % len(CITIES)][0],
            status=statuses[index % len(statuses)],
            priority=priorities[index % len(priorities)],
            review_note=(
                "Nhân viên đã kiểm tra chứng từ ban đầu và cập nhật trạng thái hồ sơ."
                if index % 3 == 0
                else None
            ),
        )
        db.add(claim)
        claims.append(claim)
    db.flush()
    for index, claim in enumerate(claims):
        db.add(
            ClaimAttachment(
                claim_id=claim.id,
                file_name=f"chung-tu-boi-thuong-{index + 1:03d}.pdf",
                file_url=f"https://demo.insurance.local/claims/{claim.id}/evidence.pdf",
                mime_type="application/pdf",
            )
        )
    db.flush()
    return claims


def seed_appointments(
    db: Session,
    *,
    assignments: list[CustomerAssignment],
) -> list[Appointment]:
    statuses = [
        AppointmentStatus.PENDING,
        AppointmentStatus.ACCEPTED,
        AppointmentStatus.REJECTED,
        AppointmentStatus.COMPLETED,
    ]
    appointments: list[Appointment] = []
    for index in range(40):
        assignment = assignments[index % len(assignments)]
        appointment = Appointment(
            customer_id=assignment.customer_id,
            employee_id=assignment.employee_id,
            scheduled_at=datetime.now(UTC) - timedelta(days=180 - index * 4),
            duration_minutes=[30, 45, 60][index % 3],
            status=statuses[index % len(statuses)],
            note=[
                "Tư vấn gia hạn hợp đồng bảo hiểm.",
                "Lịch kiểm tra chứng từ bồi thường.",
                "Trao đổi nâng cấp gói bảo hiểm sức khỏe.",
                "Giải thích quyền lợi bảo hiểm xe cơ giới.",
            ][index % 4],
        )
        db.add(appointment)
        appointments.append(appointment)
    db.flush()
    return appointments


def seed_chat(db: Session, *, assignments: list[CustomerAssignment]) -> None:
    rooms: list[ChatRoom] = []
    for assignment in assignments:
        room = ChatRoom(
            customer_id=assignment.customer_id,
            employee_id=assignment.employee_id,
        )
        db.add(room)
        rooms.append(room)
    db.flush()
    message_count = 0
    for room_index, room in enumerate(rooms):
        customer_user_id = room.customer.user_id
        employee_user_id = room.employee.user_id
        for message_index in range(3):
            role, content = CHAT_MESSAGES[(room_index + message_index) % len(CHAT_MESSAGES)]
            db.add(
                ChatMessage(
                    room_id=room.id,
                    sender_user_id=customer_user_id if role == "CUSTOMER" else employee_user_id,
                    content=content,
                    is_read=message_index < 2,
                    created_at=_past_datetime(120 - room_index, 8 + message_index),
                )
            )
            message_count += 1
    db.flush()
    if message_count < 200:
        raise RuntimeError("Demo chat seed did not create enough messages")


def seed_follow_up_notes(
    db: Session,
    *,
    assignments: list[CustomerAssignment],
) -> None:
    for index, assignment in enumerate(assignments):
        if index % 2 == 0:
            db.add(
                FollowUpNote(
                    customer_id=assignment.customer_id,
                    employee_id=assignment.employee_id,
                    note=[
                        "Gọi khách hàng xác nhận hóa đơn bồi thường còn thiếu.",
                        "Theo dõi quyết định gia hạn vào tuần tới.",
                        "Gửi bảng so sánh quyền lợi mới qua email.",
                        "Nhắc khách hàng tải giấy ra viện lên hệ thống.",
                    ][index % 4],
                    next_action_at=datetime.now(UTC) + timedelta(days=(index % 14) + 1),
                )
            )
    db.flush()


def seed_login_history(db: Session, *, users: list[User]) -> None:
    for user_index, user in enumerate(users):
        for attempt in range(3):
            db.add(
                LoginHistory(
                    user_id=user.id,
                    email=user.email,
                    ip_address=f"10.0.{user_index % 50}.{20 + attempt}",
                    user_agent="Mozilla/5.0 demo browser",
                    success=attempt != 0 or user_index % 7 != 0,
                    created_at=_past_datetime((user_index * 3 + attempt) % 365),
                )
            )
    db.flush()


def seed_activity_logs(
    db: Session,
    *,
    admin: User,
    employees: list[Employee],
    customers: list[Customer],
) -> None:
    actions = [
        ("admin.package.create", "insurance_package"),
        ("admin.assignment.create", "customer_assignment"),
        ("employee.claim.update_status", "claim"),
        ("employee.follow_up_note.create", "follow_up_note"),
        ("customer.chatbot.query", "document_chunks"),
    ]
    actors = [admin.id] + [employee.user_id for employee in employees]
    for index in range(160):
        action, entity_type = actions[index % len(actions)]
        db.add(
            ActivityLog(
                actor_user_id=actors[index % len(actors)],
                action=action,
                entity_type=entity_type,
                entity_id=str((index % max(1, len(customers))) + 1),
                metadata_json={"seeded": True, "batch": "rich_demo"},
                created_at=_past_datetime(index % 365),
            )
        )
    db.flush()


def seed_rag_documents(db: Session, *, admin: User) -> None:
    embedding_service = LocalEmbeddingService()
    for title, file_name, content_type, raw_text in RAG_DOCUMENTS:
        document = Document(
            title=title,
            file_name=file_name,
            content_type=content_type,
            raw_text=" ".join(raw_text.split()),
            processing_status="completed",
            page_count=0,
            extracted_character_count=len(" ".join(raw_text.split())),
            uploaded_by_user_id=admin.id,
        )
        db.add(document)
        db.flush()
        chunks: list[DocumentChunk] = []
        for chunk_index, chunk_text in enumerate(_chunk_text(document.raw_text, chunk_size=420, overlap=60)):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk_index,
                content=chunk_text,
                embedding_json=embedding_service.embed(chunk_text),
                token_count=len(_tokens(chunk_text)),
            )
            db.add(chunk)
            chunks.append(chunk)
        db.flush()
        GraphRagIngestionService.ingest_chunks(db, chunks=chunks)
        db.flush()
        document.chunk_count = len(chunks)
        document.entity_count = db.query(RagEntity).filter_by(document_id=document.id).count()
        document.relationship_count = (
            db.query(RagRelationship).filter_by(document_id=document.id).count()
        )
        chunk_lengths = [len(chunk.content or "") for chunk in chunks]
        document.average_chunk_length = (
            round(sum(chunk_lengths) / len(chunk_lengths)) if chunk_lengths else 0
        )
        document.max_chunk_length = max(chunk_lengths) if chunk_lengths else 0
        document.skipped_duplicate_chunks = 0
    db.flush()


def seed_demo_data(db: Session, *, actor: User) -> None:
    clean_demo_data(db)
    actor = seed_admin(db, record_activity=True)
    employees = seed_employees(db)
    customers = seed_customers(db)
    packages = seed_packages_and_processes(db)
    assignments = seed_assignments(db, customers=customers, employees=employees)
    subscriptions = seed_subscriptions(db, customers=customers, packages=packages)
    seed_claims(db, subscriptions=subscriptions, employees=employees)
    seed_appointments(db, assignments=assignments)
    seed_chat(db, assignments=assignments)
    seed_follow_up_notes(db, assignments=assignments)
    seed_rag_documents(db, admin=actor)
    all_users = [actor] + [employee.user for employee in employees] + [customer.user for customer in customers]
    seed_login_history(db, users=all_users)
    seed_activity_logs(db, admin=actor, employees=employees, customers=customers)
    db.commit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed insurance demo data.")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove demo data and keep the admin account.",
    )
    parser.add_argument(
        "--reseed",
        action="store_true",
        help="Clean demo data, then generate fresh demo data.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = SessionLocal()
    try:
        admin = seed_admin(db)
        if args.clean and not args.reseed:
            clean_demo_data(db)
            seed_admin(db, record_activity=False)
            return
        seed_demo_data(db, actor=admin)
    finally:
        db.close()


if __name__ == "__main__":
    main()
