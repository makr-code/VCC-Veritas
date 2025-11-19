"""
VQB Frontend - Process Model

Data model for VPB processes with Observable support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from .base_model import Observable


class ProcessStatus(Enum):
    """Process status enumeration"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class Process:
    """
    Data model for a VPB process
    
    Attributes:
        id: Unique process identifier
        title: Process title/name
        description: Detailed description
        start_time: Process start datetime
        end_time: Process end datetime
        status: Current process status
        authority: Responsible authority
        level: Display level (for timeline stacking)
        documents: List of associated document IDs
        dependencies: List of process IDs this depends on
        metadata: Additional metadata
    """
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    status: ProcessStatus = ProcessStatus.PLANNED
    description: str = ""
    authority: Optional[str] = None
    level: int = 0
    documents: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_days(self) -> float:
        """Calculate process duration in days"""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 86400
    
    @property
    def is_active(self) -> bool:
        """Check if process is currently active"""
        return self.status == ProcessStatus.IN_PROGRESS
    
    @property
    def is_completed(self) -> bool:
        """Check if process is completed"""
        return self.status == ProcessStatus.COMPLETED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status.value,
            "authority": self.authority,
            "level": self.level,
            "documents": self.documents,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Process":
        """Create Process from dictionary"""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            status=ProcessStatus(data.get("status", "planned")),
            authority=data.get("authority"),
            level=data.get("level", 0),
            documents=data.get("documents", []),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
        )


class ProcessModel(Observable):
    """
    Model for managing processes with Observable support
    
    Provides CRUD operations and notifies observers of changes.
    """
    
    def __init__(self):
        """Initialize process model"""
        super().__init__()
        self._processes: Dict[str, Process] = {}
    
    def add_process(self, process: Process):
        """
        Add a new process
        
        Args:
            process: Process to add
        """
        self._processes[process.id] = process
        self.notify(event="process_added", process=process)
    
    def update_process(self, process_id: str, **kwargs):
        """
        Update process fields
        
        Args:
            process_id: ID of process to update
            **kwargs: Fields to update
        """
        if process_id in self._processes:
            process = self._processes[process_id]
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(process, key):
                    setattr(process, key, value)
            
            self.notify(event="process_updated", process_id=process_id, process=process)
    
    def remove_process(self, process_id: str):
        """
        Remove a process
        
        Args:
            process_id: ID of process to remove
        """
        if process_id in self._processes:
            process = self._processes.pop(process_id)
            self.notify(event="process_removed", process_id=process_id, process=process)
    
    def get_process(self, process_id: str) -> Optional[Process]:
        """
        Get process by ID
        
        Args:
            process_id: Process ID
        
        Returns:
            Process if found, None otherwise
        """
        return self._processes.get(process_id)
    
    def get_all_processes(self) -> List[Process]:
        """
        Get all processes
        
        Returns:
            List of all processes
        """
        return list(self._processes.values())
    
    def get_processes_by_status(self, status: ProcessStatus) -> List[Process]:
        """
        Get processes filtered by status
        
        Args:
            status: Process status to filter by
        
        Returns:
            List of processes with given status
        """
        return [p for p in self._processes.values() if p.status == status]
    
    def get_processes_by_authority(self, authority: str) -> List[Process]:
        """
        Get processes filtered by authority
        
        Args:
            authority: Authority name to filter by
        
        Returns:
            List of processes from given authority
        """
        return [p for p in self._processes.values() if p.authority == authority]
    
    def clear(self):
        """Remove all processes"""
        self._processes.clear()
        self.notify(event="processes_cleared")
    
    def load_processes(self, processes: List[Process]):
        """
        Load multiple processes at once
        
        Args:
            processes: List of processes to load
        """
        self.clear()
        for process in processes:
            self._processes[process.id] = process
        self.notify(event="processes_loaded", count=len(processes))
    
    def get_count(self) -> int:
        """Get total process count"""
        return len(self._processes)
