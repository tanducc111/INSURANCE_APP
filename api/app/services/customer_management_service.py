from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.customer_management import (
    AssignmentStatus,
    Customer,
    CustomerAssignment,
    Employee,
    FollowUpNote,
)
from app.models.user import User, UserRole
from app.repositories.audit_repository import AuditRepository
from app.repositories.customer_management_repository import (
    AssignmentRepository,
    CustomerRepository,
    EmployeeRepository,
    FollowUpNoteRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.customer_management import (
    CustomerAssignmentCreate,
    CustomerAssignmentUpdate,
    CustomerCreate,
    CustomerUpdate,
    EmployeeCreate,
    EmployeeUpdate,
    FollowUpNoteCreate,
)
from app.schemas.user import UserCreate


def _create_role_user(
    db: Session,
    payload: EmployeeCreate | CustomerCreate,
    role: UserRole,
) -> User:
    existing_user = UserRepository.get_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user_payload = UserCreate(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=role,
        status=payload.status,
    )
    user = UserRepository.create_user(
        db,
        user_payload,
        get_password_hash(payload.password),
    )
    db.flush()
    return user


class EmployeeService:
    @staticmethod
    def create_employee(db: Session, *, payload: EmployeeCreate, actor: User) -> Employee:
        if EmployeeRepository.get_by_code(db, payload.employee_code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee code already exists",
            )

        user = _create_role_user(db, payload, UserRole.EMPLOYEE)
        employee = EmployeeRepository.create_employee(db, payload=payload, user=user)
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.employee.create",
            entity_type="employee",
            entity_id=str(employee.id),
            metadata_json={"employee_code": employee.employee_code},
        )
        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def list_employees(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> list[Employee]:
        return EmployeeRepository.list_employees(
            db,
            skip=skip,
            limit=min(limit, 100),
            search=search,
        )

    @staticmethod
    def update_employee(
        db: Session,
        *,
        employee_id: int,
        payload: EmployeeUpdate,
        actor: User,
    ) -> Employee:
        employee = EmployeeRepository.get_by_id(db, employee_id)
        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if "employee_code" in update_data:
            existing_employee = EmployeeRepository.get_by_code(
                db,
                update_data["employee_code"],
            )
            if existing_employee and existing_employee.id != employee.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Employee code already exists",
                )

        user_fields = {"full_name", "status"}
        for field, value in update_data.items():
            if field in user_fields:
                setattr(employee.user, field, value)
            else:
                setattr(employee, field, value)

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.employee.update",
            entity_type="employee",
            entity_id=str(employee.id),
            metadata_json={"fields": sorted(update_data.keys())},
        )
        db.commit()
        db.refresh(employee)
        return employee


class CustomerService:
    @staticmethod
    def create_customer(db: Session, *, payload: CustomerCreate, actor: User) -> Customer:
        if CustomerRepository.get_by_code(db, payload.customer_code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer code already exists",
            )
        if payload.identity_number and CustomerRepository.get_by_identity_number(
            db,
            payload.identity_number,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Identity number already exists",
            )

        user = _create_role_user(db, payload, UserRole.CUSTOMER)
        customer = CustomerRepository.create_customer(db, payload=payload, user=user)
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.customer.create",
            entity_type="customer",
            entity_id=str(customer.id),
            metadata_json={"customer_code": customer.customer_code},
        )
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def list_customers(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> list[Customer]:
        return CustomerRepository.list_customers(
            db,
            skip=skip,
            limit=min(limit, 100),
            search=search,
        )

    @staticmethod
    def update_customer(
        db: Session,
        *,
        customer_id: int,
        payload: CustomerUpdate,
        actor: User,
    ) -> Customer:
        customer = CustomerRepository.get_by_id(db, customer_id)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if "customer_code" in update_data:
            existing_customer = CustomerRepository.get_by_code(
                db,
                update_data["customer_code"],
            )
            if existing_customer and existing_customer.id != customer.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Customer code already exists",
                )
        if update_data.get("identity_number"):
            existing_customer = CustomerRepository.get_by_identity_number(
                db,
                update_data["identity_number"],
            )
            if existing_customer and existing_customer.id != customer.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Identity number already exists",
                )

        user_fields = {"full_name", "status"}
        for field, value in update_data.items():
            if field in user_fields:
                setattr(customer.user, field, value)
            else:
                setattr(customer, field, value)

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.customer.update",
            entity_type="customer",
            entity_id=str(customer.id),
            metadata_json={"fields": sorted(update_data.keys())},
        )
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def get_current_customer(db: Session, *, user: User) -> Customer:
        customer = CustomerRepository.get_by_user_id(db, user.id)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found",
            )
        return customer


class AssignmentService:
    @staticmethod
    def create_assignment(
        db: Session,
        *,
        payload: CustomerAssignmentCreate,
        actor: User,
    ) -> CustomerAssignment:
        customer = CustomerRepository.get_by_id(db, payload.customer_id)
        employee = EmployeeRepository.get_by_id(db, payload.employee_id)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )
        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        if payload.status == AssignmentStatus.ACTIVE:
            active_assignment = AssignmentRepository.get_active_for_customer(
                db,
                payload.customer_id,
            )
            if active_assignment:
                active_assignment.status = AssignmentStatus.INACTIVE

        assignment = AssignmentRepository.create_assignment(db, payload)
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.assignment.create",
            entity_type="customer_assignment",
            entity_id=str(assignment.id),
            metadata_json={
                "customer_id": assignment.customer_id,
                "employee_id": assignment.employee_id,
                "status": assignment.status.value,
            },
        )
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def list_assignments(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        status_filter: AssignmentStatus | None = None,
    ) -> list[CustomerAssignment]:
        return AssignmentRepository.list_assignments(
            db,
            skip=skip,
            limit=min(limit, 100),
            status_filter=status_filter,
        )

    @staticmethod
    def update_assignment_status(
        db: Session,
        *,
        assignment_id: int,
        payload: CustomerAssignmentUpdate,
        actor: User,
    ) -> CustomerAssignment:
        assignment = AssignmentRepository.get_by_id(db, assignment_id)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )

        if payload.status == AssignmentStatus.ACTIVE:
            active_assignment = AssignmentRepository.get_active_for_customer(
                db,
                assignment.customer_id,
            )
            if active_assignment and active_assignment.id != assignment.id:
                active_assignment.status = AssignmentStatus.INACTIVE

        assignment.status = payload.status
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.assignment.update_status",
            entity_type="customer_assignment",
            entity_id=str(assignment.id),
            metadata_json={"status": assignment.status.value},
        )
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def list_assigned_customers(
        db: Session,
        *,
        user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Customer]:
        employee = EmployeeRepository.get_by_user_id(db, user.id)
        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile not found",
            )
        assignments = AssignmentRepository.list_active_for_employee(
            db,
            employee.id,
            skip=skip,
            limit=min(limit, 100),
        )
        return [assignment.customer for assignment in assignments]

    @staticmethod
    def get_assigned_employee_for_customer(
        db: Session,
        *,
        user: User,
    ) -> Employee | None:
        customer = CustomerService.get_current_customer(db, user=user)
        assignment = AssignmentRepository.get_active_for_customer(db, customer.id)
        return assignment.employee if assignment else None

    @staticmethod
    def ensure_employee_assignment(
        db: Session,
        *,
        user: User,
        customer_id: int,
    ) -> Employee:
        employee = EmployeeRepository.get_by_user_id(db, user.id)
        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile not found",
            )
        active_assignment = AssignmentRepository.get_active_for_customer(
            db,
            customer_id,
        )
        if active_assignment is None or active_assignment.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customer is not assigned to this employee",
            )
        return employee


class FollowUpNoteService:
    @staticmethod
    def list_notes_for_assigned_customer(
        db: Session,
        *,
        customer_id: int,
        user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FollowUpNote]:
        AssignmentService.ensure_employee_assignment(
            db,
            user=user,
            customer_id=customer_id,
        )
        return FollowUpNoteRepository.list_for_customer(
            db,
            customer_id,
            skip=skip,
            limit=min(limit, 100),
        )

    @staticmethod
    def create_note_for_assigned_customer(
        db: Session,
        *,
        customer_id: int,
        payload: FollowUpNoteCreate,
        actor: User,
    ) -> FollowUpNote:
        employee = AssignmentService.ensure_employee_assignment(
            db,
            user=actor,
            customer_id=customer_id,
        )
        note = FollowUpNoteRepository.create_note(
            db,
            customer_id=customer_id,
            employee_id=employee.id,
            payload=payload,
        )
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="employee.follow_up_note.create",
            entity_type="follow_up_note",
            entity_id=str(note.id),
            metadata_json={"customer_id": customer_id},
        )
        db.commit()
        db.refresh(note)
        return note
