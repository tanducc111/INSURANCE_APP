from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.customer_management import (
    AssignmentStatus,
    Customer,
    CustomerAssignment,
    Employee,
)
from app.models.insurance import InsurancePackage, InsuranceStatus
from app.models.subscription import (
    CustomerInsuranceSubscription,
    PaymentStatus,
    SubscriptionStatus,
)
from app.models.user import User, UserRole, UserStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.customer_management_repository import (
    AssignmentRepository,
    CustomerRepository,
    EmployeeRepository,
)
from app.repositories.insurance_repository import InsurancePackageRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate

DEMO_EMPLOYEE_EMAIL = "employee@insurance.local"
DEMO_EMPLOYEE_PASSWORD = "11111111"
DEMO_EMPLOYEE_CODE = "EMP-DEMO-001"

DEMO_CUSTOMER_EMAIL = "customer@insurance.local"
DEMO_CUSTOMER_PASSWORD = "11111111"
DEMO_CUSTOMER_CODE = "CUS-DEMO-001"

DEMO_PACKAGE_CODE = "PKG-DEMO-HEALTH"
DEMO_POLICY_NUMBER = "POL-DEMO-0001"


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


def seed_admin(db: Session) -> User:
    admin = _ensure_user(
        db,
        email=settings.SEED_ADMIN_EMAIL,
        password=settings.SEED_ADMIN_PASSWORD,
        full_name=settings.SEED_ADMIN_FULL_NAME,
        role=UserRole.ADMIN,
    )
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


def _ensure_demo_employee(db: Session, actor: User) -> Employee:
    user = _ensure_user(
        db,
        email=DEMO_EMPLOYEE_EMAIL,
        password=DEMO_EMPLOYEE_PASSWORD,
        full_name="Demo Employee",
        role=UserRole.EMPLOYEE,
    )
    employee = EmployeeRepository.get_by_code(db, DEMO_EMPLOYEE_CODE)
    if employee is None:
        employee = Employee(
            user_id=user.id,
            employee_code=DEMO_EMPLOYEE_CODE,
            department="Customer Success",
            position="Insurance Advisor",
            hire_date=date(2026, 1, 10),
        )
        db.add(employee)
        db.flush()
    else:
        employee.user_id = user.id
        employee.department = "Customer Success"
        employee.position = "Insurance Advisor"
        employee.hire_date = date(2026, 1, 10)

    AuditRepository.record_activity(
        db,
        actor_user_id=actor.id,
        action="seed.employee.upsert",
        entity_type="employee",
        entity_id=str(employee.id),
        metadata_json={"employee_code": employee.employee_code},
    )
    return employee


def _ensure_demo_customer(db: Session, actor: User) -> Customer:
    user = _ensure_user(
        db,
        email=DEMO_CUSTOMER_EMAIL,
        password=DEMO_CUSTOMER_PASSWORD,
        full_name="Demo Customer",
        role=UserRole.CUSTOMER,
    )
    customer = CustomerRepository.get_by_code(db, DEMO_CUSTOMER_CODE)
    if customer is None:
        customer = Customer(
            user_id=user.id,
            customer_code=DEMO_CUSTOMER_CODE,
            date_of_birth=date(1990, 5, 20),
            address="123 Demo Street",
            identity_number="DEMO-ID-001",
        )
        db.add(customer)
        db.flush()
    else:
        customer.user_id = user.id
        customer.date_of_birth = date(1990, 5, 20)
        customer.address = "123 Demo Street"
        customer.identity_number = "DEMO-ID-001"

    AuditRepository.record_activity(
        db,
        actor_user_id=actor.id,
        action="seed.customer.upsert",
        entity_type="customer",
        entity_id=str(customer.id),
        metadata_json={"customer_code": customer.customer_code},
    )
    return customer


def _ensure_demo_package(db: Session, actor: User) -> InsurancePackage:
    package = InsurancePackageRepository.get_by_code(db, DEMO_PACKAGE_CODE)
    if package is None:
        package = InsurancePackage(
            code=DEMO_PACKAGE_CODE,
            name="Demo Health Protection",
            package_type="Health",
            description="Demo package for local walkthroughs.",
            premium_amount=Decimal("120.00"),
            coverage_amount=Decimal("10000.00"),
            duration_months=12,
            status=InsuranceStatus.ACTIVE,
        )
        db.add(package)
        db.flush()
    else:
        package.name = "Demo Health Protection"
        package.package_type = "Health"
        package.description = "Demo package for local walkthroughs."
        package.premium_amount = Decimal("120.00")
        package.coverage_amount = Decimal("10000.00")
        package.duration_months = 12
        package.status = InsuranceStatus.ACTIVE

    AuditRepository.record_activity(
        db,
        actor_user_id=actor.id,
        action="seed.package.upsert",
        entity_type="insurance_package",
        entity_id=str(package.id),
        metadata_json={"code": package.code},
    )
    return package


def _ensure_demo_assignment(
    db: Session,
    *,
    customer: Customer,
    employee: Employee,
    actor: User,
) -> CustomerAssignment:
    assignment = AssignmentRepository.get_active_for_customer(db, customer.id)
    if assignment is None:
        assignment = CustomerAssignment(
            customer_id=customer.id,
            employee_id=employee.id,
            status=AssignmentStatus.ACTIVE,
        )
        db.add(assignment)
        db.flush()
    else:
        assignment.employee_id = employee.id
        assignment.status = AssignmentStatus.ACTIVE

    AuditRepository.record_activity(
        db,
        actor_user_id=actor.id,
        action="seed.assignment.upsert",
        entity_type="customer_assignment",
        entity_id=str(assignment.id),
        metadata_json={
            "customer_id": customer.id,
            "employee_id": employee.id,
        },
    )
    return assignment


def _ensure_demo_subscription(
    db: Session,
    *,
    customer: Customer,
    package: InsurancePackage,
    actor: User,
) -> CustomerInsuranceSubscription:
    subscription = SubscriptionRepository.get_by_policy_number(
        db,
        DEMO_POLICY_NUMBER,
    )
    if subscription is None:
        subscription = CustomerInsuranceSubscription(
            customer_id=customer.id,
            package_id=package.id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=SubscriptionStatus.ACTIVE,
            payment_status=PaymentStatus.PAID,
            policy_number=DEMO_POLICY_NUMBER,
            premium_amount=Decimal("120.00"),
        )
        db.add(subscription)
        db.flush()
    else:
        subscription.customer_id = customer.id
        subscription.package_id = package.id
        subscription.start_date = date(2026, 1, 1)
        subscription.end_date = date(2026, 12, 31)
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.payment_status = PaymentStatus.PAID
        subscription.premium_amount = Decimal("120.00")

    AuditRepository.record_activity(
        db,
        actor_user_id=actor.id,
        action="seed.subscription.upsert",
        entity_type="customer_insurance_subscription",
        entity_id=str(subscription.id),
        metadata_json={"policy_number": subscription.policy_number},
    )
    return subscription


def seed_demo_data(db: Session, *, actor: User) -> None:
    employee = _ensure_demo_employee(db, actor)
    customer = _ensure_demo_customer(db, actor)
    package = _ensure_demo_package(db, actor)
    _ensure_demo_assignment(db, customer=customer, employee=employee, actor=actor)
    _ensure_demo_subscription(db, customer=customer, package=package, actor=actor)
    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        admin = seed_admin(db)
        seed_demo_data(db, actor=admin)
    finally:
        db.close()


if __name__ == "__main__":
    main()
