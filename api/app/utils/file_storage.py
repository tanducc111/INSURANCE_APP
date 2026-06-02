import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status


@dataclass(frozen=True)
class StoredUpload:
    original_name: str
    stored_name: str
    file_url: str
    mime_type: str
    file_size: int


@dataclass(frozen=True)
class ValidatedUpload:
    original_name: str
    mime_type: str
    content: bytes


def ensure_upload_dir(upload_dir: str | Path) -> Path:
    directory = Path(upload_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_file_stem(file_name: str) -> str:
    stem = Path(file_name).stem or "tep-dinh-kem"
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip(".-") or "tep-dinh-kem"
    return stem[:80]


async def validate_uploads(
    files: list[UploadFile],
    *,
    allowed_types: dict[str, str],
    max_bytes: int,
    empty_message: str,
    unsupported_message: str,
    oversized_message: str,
) -> list[ValidatedUpload]:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=empty_message,
        )

    validated_files: list[ValidatedUpload] = []
    for file in files:
        mime_type = file.content_type or "application/octet-stream"
        if mime_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=unsupported_message,
            )

        content = await file.read()
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=oversized_message,
            )

        validated_files.append(
            ValidatedUpload(
                original_name=file.filename or "tep-dinh-kem",
                mime_type=mime_type,
                content=content,
            )
        )
    return validated_files


def store_uploads(
    uploads: list[ValidatedUpload],
    *,
    upload_dir: str | Path,
    public_prefix: str,
    name_prefix: str,
    allowed_types: dict[str, str],
) -> list[StoredUpload]:
    directory = ensure_upload_dir(upload_dir)
    stored_uploads: list[StoredUpload] = []
    for upload in uploads:
        extension = allowed_types[upload.mime_type]
        stored_name = (
            f"{name_prefix}-{uuid.uuid4().hex}-"
            f"{safe_file_stem(upload.original_name)}{extension}"
        )
        file_path = directory / stored_name
        file_path.write_bytes(upload.content)
        stored_uploads.append(
            StoredUpload(
                original_name=upload.original_name,
                stored_name=stored_name,
                file_url=f"{public_prefix.rstrip('/')}/{stored_name}",
                mime_type=upload.mime_type,
                file_size=len(upload.content),
            )
        )
    return stored_uploads


def remove_stored_upload(*, file_url: str, upload_dir: str | Path) -> None:
    file_name = Path(file_url).name
    if not file_name:
        return

    directory = ensure_upload_dir(upload_dir).resolve()
    file_path = (directory / file_name).resolve()
    if directory in file_path.parents and file_path.exists():
        file_path.unlink()
