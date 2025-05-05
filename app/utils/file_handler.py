"""
파일 업로드 핸들러
"""
from enum import Enum
from typing import Dict, Optional
import os
import uuid
import mimetypes
from datetime import datetime
from fastapi import UploadFile
from app.utils.logger import app_logger, LogType
import logging

class FileType(Enum):
    IMAGE = 'image'
    DOCUMENT = 'document'
    ARCHIVE = 'archive'
    OTHER = 'other'

UPLOAD_DIRS: Dict[FileType, str] = {
    FileType.IMAGE: "app/upload/images",
    FileType.DOCUMENT: "app/upload/documents",
    FileType.ARCHIVE: "app/upload/archives",
    FileType.OTHER: "app/upload/others"
}

# MIME 타입 기반 파일 타입 매핑
MIME_TYPE_MAPPING: Dict[str, FileType] = {
    # 이미지 타입
    'image/jpeg': FileType.IMAGE,
    'image/png': FileType.IMAGE,
    'image/gif': FileType.IMAGE,
    'image/bmp': FileType.IMAGE,
    'image/webp': FileType.IMAGE,
    'image/svg+xml': FileType.IMAGE,
    
    # 문서 타입
    'application/pdf': FileType.DOCUMENT,
    'application/msword': FileType.DOCUMENT,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileType.DOCUMENT,
    'application/vnd.ms-powerpoint': FileType.DOCUMENT,
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': FileType.DOCUMENT,
    'application/vnd.ms-excel': FileType.DOCUMENT,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': FileType.DOCUMENT,
    'text/plain': FileType.DOCUMENT,
    'text/csv': FileType.DOCUMENT,
    'text/html': FileType.DOCUMENT,
    
    # 압축 파일 타입
    'application/zip': FileType.ARCHIVE,
    'application/x-rar-compressed': FileType.ARCHIVE,
    'application/x-7z-compressed': FileType.ARCHIVE,
    'application/x-tar': FileType.ARCHIVE,
    'application/gzip': FileType.ARCHIVE
}

# 확장자 기반 파일 타입 매핑 (MIME 타입이 없는 경우를 위한 백업)
EXTENSION_MAPPING: Dict[str, FileType] = {
    # 이미지 확장자
    '.jpg': FileType.IMAGE,
    '.jpeg': FileType.IMAGE,
    '.png': FileType.IMAGE,
    '.gif': FileType.IMAGE,
    '.bmp': FileType.IMAGE,
    '.webp': FileType.IMAGE,
    '.svg': FileType.IMAGE,
    
    # 문서 확장자
    '.pdf': FileType.DOCUMENT,
    '.doc': FileType.DOCUMENT,
    '.docx': FileType.DOCUMENT,
    '.ppt': FileType.DOCUMENT,
    '.pptx': FileType.DOCUMENT,
    '.xls': FileType.DOCUMENT,
    '.xlsx': FileType.DOCUMENT,
    '.txt': FileType.DOCUMENT,
    '.csv': FileType.DOCUMENT,
    '.html': FileType.DOCUMENT,
    
    # 압축 파일 확장자
    '.zip': FileType.ARCHIVE,
    '.rar': FileType.ARCHIVE,
    '.7z': FileType.ARCHIVE,
    '.tar': FileType.ARCHIVE,
    '.gz': FileType.ARCHIVE
}

def get_file_type(filename: str, content_type: Optional[str] = None) -> FileType:
    """
    파일의 MIME 타입과 확장자를 기반으로 파일 타입을 결정합니다.
    
    Args:
        filename: 파일명
        content_type: 파일의 MIME 타입 (선택사항)
        
    Returns:
        FileType: 결정된 파일 타입
    """
    # MIME 타입으로 먼저 판단
    if content_type:
        file_type = MIME_TYPE_MAPPING.get(content_type.lower())
        if file_type:
            return file_type
    
    # 확장자로 판단
    ext = os.path.splitext(filename)[1].lower()
    file_type = EXTENSION_MAPPING.get(ext)
    if file_type:
        return file_type
    
    # MIME 타입이 없고 확장자도 매핑되지 않은 경우
    if content_type:
        # MIME 타입의 기본 카테고리로 판단
        main_type = content_type.split('/')[0]
        if main_type == 'image':
            return FileType.IMAGE
        elif main_type == 'text':
            return FileType.DOCUMENT
        elif main_type == 'application':
            return FileType.DOCUMENT
    
    # 모든 방법으로도 판단이 안되면 OTHER로 분류
    return FileType.OTHER

def ensure_upload_dir(file_type: FileType):
    """업로드 디렉토리가 없으면 생성합니다."""
    upload_dir = UPLOAD_DIRS[file_type]
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        app_logger.log(
            logging.INFO,
            f"업로드 디렉토리 생성: {upload_dir}",
            log_type=LogType.ALL
        )

async def save_file(file: UploadFile, file_type: Optional[FileType] = None) -> dict:
    """파일을 저장하고 저장된 경로와 파일명을 반환합니다."""
    try:
        # 파일 타입 결정
        if file_type is None:
            file_type = get_file_type(file.filename, file.content_type)
            if file_type == FileType.OTHER:
                app_logger.log(
                    logging.WARNING,
                    f"지원하지 않는 파일 형식: {file.filename} (MIME: {file.content_type})",
                    log_type=LogType.ALL
                )

        ensure_upload_dir(file_type)
        
        # 새 파일명 생성
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ''
        new_filename = f"{uuid.uuid4()}_{int(datetime.now().timestamp())}{file_extension}"
        
        # 파일 저장
        file_path = os.path.join(UPLOAD_DIRS[file_type], new_filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        app_logger.log(
            logging.INFO,
            f"파일 저장 성공: {new_filename} (타입: {file_type.value})",
            log_type=LogType.ALL
        )
        
        return {
            "type": file_type.value,
            "path": UPLOAD_DIRS[file_type],
            "filename": new_filename
        }
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"파일 저장 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise

def delete_file(file_info: dict):
    """파일을 삭제합니다."""
    try:
        file_path = os.path.join(file_info["path"], file_info["filename"])
        if os.path.exists(file_path):
            os.remove(file_path)
            app_logger.log(
                logging.INFO,
                f"파일 삭제 성공: {file_info['filename']}",
                log_type=LogType.ALL
            )
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"파일 삭제 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise 