import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict
from .indexing_types import FileStatus, IndexingStatus
from .index_status_tracker import IndexStatusTracker

logger = logging.getLogger(__name__)

class FileDiscoveryService:
    def __init__(
        self,
        status_tracker: IndexStatusTracker,
        supported_extensions: Set[str],
        base_directory: str
    ):
        self.status_tracker = status_tracker
        self.supported_extensions = supported_extensions
        self.base_directory = Path(base_directory)

    def scan_directory(self) -> List[FileStatus]:
        """
        Scan the directory and update file statuses
        Returns: List of files that need indexing
        """
        try:
            # Get all existing files
            current_files = self._get_current_files()
            
            # Update status for existing files
            self._update_existing_files(current_files)
            
            # Mark files that no longer exist
            self.status_tracker.mark_deleted_files(current_files)
            
            # Get list of files that need indexing
            return self.status_tracker.get_files_needing_indexing()
            
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            return []

    def _get_current_files(self) -> List[str]:
        """Get all supported files in the directory"""
        current_files = []
        for root, _, files in os.walk(self.base_directory):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.supported_extensions:
                    current_files.append(str(file_path))
        return current_files

    def _update_existing_files(self, current_files: List[str]) -> None:
        """Update status for all existing files"""
        for file_path in current_files:
            self._process_file(file_path)

    def _process_file(self, file_path: str) -> None:
        """Process a single file and update its status if necessary"""
        try:
            path = Path(file_path)
            current_modified_time = datetime.fromtimestamp(path.stat().st_mtime)
            
            # Get existing status
            existing_status = self.status_tracker.get_file_status(file_path)
            
            if existing_status is None:
                # New file - add to tracking
                self.status_tracker.add_pending_file(file_path)
                logger.info(f"Added new file to tracking: {file_path}")
                
            elif existing_status.indexing_status == IndexingStatus.COMPLETE:
                # Check if file has been modified since last indexing
                if current_modified_time > existing_status.last_modified_time:
                    self.status_tracker.update_file_status(
                        file_path,
                        IndexingStatus.PENDING,
                        "File modified since last indexing"
                    )
                    logger.info(f"Marked modified file for re-indexing: {file_path}")
                    
            elif existing_status.indexing_status == IndexingStatus.DELETED_FROM_STORE:
                # File exists again - mark for re-indexing
                self.status_tracker.update_file_status(
                    file_path,
                    IndexingStatus.PENDING,
                    "File restored - needs re-indexing"
                )
                logger.info(f"Marked restored file for re-indexing: {file_path}")
                
            # Note: We don't change status for RUNNING, PENDING, or FAILED files
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            if existing_status:
                self.status_tracker.update_file_status(
                    file_path,
                    IndexingStatus.FAILED,
                    f"Error during file processing: {str(e)}"
                )