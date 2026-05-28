from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.customer_management import (
    AssignmentStatus,
    Customer,
    CustomerAssignment,
    Employee,
    FollowUpNote,
)
from app.models.user import User
from app.schemas.customer_management import (
    CustomerAssignmentCreate,
    CustomerCreate,
    EmployeeCreate,
    FollowUpNoteCreate,
)


class EmployeeRepository:
    @staticmethod
    def get_by_id(db: Session, employee_id: int) -> Employee | None:
        return db.scalar(
            select(Employee)
            .options(joinedload(Employee.user))
            .where(Employee.id == employee_id)
        )

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Employee | None:
        return db.scalar(
            select(Employee)
            .options(joinedload(Employee.user))
            .where(Employee.user_id == user_id)
        )

    @staticmethod
    def get_by_code(db: Session, employee_code: str) -> Employee | None:
        return db.scalar(
            select(Employee).where(
                func.lower(Employee.employee_code) == employee_code.lower()
            )
        )

    @staticmethod
    def list_employees(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> list[Employee]:
        query: Select[tuple[Employee]] = (
            select(Employee)
            .options(joinedload(Employee.user))
            .join(Employee.user)
            .order_by(Employee.created_at.desc())
        )
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                func.lower(Employee.employee_code).like(pattern)
                | func.lower(Employee.department).like(pattern)
                | func.lower(Employee.position).like(pattern)
                | func.lower(User.email).like(pattern)
                | func.lower(User.full_name).like(pattern)
            )
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_employee(
        db: Session,
        *,
        payload: EmployeeCreate,
        user: User,
    ) -> Employee:
        employee = Employee(
            user_id=user.id,
            employee_code=payload.employee_code,
            department=payload.department,
            position=payload.position,
            hire_date=payload.hire_date,
        )
        db.add(employee)
        return employee


class CustomerRepository:
    @staticmethod
    def get_by_id(db: Session, customer_id: int) -> Customer | None:
        return db.scalar(
            select(Customer)
            .options(joinedload(Customer.user))
            .where(Customer.id == customer_id)
        )

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Customer | None:
        return db.scalar(
            select(Customer)
            .options(joinedload(Customer.user))
            .where(Customer.user_id == user_id)
        )

    @staticmethod
    def get_by_code(db: Session, customer_code: str) -> Customer | None:
        return db.scalar(
            select(Customer).where(
                func.lower(Customer.customer_code) == customer_code.lower()
            )
        )

    @staticmethod
    def get_by_identity_number(
        db: Session,
        identity_number: str,
    ) -> Customer | None:
        return db.scalar(
            select(Customer).where(Customer.identity_number == identity_number)
        )

    @staticmethod
    def list_customers(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> list[Customer]:
        query: Select[tuple[Customer]] = (
            select(Customer)
            .options(joinedload(Customer.user))
            .join(Customer.user)
            .order_by(Customer.created_at.desc())
        )
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                func.lower(Customer.customer_code).like(pattern)
                | func.lower(Customer.identity_number).like(pattern)
                | func.lower(User.email).like(pattern)
                | func.lower(User.full_name).like(pattern)
            )
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_customer(
        db: Session,
        *,
        payload: CustomerCreate,
        user: User,
    ) -> Customer:
        customer = Customer(
            user_id=user.id,
            customer_code=payload.customer_code,
            date_of_birth=payload.date_of_birth,
            address=payload.address,
            identity_number=payload.identity_number,
        )
        db.add(customer)
        return customer


class AssignmentRepository:
    @staticmethod
    def get_by_id(db: Session, assignment_id: int) -> CustomerAssignment | None:
        return db.scalar(
            select(CustomerAssignment)
            .options(
                joinedload(CustomerAssignment.customer).joinedload(Customer.user),
                joinedload(CustomerAssignment.employee).joinedload(Employee.user),
            )
            .where(CustomerAssignment.id == assignment_id)
        )

    @staticmethod
    def get_active_for_customer(
        db: Session,
        customer_id: int,
    ) -> CustomerAssignment | None:
        return db.scalar(
            select(CustomerAssignment)
            .options(
                joinedload(CustomerAssignment.customer).joinedload(Customer.user),
                joinedload(CustomerAssignment.employee).joinedload(Employee.user),
            )
            .where(
                CustomerAssignment.customer_id == customer_id,
                CustomerAssignment.status == AssignmentStatus.ACTIVE,
            )
            .order_by(CustomerAssignment.created_at.desc())
        )

    @staticmethod
    def list_assignments(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        status_filter: AssignmentStatus | None = None,
    ) -> list[CustomerAssignment]:
        query: Select[tuple[CustomerAssignment]] = (
            select(CustomerAssignment)
            .options(
                joinedload(CustomerAssignment.customer).joinedload(Customer.user),
                joinedload(CustomerAssignment.employee).joinedload(Employee.user),
            )
            .order_by(CustomerAssignment.created_at.desc())
        )
        if status_filter:
            query = query.where(CustomerAssignment.status == status_filter)
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def list_active_for_employee(
        db: Session,
        employee_id: int,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CustomerAssignment]:
        query = (
            select(CustomerAssignment)
            .options(
                joinedload(CustomerAssignment.customer).joinedload(Customer.user),
                joinedload(CustomerAssignment.employee).joinedload(Employee.user),
            )
            .where(
                CustomerAssignment.employee_id == employee_id,
                CustomerAssignment.status == AssignmentStatus.ACTIVE,
            )
            .order_by(CustomerAssignment.created_at.desc())
        )
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_assignment(
        db: Session,
        payload: CustomerAssignmentCreate,
    ) -> CustomerAssignment:
        assignment = CustomerAssignment(**payload.model_dump())
        db.add(assignment)
        return assignment


class FollowUpNoteRepository:
    @staticmethod
    def list_for_customer(
        db: Session,
        customer_id: int,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FollowUpNote]:
        query = (
            select(FollowUpNote)
            .options(
                joinedload(FollowUpNote.customer).joinedload(Customer.user),
                joinedload(FollowUpNote.employee).joinedload(Employee.user),
            )
            .where(FollowUpNote.customer_id == customer_id)
            .order_by(FollowUpNote.created_at.desc())
        )
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_note(
        db: Session,
        *,
        customer_id: int,
        employee_id: int,
        payload: FollowUpNoteCreate,
    ) -> FollowUpNote:
        note = FollowUpNote(
            customer_id=customer_id,
            employee_id=employee_id,
            note=payload.note,
            next_action_at=payload.next_action_at,
        )
        db.add(note)
        return note
