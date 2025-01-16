import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

class FileOperationError(Exception):
    """Custom exception for file operations."""
    pass

class FileOperations:
    def __init__(self, base_dir: Union[str, Path]):
        """Initialize with a base directory for operations."""
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # Ensure base directory has proper permissions (700)
        self.base_dir.chmod(0o700)
        logger.info(f"Initialized file operations in directory: {self.base_dir}")

    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and resolve a path relative to base_dir."""
        try:
            full_path = (self.base_dir / Path(path)).resolve()
            if not str(full_path).startswith(str(self.base_dir)):
                raise FileOperationError(f"Path {path} attempts to escape base directory")
            return full_path
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError(f"Invalid path {path}: {str(e)}")

    def _ensure_parent_dir(self, path: Path) -> None:
        """Ensure parent directory exists with proper permissions."""
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
            path.parent.chmod(0o700)

    def create_file(self, path: Union[str, Path], content: str = "") -> Path:
        """Create a new file with optional content."""
        try:
            file_path = self._validate_path(path)
            self._ensure_parent_dir(file_path)
            
            if file_path.exists():
                raise FileOperationError(f"File {path} already exists")
            
            # Create file with restricted permissions first
            old_umask = os.umask(0o077)
            try:
                file_path.write_text(content)
            finally:
                os.umask(old_umask)
            
            logger.info(f"Created file: {path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to create file {path}: {str(e)}")
            raise FileOperationError(f"Failed to create file: {str(e)}")

    def read_file(self, path: Union[str, Path]) -> str:
        """Read and return file contents."""
        try:
            file_path = self._validate_path(path)
            if not file_path.exists():
                raise FileOperationError(f"File {path} does not exist")
            
            content = file_path.read_text()
            logger.info(f"Read file: {path}")
            return content
        except Exception as e:
            logger.error(f"Failed to read file {path}: {str(e)}")
            raise FileOperationError(f"Failed to read file: {str(e)}")

    def update_file(self, path: Union[str, Path], content: str) -> Path:
        """Update an existing file with new content."""
        try:
            file_path = self._validate_path(path)
            if not file_path.exists():
                raise FileOperationError(f"File {path} does not exist")
            
            # Preserve original permissions
            original_mode = file_path.stat().st_mode
            
            # Create temporary file with restricted permissions
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            old_umask = os.umask(0o077)
            try:
                temp_path.write_text(content)
                temp_path.chmod(original_mode)
                temp_path.replace(file_path)
            finally:
                os.umask(old_umask)
                if temp_path.exists():
                    temp_path.unlink()
            
            logger.info(f"Updated file: {path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to update file {path}: {str(e)}")
            raise FileOperationError(f"Failed to update file: {str(e)}")

    def delete_file(self, path: Union[str, Path]) -> None:
        """Delete a file."""
        try:
            file_path = self._validate_path(path)
            if not file_path.exists():
                raise FileOperationError(f"File {path} does not exist")
            
            file_path.unlink()
            logger.info(f"Deleted file: {path}")
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {str(e)}")
            raise FileOperationError(f"Failed to delete file: {str(e)}")

    def list_files(self, directory: Optional[Union[str, Path]] = None) -> list[Path]:
        """List all files in the specified directory."""
        try:
            if directory:
                dir_path = self._validate_path(directory)
            else:
                dir_path = self.base_dir

            if not dir_path.exists() or not dir_path.is_dir():
                raise FileOperationError(f"Directory {directory} does not exist")
            
            files = [f for f in dir_path.rglob('*') if f.is_file()]
            logger.info(f"Listed {len(files)} files in {directory or '.'}")
            return files
        except Exception as e:
            logger.error(f"Failed to list files in {directory or '.'}: {str(e)}")
            raise FileOperationError(f"Failed to list files: {str(e)}")

    def copy_file(self, src: Union[str, Path], dst: Union[str, Path]) -> Path:
        """Copy a file to a new location."""
        try:
            src_path = self._validate_path(src)
            dst_path = self._validate_path(dst)

            if not src_path.exists():
                raise FileOperationError(f"Source file {src} does not exist")
            if dst_path.exists():
                raise FileOperationError(f"Destination file {dst} already exists")

            self._ensure_parent_dir(dst_path)
            
            # Copy with preserved permissions
            shutil.copy2(src_path, dst_path)
            logger.info(f"Copied file from {src} to {dst}")
            return dst_path
        except Exception as e:
            logger.error(f"Failed to copy file from {src} to {dst}: {str(e)}")
            raise FileOperationError(f"Failed to copy file: {str(e)}") 