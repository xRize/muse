import os
from pathlib import Path

def get_base_dir() -> Path:
    base_dir = Path.home() / ".muse"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def get_socket_path() -> Path:
    return get_base_dir() / "muse.sock"

def get_state_file() -> Path:
    return get_base_dir() / "state.json"

def get_log_file() -> Path:
    return get_base_dir() / "muse.log"

def get_download_dir() -> Path:
    download_dir = get_base_dir() / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir

def get_config_file() -> Path:
    return get_base_dir() / "config.toml"
