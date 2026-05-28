from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user, require_roles
from app.db.session import get_db
from app.models.insurance import (
    InsurancePackage,
    InsuranceProcess,
    InsuranceStatus,
    ProcessStep,
)
from app.models.user import User, UserRole
from app.schemas.insurance import (
    InsurancePackageCreate,
    InsurancePackageRead,
    InsurancePackageUpdate,
    InsuranceProcessCreate,
    InsuranceProcessRead,
    InsuranceProcessUpdate,
    ProcessStepCreate,
    ProcessStepRead,
    ProcessStepUpdate,
)
from app.services.insurance_service import (
    InsurancePackageService,
    InsuranceProcessService,
    ProcessStepService,
)

router = APIRouter(prefix="/insurance", tags=["insurance"])


@router.get("/packages", response_model=list[InsurancePackageRead])
async def list_packages(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    status_filter: InsuranceStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[InsurancePackage]:
    return InsurancePackageService.list_packages(
        db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        search=search,
        status_filter=status_filter,
    )


@router.post(
    "/packages",
    response_model=InsurancePackageRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_package(
    payload: InsurancePackageCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> InsurancePackage:
    return InsurancePackageService.create_package(
        db,
        payload=payload,
        actor=current_admin,
    )


@router.get("/packages/{package_id}", response_model=InsurancePackageRead)
async def get_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InsurancePackage:
    return InsurancePackageService.get_package(
        db,
        package_id=package_id,
        current_user=current_user,
    )


@router.patch("/packages/{package_id}", response_model=InsurancePackageRead)
async def update_package(
    package_id: int,
    payload: InsurancePackageUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> InsurancePackage:
    return InsurancePackageService.update_package(
        db,
        package_id=package_id,
        payload=payload,
        actor=current_admin,
    )


@router.delete("/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Response:
    InsurancePackageService.delete_package(
        db,
        package_id=package_id,
        actor=current_admin,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/processes", response_model=list[InsuranceProcessRead])
async def list_processes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    package_id: int | None = Query(default=None),
    search: str | None = Query(default=None, max_length=255),
    status_filter: InsuranceStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[InsuranceProcess]:
    return InsuranceProcessService.list_processes(
        db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        package_id=package_id,
        search=search,
        status_filter=status_filter,
    )


@router.post(
    "/processes",
    response_model=InsuranceProcessRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_process(
    payload: InsuranceProcessCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> InsuranceProcess:
    return InsuranceProcessService.create_process(
        db,
        payload=payload,
        actor=current_admin,
    )


@router.get("/processes/{process_id}", response_model=InsuranceProcessRead)
async def get_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InsuranceProcess:
    return InsuranceProcessService.get_process(
        db,
        process_id=process_id,
        current_user=current_user,
    )


@router.patch("/processes/{process_id}", response_model=InsuranceProcessRead)
async def update_process(
    process_id: int,
    payload: InsuranceProcessUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> InsuranceProcess:
    return InsuranceProcessService.update_process(
        db,
        process_id=process_id,
        payload=payload,
        actor=current_admin,
    )


@router.delete("/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Response:
    InsuranceProcessService.delete_process(
        db,
        process_id=process_id,
        actor=current_admin,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/processes/{process_id}/steps", response_model=list[ProcessStepRead])
async def list_steps(
    process_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ProcessStep]:
    return ProcessStepService.list_steps(
        db,
        process_id=process_id,
        current_user=current_user,
        skip=skip,
        limit=limit,
        search=search,
    )


@router.post(
    "/processes/{process_id}/steps",
    response_model=ProcessStepRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_step(
    process_id: int,
    payload: ProcessStepCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> ProcessStep:
    return ProcessStepService.create_step(
        db,
        process_id=process_id,
        payload=payload,
        actor=current_admin,
    )


@router.get("/steps/{step_id}", response_model=ProcessStepRead)
async def get_step(
    step_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProcessStep:
    return ProcessStepService.get_step(
        db,
        step_id=step_id,
        current_user=current_user,
    )


@router.patch("/steps/{step_id}", response_model=ProcessStepRead)
async def update_step(
    step_id: int,
    payload: ProcessStepUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> ProcessStep:
    return ProcessStepService.update_step(
        db,
        step_id=step_id,
        payload=payload,
        actor=current_admin,
    )


@router.delete("/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_step(
    step_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Response:
    ProcessStepService.delete_step(db, step_id=step_id, actor=current_admin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
