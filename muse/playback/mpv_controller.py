import os
import subprocess
import time
from python_mpv_jsonipc import MPV
from loguru import logger
from muse.models.config import Config

class MPVController:
    def __init__(self, config: Config):
        self.ipc_path = config.playback.mpv_ipc_path
        self.mpv = None
        self._process = None
        self._event_callbacks = []

    def start(self):
        """Start mpv process and connect to IPC."""
        if self.mpv:
            return

        logger.info(f"Starting mpv with IPC at {self.ipc_path}")
        
        # Ensure the socket directory exists
        socket_dir = os.path.dirname(self.ipc_path)
        if socket_dir and not os.path.exists(socket_dir):
            os.makedirs(socket_dir, exist_ok=True)

        # Cleanup existing socket
        if os.path.exists(self.ipc_path):
            try:
                os.remove(self.ipc_path)
            except:
                pass

        # Launch mpv
        self._process = subprocess.Popen(
            ["mpv", "--idle", f"--input-ipc-server={self.ipc_path}", "--no-video"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for socket to be created
        max_retries = 20
        for _ in range(max_retries):
            if os.path.exists(self.ipc_path):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"Failed to start mpv: {self.ipc_path} not created")

        # Connect to IPC
        self.mpv = MPV(start_mpv=False, ipc_socket=self.ipc_path)
        
        # Register event handler
        @self.mpv.on_event("end-file")
        def handle_end_file(event):
            logger.debug(f"MPV event: end-file {event}")
            for cb in self._event_callbacks:
                cb("end-file", event)

        logger.info("Connected to mpv IPC")

    def register_callback(self, callback):
        self._event_callbacks.append(callback)

    def stop(self):
        """Stop mpv and cleanup."""
        if self.mpv:
            try:
                self.mpv.terminate()
            except:
                pass
            self.mpv = None
        
        if self._process:
            self._process.terminate()
            self._process.wait()
            self._process = None
        
        if os.path.exists(self.ipc_path):
            try:
                os.remove(self.ipc_path)
            except:
                pass

    def play_file(self, file_path: str, position: float = 0):
        """Load and play a file."""
        if not self.mpv:
            self.start()
        logger.info(f"Playing file: {file_path} from position {position}")
        
        # Use start option for loadfile to avoid seek errors
        options = {}
        if position > 0:
            options["start"] = f"{position}"
        
        # python-mpv-jsonipc might not support passing options via loadfile method directly 
        # as a dict, let's use command() if needed or check if it supports it.
        # Actually, let's use the command interface to be safe.
        self.mpv.command("loadfile", file_path, "replace", options)
        self.mpv.pause = False

    def seek(self, position: float, mode: str = "absolute"):
        """Seek to position."""
        if self.mpv:
            self.mpv.seek(position, mode)

    def pause(self):
        """Pause playback."""
        if self.mpv:
            self.mpv.pause = True

    def resume(self):
        """Resume playback."""
        if self.mpv:
            self.mpv.pause = False

    def toggle_pause(self):
        """Toggle pause state."""
        if self.mpv:
            self.mpv.pause = not self.mpv.pause

    def get_playback_info(self) -> dict:
        """Get current playback position and duration."""
        if not self.mpv:
            return {"position": 0, "duration": 0}
        
        try:
            # We use try/except because properties might be None if nothing is playing
            pos = self.mpv.time_pos
            dur = self.mpv.duration
            return {
                "position": pos if pos is not None else 0,
                "duration": dur if dur is not None else 0
            }
        except:
            return {"position": 0, "duration": 0}

    def quit(self):
        """Quit mpv."""
        self.stop()
