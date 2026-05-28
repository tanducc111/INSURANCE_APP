from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.insurance import (
    InsurancePackage,
    InsuranceProcess,
    InsuranceStatus,
    ProcessStep,
)
from app.models.user import User, UserRole
from app.repositories.audit_repository import AuditRepository
from app.repositories.insurance_repository import (
    InsurancePackageRepository,
    InsuranceProcessRepository,
    ProcessStepRepository,
)
from app.schemas.insurance import (
    InsurancePackageCreate,
    InsurancePackageUpdate,
    InsuranceProcessCreate,
    InsuranceProcessUpdate,
    ProcessStepCreate,
    ProcessStepUpdate,
)


def _is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


def _ensure_package_visible(package: InsurancePackage, user: User) -> None:
    if not _is_admin(user) and package.status != InsuranceStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance package not found",
        )


def _ensure_process_visible(process: InsuranceProcess, user: User) -> None:
    if not _is_admin(user) and (
        process.status != InsuranceStatus.ACTIVE
        or process.package.status != InsuranceStatus.ACTIVE
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance process not found",
        )


class InsurancePackageService:
    @staticmethod
    def list_packages(
        db: Session,
        *,
        current_user: User,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status_filter: InsuranceStatus | None = None,
    ) -> list[InsurancePackage]:
        return InsurancePackageRepository.list_packages(
            db,
            skip=skip,
            limit=min(limit, 100),
            search=search,
            status_filter=status_filter,
            active_only=not _is_admin(current_user),
        )

    @staticmethod
    def get_package(
        db: Session,
        *,
        package_id: int,
        current_user: User,
    ) -> InsurancePackage:
        package = InsurancePackageRepository.get_by_id(db, package_id)
        if package is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance package not found",
            )
        _ensure_package_visible(package, current_user)
        return package

    @staticmethod
    def create_package(
        db: Session,
        *,
        payload: InsurancePackageCreate,
        actor: User,
    ) -> InsurancePackage:
        existing_package = InsurancePackageRepository.get_by_code(db, payload.code)
        if existing_package:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Package code already exists",
            )

        package = InsurancePackageRepository.create_package(db, payload)
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.insurance_package.create",
            entity_type="insurance_package",
            entity_id=str(package.id),
            metadata_json={"code": package.code, "status": package.status.value},
        )
        db.commit()
        db.refresh(package)
        return package

    @staticmethod
    def update_package(
        db: Session,
        *,
        package_id: int,
        payload: InsurancePackageUpdate,
        actor: User,
    ) -> InsurancePackage:
        package = InsurancePackageRepository.get_by_id(db, package_id)
        if package is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance package not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if "code" in update_data:
            existing_package = InsurancePackageRepository.get_by_code(
                db,
                update_data["code"],
            )
            if existing_package and existing_package.id != package.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Package code already exists",
                )

        for field, value in update_data.items():
            setattr(package, field, value)

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.insurance_package.update",
            entity_type="insurance_package",
            entity_id=str(package.id),
            metadata_json={"fields": sorted(update_data.keys())},
        )
        db.commit()
        db.refresh(package)
        return package

    @staticmethod
    def delete_package(db: Session, *, package_id: int, actor: User) -> None:
        package = InsurancePackageRepository.get_by_id(db, package_id)
        if package is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance package not found",
            )

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.insurance_package.delete",
            entity_type="insurance_package",
            entity_id=str(package.id),
            metadata_json={"code": package.code},
        )
        InsurancePackageRepository.delete_package(db, package)
        db.commit()


class InsuranceProcessService:
    @staticmethod
    def list_processes(
        db: Session,
        *,
        current_user: User,
        skip: int = 0,
        limit: int = 50,
        package_id: int | None = None,
        search: str | None = None,
        status_filter: InsuranceStatus | None = None,
    ) -> list[InsuranceProcess]:
        return InsuranceProcessRepository.list_processes(
            db,
            skip=skip,
            limit=min(limit, 100),
            package_id=package_id,
            search=search,
            status_filter=status_filter,
            active_only=not _is_admin(current_user),
        )

    @staticmethod
    def get_process(
        db: Session,
        *,
        process_id: int,
        current_user: User,
    ) -> InsuranceProcess:
        process = InsuranceProcessRepository.get_by_id(db, process_id)
        if process is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance process not found",
            )
        _ensure_process_visible(process, current_user)
        return process

    @staticmethod
    def create_process(
        db: Session,
        *,
        payload: InsuranceProcessCreate,
        actor: User,
    ) -> InsuranceProcess:
        package = InsurancePackageRepository.get_by_id(db, payload.package_id)
        if package is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance package not found",
            )

        process = InsuranceProcessRepository.create_process(db, payload)
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.insurance_process.create",
            entity_type="insurance_process",
            entity_id=str(process.id),
            metadata_json={"package_id": process.package_id},
        )
        db.commit()
        db.refresh(process)
        return process

    @staticmethod
    def update_process(
        db: Session,
        *,
        process_id: int,
        payload: InsuranceProcessUpdate,
        actor: User,
    ) -> InsuranceProcess:
        process = InsuranceProcessRepository.get_by_id(db, process_id)
        if process is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance process not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if "package_id" in update_data:
            package = InsurancePackageRepository.get_by_id(db, update_data["package_id"])
            if package is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance package not found",
                )

        for field, value in update_data.items():
            setattr(process, field, value)

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.insurance_process.update",
            entity_type="insurance_process",
            entity_id=str(process.id),
            metadata_json={"fields": sorted(update_data.keys())},
        )
        db.commit()
        db.refresh(process)
        return process

    @staticmethod
    def delete_process(db: Session, *, process_id: int, actor: User) -> None:
        process = InsuranceProcessRepository.get_by_id(db, process_id)
        if process is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance process not found",
            )

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.insurance_process.delete",
            entity_type="insurance_process",
            entity_id=str(process.id),
        )
        InsuranceProcessRepository.delete_process(db, process)
        db.commit()


class ProcessStepService:
    @staticmethod
    def list_steps(
        db: Session,
        *,
        process_id: int,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[ProcessStep]:
        process = InsuranceProcessService.get_process(
            db,
            process_id=process_id,
            current_user=current_user,
        )
        return ProcessStepRepository.list_steps(
            db,
            process_id=process.id,
            skip=skip,
            limit=min(limit, 100),
            search=search,
        )

    @staticmethod
    def get_step(
        db: Session,
        *,
        step_id: int,
        current_user: User,
    ) -> ProcessStep:
        step = ProcessStepRepository.get_by_id(db, step_id)
        if step is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process step not found",
            )
        InsuranceProcessService.get_process(
            db,
            process_id=step.process_id,
            current_user=current_user,
        )
        return step

    @staticmethod
    def create_step(
        db: Session,
        *,
        process_id: int,
        payload: ProcessStepCreate,
        actor: User,
    ) -> ProcessStep:
        process = InsuranceProcessRepository.get_by_id(db, process_id)
        if process is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance process not found",
            )

        step = ProcessStepRepository.create_step(
            db,
            process_id=process_id,
            payload=payload,
        )
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.process_step.create",
            entity_type="process_step",
            entity_id=str(step.id),
            metadata_json={"process_id": process_id},
        )
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def update_step(
        db: Session,
        *,
        step_id: int,
        payload: ProcessStepUpdate,
        actor: User,
    ) -> ProcessStep:
        step = ProcessStepRepository.get_by_id(db, step_id)
        if step is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process step not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(step, field, value)

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.process_step.update",
            entity_type="process_step",
            entity_id=str(step.id),
            metadata_json={"fields": sorted(update_data.keys())},
        )
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def delete_step(db: Session, *, step_id: int, actor: User) -> None:
        step = ProcessStepRepository.get_by_id(db, step_id)
        if step is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process step not found",
            )

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.process_step.delete",
            entity_type="process_step",
            entity_id=str(step.id),
            metadata_json={"process_id": step.process_id},
        )
        ProcessStepRepository.delete_step(db, step)
        db.commit()
