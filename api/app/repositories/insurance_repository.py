from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.insurance import (
    InsurancePackage,
    InsuranceProcess,
    InsuranceStatus,
    ProcessStep,
)
from app.schemas.insurance import (
    InsurancePackageCreate,
    InsuranceProcessCreate,
    ProcessStepCreate,
)


class InsurancePackageRepository:
    @staticmethod
    def get_by_id(db: Session, package_id: int) -> InsurancePackage | None:
        return db.scalar(
            select(InsurancePackage).where(InsurancePackage.id == package_id)
        )

    @staticmethod
    def get_by_code(db: Session, code: str) -> InsurancePackage | None:
        return db.scalar(
            select(InsurancePackage).where(
                func.lower(InsurancePackage.code) == code.lower()
            )
        )

    @staticmethod
    def list_packages(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status_filter: InsuranceStatus | None = None,
        active_only: bool = False,
    ) -> list[InsurancePackage]:
        query: Select[tuple[InsurancePackage]] = select(InsurancePackage).order_by(
            InsurancePackage.created_at.desc()
        )
        if active_only:
            query = query.where(InsurancePackage.status == InsuranceStatus.ACTIVE)
        elif status_filter:
            query = query.where(InsurancePackage.status == status_filter)

        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                func.lower(InsurancePackage.code).like(pattern)
                | func.lower(InsurancePackage.name).like(pattern)
                | func.lower(InsurancePackage.package_type).like(pattern)
            )

        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_package(
        db: Session,
        payload: InsurancePackageCreate,
    ) -> InsurancePackage:
        package = InsurancePackage(**payload.model_dump())
        db.add(package)
        return package

    @staticmethod
    def delete_package(db: Session, package: InsurancePackage) -> None:
        db.delete(package)


class InsuranceProcessRepository:
    @staticmethod
    def get_by_id(db: Session, process_id: int) -> InsuranceProcess | None:
        return db.scalar(
            select(InsuranceProcess).where(InsuranceProcess.id == process_id)
        )

    @staticmethod
    def list_processes(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        package_id: int | None = None,
        search: str | None = None,
        status_filter: InsuranceStatus | None = None,
        active_only: bool = False,
    ) -> list[InsuranceProcess]:
        query: Select[tuple[InsuranceProcess]] = select(InsuranceProcess).join(
            InsuranceProcess.package
        )
        if package_id:
            query = query.where(InsuranceProcess.package_id == package_id)
        if active_only:
            query = query.where(
                InsuranceProcess.status == InsuranceStatus.ACTIVE,
                InsurancePackage.status == InsuranceStatus.ACTIVE,
            )
        elif status_filter:
            query = query.where(InsuranceProcess.status == status_filter)

        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(func.lower(InsuranceProcess.name).like(pattern))

        query = query.order_by(InsuranceProcess.created_at.desc())
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_process(
        db: Session,
        payload: InsuranceProcessCreate,
    ) -> InsuranceProcess:
        process = InsuranceProcess(**payload.model_dump())
        db.add(process)
        return process

    @staticmethod
    def delete_process(db: Session, process: InsuranceProcess) -> None:
        db.delete(process)


class ProcessStepRepository:
    @staticmethod
    def get_by_id(db: Session, step_id: int) -> ProcessStep | None:
        return db.scalar(select(ProcessStep).where(ProcessStep.id == step_id))

    @staticmethod
    def list_steps(
        db: Session,
        *,
        process_id: int,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[ProcessStep]:
        query: Select[tuple[ProcessStep]] = (
            select(ProcessStep)
            .where(ProcessStep.process_id == process_id)
            .order_by(ProcessStep.step_order.asc(), ProcessStep.id.asc())
        )
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(func.lower(ProcessStep.name).like(pattern))

        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_step(
        db: Session,
        *,
        process_id: int,
        payload: ProcessStepCreate,
    ) -> ProcessStep:
        step = ProcessStep(process_id=process_id, **payload.model_dump())
        db.add(step)
        return step

    @staticmethod
    def delete_step(db: Session, step: ProcessStep) -> None:
        db.delete(step)
