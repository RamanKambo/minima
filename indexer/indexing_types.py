from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class IndexingStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    DELETED_FROM_STORE = "DELETED_FROM_STORE"


@dataclass
class FileStatus:
    filename: str
    file_extension: str
    relative_path: str
    indexing_status: IndexingStatus
    last_modified_time: datetime
    last_indexed_time: Optional[datetime]
    error_message: Optional[str]

    @classmethod
    def create_pending(cls, filepath: str, modified_time: datetime) -> 'FileStatus':
        """
        Create a new FileStatus instance with PENDING status
        """
        from pathlib import Path
        path = Path(filepath)
        return cls(
            filename=path.name,
            file_extension=path.suffix.lower(),
            relative_path=str(path),
            indexing_status=IndexingStatus.PENDING,
            last_modified_time=modified_time,
            last_indexed_time=None,
            error_message=None
        )

    def to_dict(self) -> dict:
        """
        Convert the FileStatus instance to a dictionary for CSV storage
        """
        return {
            'filename': self.filename,
            'file_extension': self.file_extension,
            'relative_path': self.relative_path,
            'indexing_status': self.indexing_status.value,
            'last_modified_time': self.last_modified_time.isoformat(),
            'last_indexed_time': self.last_indexed_time.isoformat() if self.last_indexed_time else None,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FileStatus':
        """
        Create a FileStatus instance from a dictionary (loaded from CSV)
        """
        return cls(
            filename=data['filename'],
            file_extension=data['file_extension'],
            relative_path=data['relative_path'],
            indexing_status=IndexingStatus(data['indexing_status']),
            last_modified_time=datetime.fromisoformat(data['last_modified_time']),
            last_indexed_time=datetime.fromisoformat(data['last_indexed_time']) if data['last_indexed_time'] else None,
            error_message=data['error_message']
        )