from collections import deque
import random
from typing import Optional
from muse.models.track import Track

class QueueManager:
    def __init__(self):
        self.current: Optional[Track] = None
        self.queue: deque[Track] = deque()
        self.history: deque[Track] = deque(maxlen=100)
        self.loop_queue: bool = False

    def add(self, track: Track, top: bool = False):
        if top:
            self.queue.appendleft(track)
        else:
            self.queue.append(track)

    def next(self) -> Optional[Track]:
        if self.current:
            if self.loop_queue:
                self.queue.append(self.current)
            else:
                self.history.append(self.current)
        
        if not self.queue:
            self.current = None
            return None
        
        self.current = self.queue.popleft()
        return self.current

    def toggle_loop(self) -> bool:
        self.loop_queue = not self.loop_queue
        return self.loop_queue

    def previous(self) -> Optional[Track]:
        if not self.history:
            return None
        
        if self.current:
            self.queue.appendleft(self.current)
        
        self.current = self.history.pop()
        return self.current

    def clear(self):
        self.queue.clear()
        self.current = None

    def shuffle(self):
        temp_list = list(self.queue)
        random.shuffle(temp_list)
        self.queue = deque(temp_list)

    def remove(self, index: int) -> Optional[Track]:
        if 0 <= index < len(self.queue):
            # This is inefficient for deque but fine for small queues
            temp_list = list(self.queue)
            track = temp_list.pop(index)
            self.queue = deque(temp_list)
            return track
        return None

    def get_queue(self) -> list[Track]:
        return list(self.queue)

    def to_dict(self):
        return {
            "current": self.current.to_dict() if self.current else None,
            "queue": [t.to_dict() for t in self.queue],
            "history": [t.to_dict() for t in self.history],
            "loop_queue": self.loop_queue
        }

    def from_dict(self, data):
        self.current = Track.from_dict(data["current"]) if data.get("current") else None
        self.queue = deque([Track.from_dict(t) for t in data.get("queue", [])])
        self.history = deque([Track.from_dict(t) for t in data.get("history", [])], maxlen=100)
        self.loop_queue = data.get("loop_queue", False)
