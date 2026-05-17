import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from muse.utils.paths import get_config_file

@dataclass
class PlaybackConfig:
    volume: int = 100
    mpv_ipc_path: str = "/tmp/muse-mpv.sock"

@dataclass
class LibraryConfig:
    paths: list[str] = field(default_factory=lambda: ["~/Music", "~/.muse/downloads"])

@dataclass
class YouTubeConfig:
    enabled: bool = True

@dataclass
class Config:
    playback: PlaybackConfig = field(default_factory=PlaybackConfig)
    library: LibraryConfig = field(default_factory=LibraryConfig)
    youtube: YouTubeConfig = field(default_factory=YouTubeConfig)

def load_config() -> Config:
    config_path = get_config_file()
    if not config_path.exists():
        return Config()
    
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    
    return Config(
        playback=PlaybackConfig(**data.get("playback", {})),
        library=LibraryConfig(**data.get("library", {})),
        youtube=YouTubeConfig(**data.get("youtube", {}))
    )
