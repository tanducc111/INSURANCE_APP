from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.communication import Appointment, AppointmentStatus, ChatMessage, ChatRoom
from app.models.customer_management import Customer, Employee
from app.models.user import User, UserRole
from app.repositories.audit_repository import AuditRepository
from app.repositories.communication_repository import (
    AppointmentRepository,
    ChatMessageRepository,
    ChatRoomRepository,
)
from app.repositories.customer_management_repository import (
    AssignmentRepository,
    CustomerRepository,
    EmployeeRepository,
)
from app.schemas.communication import (
    AppointmentCreate,
    AppointmentUpdate,
    ChatMessageCreate,
)


def _get_customer_for_user(db: Session, user: User) -> Customer:
    customer = CustomerRepository.get_by_user_id(db, user.id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )
    return customer


def _get_employee_for_user(db: Session, user: User) -> Employee:
    employee = EmployeeRepository.get_by_user_id(db, user.id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )
    return employee


def _get_active_assignment_employee(db: Session, customer_id: int) -> Employee:
    assignment = AssignmentRepository.get_active_for_customer(db, customer_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned employee not found",
        )
    return assignment.employee


def _ensure_employee_can_access_customer(
    db: Session,
    *,
    user: User,
    customer_id: int,
) -> Employee:
    employee = _get_employee_for_user(db, user)
    assignment = AssignmentRepository.get_active_for_customer(db, customer_id)
    if assignment is None or assignment.employee_id != employee.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer is not assigned to this employee",
        )
    return employee


class ChatService:
    @staticmethod
    def get_or_create_customer_room(db: Session, *, actor: User) -> ChatRoom:
        customer = _get_customer_for_user(db, actor)
        employee = _get_active_assignment_employee(db, customer.id)
        room = ChatRoomRepository.get_by_participants(
            db,
            customer_id=customer.id,
            employee_id=employee.id,
        )
        if room:
            return room

        room = ChatRoomRepository.create_room(
            db,
            customer_id=customer.id,
            employee_id=employee.id,
        )
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="customer.chat_room.create",
            entity_type="chat_room",
            entity_id=str(room.id),
            metadata_json={"employee_id": employee.id},
        )
        db.commit()
        db.refresh(room)
        return room

    @staticmethod
    def list_employee_rooms(
        db: Session,
        *,
        actor: User,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ChatRoom]:
        employee = _get_employee_for_user(db, actor)
        assignments = AssignmentRepository.list_active_for_employee(
            db,
            employee.id,
            limit=100,
        )
        return ChatRoomRepository.list_for_employee(
            db,
            employee_id=employee.id,
            customer_ids=[assignment.customer_id for assignment in assignments],
            skip=skip,
            limit=min(limit, 100),
        )

    @staticmethod
    def _get_accessible_room(db: Session, *, room_id: int, actor: User) -> ChatRoom:
        room = ChatRoomRepository.get_by_id(db, room_id)
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat room not found",
            )

        if actor.role == UserRole.CUSTOMER:
            customer = _get_customer_for_user(db, actor)
            if room.customer_id != customer.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Chat room is not available for this customer",
                )
            return room

        if actor.role == UserRole.EMPLOYEE:
            _ensure_employee_can_access_customer(
                db,
                user=actor,
                customer_id=room.customer_id,
            )
            return room

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    @staticmethod
    def list_messages(
        db: Session,
        *,
        room_id: int,
        actor: User,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ChatMessage]:
        ChatService._get_accessible_room(db, room_id=room_id, actor=actor)
        return ChatMessageRepository.list_messages(
            db,
            room_id=room_id,
            skip=skip,
            limit=min(limit, 100),
        )

    @staticmethod
    def send_message(
        db: Session,
        *,
        room_id: int,
        payload: ChatMessageCreate,
        actor: User,
    ) -> ChatMessage:
        room = ChatService._get_accessible_room(db, room_id=room_id, actor=actor)
        message = ChatMessageRepository.create_message(
            db,
            room_id=room.id,
            sender_user_id=actor.id,
            payload=payload,
        )
        room.updated_at = datetime.now(UTC)
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="chat.message.send",
            entity_type="chat_message",
            entity_id=str(message.id),
            metadata_json={"room_id": room.id},
        )
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def mark_messages_read(db: Session, *, room_id: int, actor: User) -> dict[str, int]:
        ChatService._get_accessible_room(db, room_id=room_id, actor=actor)
        count = ChatMessageRepository.mark_room_messages_read(
            db,
            room_id=room_id,
            reader_user_id=actor.id,
        )
        db.commit()
        return {"updated": count}


class AppointmentService:
    @staticmethod
    def create_customer_appointment(
        db: Session,
        *,
        payload: AppointmentCreate,
        actor: User,
    ) -> Appointment:
        customer = _get_customer_for_user(db, actor)
        employee = _get_active_assignment_employee(db, customer.id)
        appointment = AppointmentRepository.create_appointment(
            db,
            customer_id=customer.id,
            employee_id=employee.id,
            payload=payload,
        )
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="customer.appointment.create",
            entity_type="appointment",
            entity_id=str(appointment.id),
            metadata_json={"employee_id": employee.id},
        )
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def list_customer_appointments(
        db: Session,
        *,
        actor: User,
        skip: int = 0,
        limit: int = 50,
        status_filter: AppointmentStatus | None = None,
    ) -> list[Appointment]:
        customer = _get_customer_for_user(db, actor)
        return AppointmentRepository.list_appointments(
            db,
            customer_id=customer.id,
            status_filter=status_filter,
            skip=skip,
            limit=min(limit, 100),
        )

    @staticmethod
    def list_employee_appointments(
        db: Session,
        *,
        actor: User,
        skip: int = 0,
        limit: int = 50,
        status_filter: AppointmentStatus | None = None,
    ) -> list[Appointment]:
        employee = _get_employee_for_user(db, actor)
        assignments = AssignmentRepository.list_active_for_employee(
            db,
            employee.id,
            limit=100,
        )
        return AppointmentRepository.list_appointments(
            db,
            employee_id=employee.id,
            customer_ids=[assignment.customer_id for assignment in assignments],
            status_filter=status_filter,
            skip=skip,
            limit=min(limit, 100),
        )

    @staticmethod
    def update_employee_appointment(
        db: Session,
        *,
        appointment_id: int,
        payload: AppointmentUpdate,
        actor: User,
    ) -> Appointment:
        appointment = AppointmentRepository.get_by_id(db, appointment_id)
        if appointment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )
        _ensure_employee_can_access_customer(
            db,
            user=actor,
            customer_id=appointment.customer_id,
        )
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appointment, field, value)
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="employee.appointment.update",
            entity_type="appointment",
            entity_id=str(appointment.id),
            metadata_json={"fields": sorted(update_data.keys())},
        )
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def list_admin_appointments(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        status_filter: AppointmentStatus | None = None,
    ) -> list[Appointment]:
        return AppointmentRepository.list_appointments(
            db,
            status_filter=status_filter,
            skip=skip,
            limit=min(limit, 100),
        )
