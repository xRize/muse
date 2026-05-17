from dataclasses import dataclass

@dataclass
class Track:
    id: str
    title: str
    artist: str
    duration: int
    source: str
    stream_url: str | None = None
    local_path: str | None = None
    thumbnail: str | None = None

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
