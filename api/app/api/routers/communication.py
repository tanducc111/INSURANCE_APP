from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user, require_roles
from app.db.session import get_db
from app.models.communication import Appointment, AppointmentStatus, ChatMessage, ChatRoom
from app.models.user import User, UserRole
from app.schemas.communication import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentUpdate,
    ChatMessageCreate,
    ChatMessageRead,
    ChatRoomRead,
)
from app.services.communication_service import AppointmentService, ChatService

router = APIRouter(tags=["communication"])


@router.get("/customer/chat-room", response_model=ChatRoomRead)
async def get_customer_chat_room(
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> ChatRoom:
    return ChatService.get_or_create_customer_room(db, actor=current_customer)


@router.post(
    "/customer/chat-room",
    response_model=ChatRoomRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_chat_room(
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> ChatRoom:
    return ChatService.get_or_create_customer_room(db, actor=current_customer)


@router.get("/employee/chat-rooms", response_model=list[ChatRoomRead])
async def list_employee_chat_rooms(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> list[ChatRoom]:
    return ChatService.list_employee_rooms(
        db,
        actor=current_employee,
        skip=skip,
        limit=limit,
    )


@router.get("/chat/rooms/{room_id}/messages", response_model=list[ChatMessageRead])
async def list_chat_messages(
    room_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ChatMessage]:
    return ChatService.list_messages(
        db,
        room_id=room_id,
        actor=current_user,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/chat/rooms/{room_id}/messages",
    response_model=ChatMessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def send_chat_message(
    room_id: int,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ChatMessage:
    return ChatService.send_message(
        db,
        room_id=room_id,
        payload=payload,
        actor=current_user,
    )


@router.patch("/chat/rooms/{room_id}/read")
async def mark_chat_messages_read(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, int]:
    return ChatService.mark_messages_read(db, room_id=room_id, actor=current_user)


@router.post(
    "/customer/appointments",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> Appointment:
    return AppointmentService.create_customer_appointment(
        db,
        payload=payload,
        actor=current_customer,
    )


@router.get("/customer/appointments", response_model=list[AppointmentRead])
async def list_customer_appointments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> list[Appointment]:
    return AppointmentService.list_customer_appointments(
        db,
        actor=current_customer,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


@router.get("/employee/appointments", response_model=list[AppointmentRead])
async def list_employee_appointments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> list[Appointment]:
    return AppointmentService.list_employee_appointments(
        db,
        actor=current_employee,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


@router.patch("/employee/appointments/{appointment_id}", response_model=AppointmentRead)
async def update_employee_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> Appointment:
    return AppointmentService.update_employee_appointment(
        db,
        appointment_id=appointment_id,
        payload=payload,
        actor=current_employee,
    )


@router.get("/admin/appointments", response_model=list[AppointmentRead])
async def list_admin_appointments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[Appointment]:
    _ = current_admin
    return AppointmentService.list_admin_appointments(
        db,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )
