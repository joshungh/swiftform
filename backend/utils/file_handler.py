import os
import json
import shutil
import aiofiles
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

class FileHandler:
    """Utility class for handling file operations"""

    def __init__(self, upload_dir: str = "uploads", results_dir: str = "results"):
        self.upload_dir = Path(upload_dir)
        self.results_dir = Path(results_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

    async def save_upload(self, file, file_id: str) -> str:
        """Save uploaded file to disk"""
        file_ext = os.path.splitext(file.filename)[1]
        file_path = self.upload_dir / f"{file_id}{file_ext}"

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        return str(file_path)

    def get_file_path(self, file_id: str) -> Optional[str]:
        """Get the path of an uploaded file"""
        for file_path in self.upload_dir.glob(f"{file_id}*"):
            if file_path.is_file():
                return str(file_path)
        return None

    async def save_result(self, job_id: str, result: Dict[str, Any]) -> None:
        """Save processing result to disk"""
        result_path = self.results_dir / f"{job_id}.json"

        async with aiofiles.open(result_path, 'w') as f:
            await f.write(json.dumps(result, indent=2))

    async def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get processing result from disk"""
        result_path = self.results_dir / f"{job_id}.json"

        if not result_path.exists():
            return None

        async with aiofiles.open(result_path, 'r') as f:
            content = await f.read()
            return json.loads(content)

    def delete_file(self, file_id: str) -> bool:
        """Delete an uploaded file"""
        file_path = self.get_file_path(file_id)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def cleanup_old_files(self, days: int = 7) -> int:
        """Clean up files older than specified days"""
        count = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for directory in [self.upload_dir, self.results_dir]:
            for file_path in directory.glob("*"):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        count += 1

        return count

    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an uploaded file"""
        file_path = self.get_file_path(file_id)
        if not file_path:
            return None

        stat = os.stat(file_path)
        return {
            "file_id": file_id,
            "file_path": file_path,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": os.path.splitext(file_path)[1]
        }