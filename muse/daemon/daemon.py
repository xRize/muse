import asyncio
import sys
import os
import json
from loguru import logger
from muse.models.config import load_config
from muse.models.track import Track
from muse.playback.mpv_controller import MPVController
from muse.models.queue import QueueManager
from muse.models.playlist import PlaylistManager
from muse.providers.youtube import YouTubeProvider
from muse.providers.local import LocalProvider
from muse.providers.cache import DownloadManager
from muse.daemon.ipc import IPCServer
from muse.daemon.state import StateManager
from muse.utils.logging import setup_logging
from muse.utils.paths import get_state_file

class MuseDaemon:
    def __init__(self):
        self.config = load_config()
        self.controller = MPVController(self.config)
        self.queue_manager = QueueManager()
        self.playlist_manager = PlaylistManager()
        self.youtube = YouTubeProvider()
        self.local = LocalProvider(self.config)
        self.downloader = DownloadManager()
        self.ipc_server = IPCServer(self.handle_command)
        self.loop = None

    async def start(self):
        self.loop = asyncio.get_running_loop()
        setup_logging(level="DEBUG")
        logger.info(f"Starting Muse Daemon with PATH: {os.environ.get('PATH')}")
        self.controller.start()
        self.controller.register_callback(self.handle_mpv_event)
        self.load_state()
        # Start periodic save
        asyncio.create_task(self.periodic_save())
        await self.ipc_server.start()

    async def periodic_save(self):
        while True:
            await asyncio.sleep(30)
            self.save_state()

    def save_state(self):
        StateManager.save(self.queue_manager, self.controller)

    def load_state(self):
        state = StateManager.load()
        if not state:
            return
        
        try:
            self.queue_manager.from_dict(state.get("queue", {}))
            if self.controller.mpv:
                self.controller.mpv.volume = state.get("volume", 100)
            
            logger.info("Loaded state")
            
            # Optionally resume playback if there was a current track
            if self.queue_manager.current:
                track = self.queue_manager.current
                position = state.get("position", 0)
                logger.info(f"Resuming playback of {track.title} from {position}")
                
                if track.local_path:
                    self.controller.play_file(track.local_path, position=position)
                elif track.source == "youtube" and track.stream_url:
                    self.controller.play_file(track.stream_url, position=position)
                
                # If it's a youtube track but no stream_url, we don't resume automatically 
                # as it requires async resolution which might be better handled when user says 'play'
                # or we can do it here. 
                elif track.source == "youtube" and not track.stream_url:
                    asyncio.create_task(self.resolve_and_resume(track, position))

        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    async def resolve_and_resume(self, track, position):
        try:
            track.stream_url = await self.youtube.resolve_stream_url(track.id)
            self.controller.play_file(track.stream_url, position=position)
        except Exception as e:
            logger.error(f"Failed to resolve and resume {track.title}: {e}")

    def handle_mpv_event(self, event_name, data):
        if event_name == "end-file":
            reason = data.get("reason")
            # 0: EOF, 2: quit, 3: stop, 4: error, 5: redirect
            if reason in ["eof", "unknown"]: # mpv-jsonipc might return strings
                logger.info("Track ended, playing next...")
                if self.loop:
                    self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.play_next()))

    async def play_next(self):
        track = self.queue_manager.next()
        if track:
            logger.info(f"Playing next track: {track.title}")
            if track.local_path:
                self.controller.play_file(track.local_path)
            elif track.source == "youtube":
                # User requested download-then-play for YouTube tracks
                try:
                    # Check if already exists in downloads
                    filename = f"{track.artist} - {track.title}.mp3".replace("/", "_")
                    file_path = self.downloader.download_dir / filename
                    if file_path.exists():
                        track.local_path = str(file_path)
                        self.controller.play_file(track.local_path)
                    else:
                        logger.info(f"Downloading {track.title} before playback")
                        local_path = await self.downloader.download(track)
                        track.local_path = local_path
                        self.controller.play_file(track.local_path)
                        # Refresh local index to include new download
                        self.local.scan()
                except Exception as e:
                    logger.error(f"Failed to download/play YouTube track {track.title}: {e}")
                    # Fallback to streaming if download fails
                    try:
                        if not track.stream_url:
                            track.stream_url = await self.youtube.resolve_stream_url(track.id)
                        self.controller.play_file(track.stream_url)
                    except Exception as e2:
                        logger.error(f"Fallback streaming failed for {track.title}: {e2}")
                        await self.play_next()
                        return
        else:
            logger.info("Queue empty, stopping playback.")
            self.controller.stop()
        
        self.save_state()

    async def _resolve_track(self, query):
        # Try exact local file first
        if os.path.exists(query):
            return Track(
                id=query,
                title=os.path.basename(query),
                artist="Unknown",
                duration=0,
                source="local",
                local_path=os.path.abspath(query)
            )
        
        # Try fuzzy local search
        local_tracks = self.local.search(query)
        if local_tracks:
            return local_tracks[0]
        
        # Search YouTube
        tracks = await self.youtube.search(query, limit=1)
        if not tracks:
            return None
        
        return tracks[0]

    async def handle_command(self, message):
        command = message.get("command")
        params = message.get("params", {})
        
        logger.info(f"Handling command: {command} with params: {params}")
        
        try:
            if command == "play":
                query = params.get("query")
                if query:
                    track = await self._resolve_track(query)
                    if not track:
                        return {"status": "error", "message": f"No results for: {query}"}
                    
                    self.queue_manager.clear()
                    self.queue_manager.add(track)
                    await self.play_next()
                    self.save_state()
                    return {"status": "ok", "message": f"Playing {track.title} - {track.artist}"}
                else:
                    self.controller.resume()
                    self.save_state()
                    return {"status": "ok", "message": "Resumed playback"}
            
            elif command == "queue":
                query = params.get("query")
                if query:
                    track = await self._resolve_track(query)
                    if not track:
                        return {"status": "error", "message": f"No results for: {query}"}
                    
                    self.queue_manager.add(track)
                    self.save_state()
                    return {"status": "ok", "message": f"Added {track.title} - {track.artist} to queue"}
                else:
                    queue_list = self.queue_manager.get_queue()
                    if not queue_list:
                        return {"status": "ok", "message": "Queue is empty"}
                    msg = "Queue:\n" + "\n".join([f"{i+1}. {t.title} - {t.artist}" for i, t in enumerate(queue_list)])
                    if self.queue_manager.loop_queue:
                        msg += "\n(Looping enabled)"
                    return {"status": "ok", "message": msg}

            elif command == "loopqueue":
                enabled = self.queue_manager.toggle_loop()
                self.save_state()
                return {"status": "ok", "message": f"Queue looping {'enabled' if enabled else 'disabled'}"}

            elif command == "shuffle":
                self.queue_manager.shuffle()
                self.save_state()
                return {"status": "ok", "message": "Queue shuffled"}

            elif command == "list":
                self.local.scan()
                tracks = list(self.local.index.values())
                if not tracks:
                    return {"status": "ok", "message": "No local songs found"}
                msg = "Available songs:\n" + "\n".join([f"{t.title} - {t.artist}" for t in sorted(tracks, key=lambda x: x.title)])
                return {"status": "ok", "message": msg}

            elif command == "search":
                query = params.get("query")
                # Search local first
                local_tracks = self.local.search(query)
                # Then YouTube
                yt_tracks = await self.youtube.search(query)
                
                results = []
                if local_tracks:
                    results.append("Local Results:")
                    results.extend([f"L: {t.title} - {t.artist}" for t in local_tracks])
                
                if yt_tracks:
                    if results: results.append("")
                    results.append("YouTube Results:")
                    results.extend([f"Y: {t.title} - {t.artist} ({t.id})" for t in yt_tracks])
                
                if not results:
                    return {"status": "ok", "message": "No results found"}
                
                return {"status": "ok", "message": "\n".join(results)}

            elif command == "pause":
                self.controller.pause()
                self.save_state()
                return {"status": "ok", "message": "Paused playback"}
            
            elif command == "stop":
                self.queue_manager.clear()
                self.controller.stop()
                self.save_state()
                return {"status": "ok", "message": "Stopped playback and cleared queue"}
            
            elif command == "next":
                await self.play_next()
                self.save_state()
                return {"status": "ok", "message": "Skipped to next track"}
            
            elif command == "prev":
                track = self.queue_manager.previous()
                if track:
                    if track.local_path:
                        self.controller.play_file(track.local_path)
                    elif track.source == "youtube" and track.stream_url:
                        self.controller.play_file(track.stream_url)
                    self.save_state()
                    return {"status": "ok", "message": f"Playing previous track: {track.title}"}
                return {"status": "error", "message": "No previous track"}

            elif command == "current":
                track = self.queue_manager.current
                if track:
                    return {"status": "ok", "message": f"Currently playing: {track.title} - {track.artist} [{track.source}]"}
                return {"status": "ok", "message": "Nothing is currently playing"}

            elif command == "status":
                track = self.queue_manager.current
                pb_info = self.controller.get_playback_info()
                queue = self.queue_manager.get_queue()
                
                return {
                    "status": "ok",
                    "data": {
                        "track": track.to_dict() if track else None,
                        "position": pb_info["position"],
                        "duration": pb_info["duration"],
                        "queue": [t.to_dict() for t in queue],
                        "loop_queue": self.queue_manager.loop_queue,
                        "paused": self.controller.mpv.pause if self.controller.mpv else True
                    }
                }

            elif command == "volume":
                value = params.get("value")
                if self.controller.mpv:
                    self.controller.mpv.volume = value
                    self.save_state()
                    return {"status": "ok", "message": f"Volume set to {value}"}
                return {"status": "error", "message": "MPV not running"}

            elif command == "download":
                query = params.get("query")
                if not query:
                    return {"status": "error", "message": "Query required for download"}
                
                # Search for the track first
                tracks = await self.youtube.search(query, limit=1)
                if not tracks:
                    return {"status": "error", "message": f"No results for: {query}"}
                
                track = tracks[0]
                # Start download in background task
                asyncio.create_task(self.downloader.download(track))
                return {"status": "ok", "message": f"Started download of {track.title} - {track.artist}"}

            elif command.startswith("playlist_"):
                pl_command = command.split("_", 1)[1]
                name = params.get("name")
                
                if pl_command == "create":
                    if self.playlist_manager.create(name):
                        return {"status": "ok", "message": f"Playlist '{name}' created"}
                    return {"status": "error", "message": f"Playlist '{name}' already exists"}
                
                elif pl_command == "delete":
                    if self.playlist_manager.delete(name):
                        return {"status": "ok", "message": f"Playlist '{name}' deleted"}
                    return {"status": "error", "message": f"Playlist '{name}' not found"}
                
                elif pl_command == "list":
                    playlists = self.playlist_manager.list_playlists()
                    return {"status": "ok", "data": playlists}
                
                elif pl_command == "get":
                    playlist = self.playlist_manager.get_playlist(name)
                    if not playlist:
                        return {"status": "error", "message": f"Playlist '{name}' not found"}
                    return {"status": "ok", "data": playlist.to_dict()}
                
                elif pl_command == "add":
                    playlist = self.playlist_manager.get_playlist(name)
                    if not playlist:
                        return {"status": "error", "message": f"Playlist '{name}' not found"}
                    
                    query = params.get("query")
                    track = await self._resolve_track(query)
                    if not track:
                        return {"status": "error", "message": f"No results for: {query}"}
                    
                    playlist.tracks.append(track)
                    self.playlist_manager.save()
                    return {"status": "ok", "message": f"Added {track.title} to playlist '{name}'"}
                
                elif pl_command == "candidates":
                    playlist = self.playlist_manager.get_playlist(name)
                    if not playlist:
                        return {"status": "error", "message": f"Playlist '{name}' not found"}
                    
                    self.local.scan()
                    all_local = list(self.local.index.values())
                    playlist_track_ids = {t.id for t in playlist.tracks}
                    
                    candidates = [t.to_dict() for t in all_local if t.id not in playlist_track_ids]
                    return {"status": "ok", "data": candidates}
                
                elif pl_command == "remove_indices":
                    playlist = self.playlist_manager.get_playlist(name)
                    if not playlist:
                        return {"status": "error", "message": f"Playlist '{name}' not found"}
                    
                    indices = sorted(params.get("indices", []), reverse=True)
                    removed = 0
                    for idx in indices:
                        if 0 <= idx < len(playlist.tracks):
                            playlist.tracks.pop(idx)
                            removed += 1
                    
                    self.playlist_manager.save()
                    return {"status": "ok", "message": f"Removed {removed} tracks from playlist '{name}'"}
                
                elif pl_command == "play":
                    playlist = self.playlist_manager.get_playlist(name)
                    if not playlist:
                        return {"status": "error", "message": f"Playlist '{name}' not found"}
                    
                    for track in playlist.tracks:
                        self.queue_manager.add(track)
                    
                    if not self.queue_manager.current:
                        await self.play_next()
                    
                    self.save_state()
                    return {"status": "ok", "message": f"Added playlist '{name}' to queue"}

            elif command == "quit":
                asyncio.create_task(self.shutdown())
                return {"status": "ok", "message": "Daemon shutting down"}
            
            else:
                return {"status": "error", "message": f"Unknown command: {command}"}
        except Exception as e:
            logger.exception("Error executing command")
            return {"status": "error", "message": str(e)}

    async def shutdown(self):
        logger.info("Shutting down daemon...")
        self.save_state()
        self.controller.stop()
        sys.exit(0)

if __name__ == "__main__":
    daemon = MuseDaemon()
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        pass
