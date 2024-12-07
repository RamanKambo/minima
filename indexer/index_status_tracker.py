import os
import csv
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock
from .indexing_types import FileStatus, IndexingStatus

logger = logging.getLogger(__name__)

class IndexStatusTracker:
    def __init__(self, status_file_path: str = "index_status.csv"):
        self.status_file_path = Path(status_file_path)
        self.status_lock = Lock()
        self.statuses: Dict[str, FileStatus] = {}
        self._ensure_status_file_exists()
        self._load_status_file()

    def _ensure_status_file_exists(self) -> None:
        """Create the status file if it doesn't exist"""
        if not self.status_file_path.exists():
            self.status_file_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_status_file({})  # Create empty status file

    def _create_backup(self) -> None:
        """Create a backup of the current status file"""
        if self.status_file_path.exists():
            backup_path = self.status_file_path.with_suffix('.csv.backup')
            shutil.copy2(self.status_file_path, backup_path)

    def _load_status_file(self) -> None:
        """Load the status file into memory"""
        if not self.status_file_path.exists():
            return

        try:
            with open(self.status_file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                self.statuses = {
                    row['relative_path']: FileStatus.from_dict(row)
                    for row in reader
                }
        except Exception as e:
            logger.error(f"Error loading status file: {e}")
            # If loading fails, try to restore from backup
            self._restore_from_backup()

    def _save_status_file(self, statuses: Dict[str, FileStatus]) -> None:
        """Save the status dictionary to the CSV file"""
        try:
            self._create_backup()
            fieldnames = [
                'filename', 'file_extension', 'relative_path',
                'indexing_status', 'last_modified_time',
                'last_indexed_time', 'error_message'
            ]
            
            with open(self.status_file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for status in statuses.values():
                    writer.writerow(status.to_dict())
        except Exception as e:
            logger.error(f"Error saving status file: {e}")
            self._restore_from_backup()

    def _restore_from_backup(self) -> None:
        """Attempt to restore the status file from backup"""
        backup_path = self.status_file_path.with_suffix('.csv.backup')
        if backup_path.exists():
            shutil.copy2(backup_path, self.status_file_path)
            self._load_status_file()

    def get_file_status(self, filepath: str) -> Optional[FileStatus]:
        """Get the status of a specific file"""
        with self.status_lock:
            return self.statuses.get(str(Path(filepath)))

    def update_file_status(
        self,
        filepath: str,
        status: IndexingStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update the status of a specific file"""
        with self.status_lock:
            path_str = str(Path(filepath))
            if path_str in self.statuses:
                file_status = self.statuses[path_str]
                file_status.indexing_status = status
                file_status.error_message = error_message
                if status == IndexingStatus.COMPLETE:
                    file_status.last_indexed_time = datetime.now()
                self._save_status_file(self.statuses)

    def add_pending_file(self, filepath: str) -> None:
        """Add a new file with PENDING status"""
        path = Path(filepath)
        with self.status_lock:
            if str(path) not in self.statuses:
                modified_time = datetime.fromtimestamp(path.stat().st_mtime)
                self.statuses[str(path)] = FileStatus.create_pending(
                    filepath=str(path),
                    modified_time=modified_time
                )
                self._save_status_file(self.statuses)

    def mark_deleted_files(self, existing_files: List[str]) -> None:
        """Mark files that no longer exist as DELETED_FROM_STORE"""
        existing_paths = {str(Path(f)) for f in existing_files}
        with self.status_lock:
            for path_str, status in self.statuses.items():
                if path_str not in existing_paths and status.indexing_status != IndexingStatus.DELETED_FROM_STORE:
                    status.indexing_status = IndexingStatus.DELETED_FROM_STORE
                    status.error_message = "File no longer exists"
            self._save_status_file(self.statuses)

    def get_files_by_status(self, status: IndexingStatus) -> List[FileStatus]:
        """Get all files with a specific status"""
        with self.status_lock:
            return [
                file_status for file_status in self.statuses.values()
                if file_status.indexing_status == status
            ]

    def get_files_needing_indexing(self) -> List[FileStatus]:
        """Get all files that need to be indexed (PENDING or FAILED status)"""
        with self.status_lock:
            return [
                file_status for file_status in self.statuses.values()
                if file_status.indexing_status in (IndexingStatus.PENDING, IndexingStatus.FAILED)
            ]