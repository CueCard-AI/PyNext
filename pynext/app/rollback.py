"""
Rollback Manager - Support rollback of generated files.

Saves checkpoints before modifications and allows
rolling back to previous state if generation fails.

Example:
    manager = RollbackManager(project_path)
    
    manager.checkpoint("Before adding auth")
    
    try:
        # Generate files...
        manager.commit()  # Clear checkpoint
    except Exception:
        manager.rollback()  # Restore previous state
"""

import json
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileSnapshot:
    """Snapshot of a file's state."""
    path: str
    existed: bool
    content: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "existed": self.existed,
            "content": self.content,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileSnapshot":
        return cls(
            path=data["path"],
            existed=data["existed"],
            content=data.get("content"),
        )


@dataclass
class Checkpoint:
    """A checkpoint representing project state."""
    id: str
    description: str
    created_at: datetime
    files: List[FileSnapshot] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "files": [f.to_dict() for f in self.files],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        return cls(
            id=data["id"],
            description=data["description"],
            created_at=datetime.fromisoformat(data["created_at"]),
            files=[FileSnapshot.from_dict(f) for f in data.get("files", [])],
        )


class RollbackManager:
    """
    Manages checkpoints and rollbacks for generated files.
    
    Creates snapshots of files before modifications and
    allows rolling back to previous states.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize rollback manager.
        
        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path).resolve()
        self._checkpoints: List[Checkpoint] = []
        self._pending_files: Set[str] = set()  # Files modified since last checkpoint
        self._checkpoint_dir = self.project_path / ".pynext" / "checkpoints"
        
        # Ensure checkpoint directory exists
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def checkpoint(
        self,
        description: str = "Checkpoint",
        files: Optional[List[str]] = None,
    ) -> str:
        """
        Create a checkpoint of current state.
        
        Args:
            description: Description of the checkpoint
            files: Specific files to snapshot (or all pending if None)
        
        Returns:
            Checkpoint ID
        """
        checkpoint_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Determine which files to snapshot
        if files:
            files_to_snapshot = files
        else:
            files_to_snapshot = list(self._pending_files)
        
        # Create snapshots
        snapshots = []
        for file_path in files_to_snapshot:
            full_path = self.project_path / file_path
            
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding="utf-8")
                    snapshots.append(FileSnapshot(
                        path=file_path,
                        existed=True,
                        content=content,
                    ))
                except Exception as e:
                    logger.warning(f"Could not snapshot {file_path}: {e}")
                    snapshots.append(FileSnapshot(
                        path=file_path,
                        existed=True,
                        content=None,
                    ))
            else:
                snapshots.append(FileSnapshot(
                    path=file_path,
                    existed=False,
                ))
        
        checkpoint = Checkpoint(
            id=checkpoint_id,
            description=description,
            created_at=datetime.utcnow(),
            files=snapshots,
        )
        
        self._checkpoints.append(checkpoint)
        self._save_checkpoint(checkpoint)
        
        logger.info(f"Created checkpoint: {checkpoint_id} - {description}")
        
        return checkpoint_id
    
    def mark_file_modified(self, file_path: str) -> None:
        """
        Mark a file as modified (for automatic checkpointing).
        
        Args:
            file_path: Relative path to file
        """
        self._pending_files.add(file_path)
    
    def rollback(self, checkpoint_id: Optional[str] = None) -> int:
        """
        Rollback to a checkpoint.
        
        Args:
            checkpoint_id: ID of checkpoint to rollback to (last if None)
        
        Returns:
            Number of files restored
        """
        if not self._checkpoints:
            logger.warning("No checkpoints to rollback to")
            return 0
        
        # Find checkpoint
        if checkpoint_id:
            checkpoint = next(
                (c for c in self._checkpoints if c.id == checkpoint_id),
                None
            )
            if not checkpoint:
                logger.warning(f"Checkpoint not found: {checkpoint_id}")
                return 0
        else:
            checkpoint = self._checkpoints[-1]
        
        # Restore files
        restored = 0
        for snapshot in checkpoint.files:
            full_path = self.project_path / snapshot.path
            
            try:
                if snapshot.existed:
                    if snapshot.content is not None:
                        # Restore original content
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        full_path.write_text(snapshot.content, encoding="utf-8")
                        restored += 1
                else:
                    # File didn't exist, delete it
                    if full_path.exists():
                        full_path.unlink()
                        restored += 1
            except Exception as e:
                logger.error(f"Could not restore {snapshot.path}: {e}")
        
        logger.info(f"Rolled back to checkpoint {checkpoint.id}, restored {restored} files")
        
        return restored
    
    def commit(self, checkpoint_id: Optional[str] = None) -> None:
        """
        Commit changes and clear checkpoint.
        
        Args:
            checkpoint_id: Checkpoint to clear (last if None)
        """
        if not self._checkpoints:
            return
        
        if checkpoint_id:
            # Remove specific checkpoint
            self._checkpoints = [c for c in self._checkpoints if c.id != checkpoint_id]
            self._delete_checkpoint(checkpoint_id)
        else:
            # Remove last checkpoint
            checkpoint = self._checkpoints.pop()
            self._delete_checkpoint(checkpoint.id)
        
        self._pending_files.clear()
        logger.info("Changes committed, checkpoint cleared")
    
    def get_checkpoints(self) -> List[Checkpoint]:
        """Get all checkpoints."""
        return self._checkpoints.copy()
    
    def clear_all_checkpoints(self) -> None:
        """Clear all checkpoints."""
        for checkpoint in self._checkpoints:
            self._delete_checkpoint(checkpoint.id)
        self._checkpoints.clear()
        self._pending_files.clear()
    
    def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to disk."""
        checkpoint_file = self._checkpoint_dir / f"{checkpoint.id}.json"
        try:
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save checkpoint: {e}")
    
    def _load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from disk."""
        checkpoint_file = self._checkpoint_dir / f"{checkpoint_id}.json"
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)
            return Checkpoint.from_dict(data)
        except Exception as e:
            logger.error(f"Could not load checkpoint: {e}")
            return None
    
    def _delete_checkpoint(self, checkpoint_id: str) -> None:
        """Delete checkpoint from disk."""
        checkpoint_file = self._checkpoint_dir / f"{checkpoint_id}.json"
        try:
            if checkpoint_file.exists():
                checkpoint_file.unlink()
        except Exception as e:
            logger.warning(f"Could not delete checkpoint file: {e}")
    
    def load_checkpoints(self) -> None:
        """Load all checkpoints from disk."""
        self._checkpoints.clear()
        
        try:
            for checkpoint_file in self._checkpoint_dir.glob("*.json"):
                checkpoint_id = checkpoint_file.stem
                checkpoint = self._load_checkpoint(checkpoint_id)
                if checkpoint:
                    self._checkpoints.append(checkpoint)
        except Exception as e:
            logger.error(f"Could not load checkpoints: {e}")
        
        # Sort by creation time
        self._checkpoints.sort(key=lambda c: c.created_at)

