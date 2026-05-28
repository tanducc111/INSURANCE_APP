from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user, require_roles
from app.db.session import get_db
from app.models.customer_management import (
    AssignmentStatus,
    Customer,
    CustomerAssignment,
    Employee,
    FollowUpNote,
)
from app.models.user import User, UserRole
from app.schemas.customer_management import (
    CustomerAssignmentCreate,
    CustomerAssignmentRead,
    CustomerAssignmentUpdate,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
    FollowUpNoteCreate,
    FollowUpNoteRead,
)
from app.services.customer_management_service import (
    AssignmentService,
    CustomerService,
    EmployeeService,
    FollowUpNoteService,
)

router = APIRouter(tags=["customer-management"])


@router.post("/admin/employees", response_model=EmployeeRead, status_code=201)
async def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Employee:
    return EmployeeService.create_employee(db, payload=payload, actor=current_admin)


@router.get("/admin/employees", response_model=list[EmployeeRead])
async def list_employees(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[Employee]:
    _ = current_admin
    return EmployeeService.list_employees(
        db,
        skip=skip,
        limit=limit,
        search=search,
    )


@router.patch("/admin/employees/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Employee:
    return EmployeeService.update_employee(
        db,
        employee_id=employee_id,
        payload=payload,
        actor=current_admin,
    )


@router.post("/admin/customers", response_model=CustomerRead, status_code=201)
async def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Customer:
    return CustomerService.create_customer(db, payload=payload, actor=current_admin)


@router.get("/admin/customers", response_model=list[CustomerRead])
async def list_customers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[Customer]:
    _ = current_admin
    return CustomerService.list_customers(
        db,
        skip=skip,
        limit=limit,
        search=search,
    )


@router.patch("/admin/customers/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Customer:
    return CustomerService.update_customer(
        db,
        customer_id=customer_id,
        payload=payload,
        actor=current_admin,
    )


@router.post(
    "/admin/assignments",
    response_model=CustomerAssignmentRead,
    status_code=201,
)
async def assign_customer(
    payload: CustomerAssignmentCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> CustomerAssignment:
    return AssignmentService.create_assignment(
        db,
        payload=payload,
        actor=current_admin,
    )


@router.get("/admin/assignments", response_model=list[CustomerAssignmentRead])
async def list_assignments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: AssignmentStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[CustomerAssignment]:
    _ = current_admin
    return AssignmentService.list_assignments(
        db,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


@router.patch(
    "/admin/assignments/{assignment_id}/status",
    response_model=CustomerAssignmentRead,
)
async def update_assignment_status(
    assignment_id: int,
    payload: CustomerAssignmentUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> CustomerAssignment:
    return AssignmentService.update_assignment_status(
        db,
        assignment_id=assignment_id,
        payload=payload,
        actor=current_admin,
    )


@router.get("/employee/customers", response_model=list[CustomerRead])
async def list_assigned_customers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> list[Customer]:
    return AssignmentService.list_assigned_customers(
        db,
        user=current_employee,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/employee/customers/{customer_id}/follow-up-notes",
    response_model=list[FollowUpNoteRead],
)
async def list_follow_up_notes(
    customer_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> list[FollowUpNote]:
    return FollowUpNoteService.list_notes_for_assigned_customer(
        db,
        customer_id=customer_id,
        user=current_employee,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/employee/customers/{customer_id}/follow-up-notes",
    response_model=FollowUpNoteRead,
    status_code=201,
)
async def create_follow_up_note(
    customer_id: int,
    payload: FollowUpNoteCreate,
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> FollowUpNote:
    return FollowUpNoteService.create_note_for_assigned_customer(
        db,
        customer_id=customer_id,
        payload=payload,
        actor=current_employee,
    )


@router.get("/customer/profile", response_model=CustomerRead)
async def get_customer_profile(
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> Customer:
    return CustomerService.get_current_customer(db, user=current_customer)


@router.get("/customer/assigned-employee", response_model=EmployeeRead | None)
async def get_assigned_employee(
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> Employee | None:
    return AssignmentService.get_assigned_employee_for_customer(
        db,
        user=current_customer,
    )
