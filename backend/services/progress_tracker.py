"""
Progress tracker for real-time status updates during PDF to XF conversion
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import json

class ProgressEvent:
    def __init__(self, event_type: str, message: str, data: Optional[Dict] = None):
        self.timestamp = datetime.now().isoformat()
        self.event_type = event_type
        self.message = message
        self.data = data or {}

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "message": self.message,
            "data": self.data
        }

class ProgressTracker:
    def __init__(self):
        self.sessions: Dict[str, List[ProgressEvent]] = {}
        self.queues: Dict[str, asyncio.Queue] = {}

    def create_session(self, session_id: str):
        """Create a new progress tracking session"""
        self.sessions[session_id] = []
        self.queues[session_id] = asyncio.Queue()

    def add_event(self, session_id: str, event_type: str, message: str, data: Optional[Dict] = None):
        """Add a progress event to a session"""
        if session_id not in self.sessions:
            self.create_session(session_id)

        event = ProgressEvent(event_type, message, data)
        self.sessions[session_id].append(event)

        # Put event in queue for SSE streaming
        if session_id in self.queues:
            try:
                self.queues[session_id].put_nowait(event)
            except:
                pass

    async def get_events(self, session_id: str):
        """Get all events for a session (for SSE streaming)"""
        if session_id not in self.queues:
            self.create_session(session_id)

        queue = self.queues[session_id]
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event.to_dict())}\n\n"

    def get_session_events(self, session_id: str) -> List[Dict]:
        """Get all events for a session"""
        if session_id not in self.sessions:
            return []
        return [event.to_dict() for event in self.sessions[session_id]]

    def cleanup_session(self, session_id: str):
        """Clean up a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.queues:
            del self.queues[session_id]

# Global progress tracker instance
progress_tracker = ProgressTracker()
