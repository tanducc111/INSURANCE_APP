from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.communication import Appointment, AppointmentStatus, ChatMessage, ChatRoom
from app.models.customer_management import Customer, Employee
from app.models.user import User
from app.schemas.communication import AppointmentCreate, ChatMessageCreate


def _room_options():
    return (
        joinedload(ChatRoom.customer).joinedload(Customer.user),
        joinedload(ChatRoom.employee).joinedload(Employee.user),
    )


def _message_options():
    return (joinedload(ChatMessage.sender),)


def _appointment_options():
    return (
        joinedload(Appointment.customer).joinedload(Customer.user),
        joinedload(Appointment.employee).joinedload(Employee.user),
    )


class ChatRoomRepository:
    @staticmethod
    def get_by_id(db: Session, room_id: int) -> ChatRoom | None:
        return db.scalar(
            select(ChatRoom).options(*_room_options()).where(ChatRoom.id == room_id)
        )

    @staticmethod
    def get_by_participants(
        db: Session,
        *,
        customer_id: int,
        employee_id: int,
    ) -> ChatRoom | None:
        return db.scalar(
            select(ChatRoom)
            .options(*_room_options())
            .where(
                ChatRoom.customer_id == customer_id,
                ChatRoom.employee_id == employee_id,
            )
        )

    @staticmethod
    def list_for_employee(
        db: Session,
        *,
        employee_id: int,
        customer_ids: list[int],
        skip: int = 0,
        limit: int = 50,
    ) -> list[ChatRoom]:
        if not customer_ids:
            return []
        query: Select[tuple[ChatRoom]] = (
            select(ChatRoom)
            .options(*_room_options())
            .where(
                ChatRoom.employee_id == employee_id,
                ChatRoom.customer_id.in_(customer_ids),
            )
            .order_by(ChatRoom.updated_at.desc())
        )
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_room(
        db: Session,
        *,
        customer_id: int,
        employee_id: int,
    ) -> ChatRoom:
        room = ChatRoom(customer_id=customer_id, employee_id=employee_id)
        db.add(room)
        return room


class ChatMessageRepository:
    @staticmethod
    def list_messages(
        db: Session,
        *,
        room_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ChatMessage]:
        query = (
            select(ChatMessage)
            .options(*_message_options())
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_message(
        db: Session,
        *,
        room_id: int,
        sender_user_id: int,
        payload: ChatMessageCreate,
    ) -> ChatMessage:
        message = ChatMessage(
            room_id=room_id,
            sender_user_id=sender_user_id,
            content=payload.content,
        )
        db.add(message)
        return message

    @staticmethod
    def mark_room_messages_read(
        db: Session,
        *,
        room_id: int,
        reader_user_id: int,
    ) -> int:
        messages = list(
            db.scalars(
                select(ChatMessage).where(
                    ChatMessage.room_id == room_id,
                    ChatMessage.sender_user_id != reader_user_id,
                    ChatMessage.is_read.is_(False),
                )
            )
        )
        for message in messages:
            message.is_read = True
        return len(messages)


class AppointmentRepository:
    @staticmethod
    def get_by_id(db: Session, appointment_id: int) -> Appointment | None:
        return db.scalar(
            select(Appointment)
            .options(*_appointment_options())
            .where(Appointment.id == appointment_id)
        )

    @staticmethod
    def list_appointments(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        status_filter: AppointmentStatus | None = None,
        customer_id: int | None = None,
        employee_id: int | None = None,
        customer_ids: list[int] | None = None,
    ) -> list[Appointment]:
        query: Select[tuple[Appointment]] = (
            select(Appointment)
            .options(*_appointment_options())
            .order_by(Appointment.scheduled_at.desc())
        )
        if customer_id is not None:
            query = query.where(Appointment.customer_id == customer_id)
        if employee_id is not None:
            query = query.where(Appointment.employee_id == employee_id)
        if customer_ids is not None:
            if not customer_ids:
                return []
            query = query.where(Appointment.customer_id.in_(customer_ids))
        if status_filter:
            query = query.where(Appointment.status == status_filter)
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_appointment(
        db: Session,
        *,
        customer_id: int,
        employee_id: int,
        payload: AppointmentCreate,
    ) -> Appointment:
        appointment = Appointment(
            customer_id=customer_id,
            employee_id=employee_id,
            scheduled_at=payload.scheduled_at,
            duration_minutes=payload.duration_minutes,
            note=payload.note,
        )
        db.add(appointment)
        return appointment
