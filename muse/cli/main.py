import asyncio
import typer
import json
from typing import Optional
from muse.daemon.ipc import send_command
from muse.models.config import load_config

app = typer.Typer(help="Muse - A terminal-first music streamer/downloader/player")

def ensure_daemon():
    """Ensure the daemon is running and reachable."""
    import socket
    from muse.utils.paths import get_base_dir
    import os
    import time

    socket_path = get_base_dir() / "muse.sock"
    
    daemon_ready = False
    if socket_path.exists():
        # Try to connect to see if it's actually alive
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                s.connect(str(socket_path))
                daemon_ready = True
        except (ConnectionRefusedError, socket.timeout):
            # Socket exists but no one is listening
            os.remove(socket_path)
    
    if not daemon_ready:
        start_daemon_background()
        # Wait a bit for the socket to appear and become reachable
        for _ in range(50):
            if socket_path.exists():
                try:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.settimeout(0.1)
                        s.connect(str(socket_path))
                        return # Ready!
                except:
                    pass
            time.sleep(0.1)

def start_daemon_background():
    import subprocess
    import sys
    import os
    from muse.utils.paths import get_base_dir
    
    log_file = get_base_dir() / "daemon_start.log"
    # Use the current directory as PYTHONPATH so muse can be found if not installed in site-packages
    env = {**os.environ}
    if "PYTHONPATH" not in env:
        env["PYTHONPATH"] = os.getcwd()
    else:
        env["PYTHONPATH"] = os.getcwd() + ":" + env["PYTHONPATH"]

    with open(log_file, "a") as f:
        subprocess.Popen(
            [sys.executable, "-m", "muse.daemon.daemon"],
            stdout=f,
            stderr=f,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=env
        )

def run_async(coro):
    ensure_daemon()
    try:
        return asyncio.run(coro)
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command(name="play")
def play(query: Optional[str] = typer.Argument(None, help="Track to play (search query or URL)")):
    """Play a track or resume playback."""
    response = run_async(send_command({
        "command": "play",
        "params": {"query": query}
    }))
    typer.echo(response.get("message", response))

@app.command(name="p", hidden=True)
def p(query: Optional[str] = typer.Argument(None, help="Track to play (search query or URL)")):
    """Short handle for play."""
    play(query)

@app.command()
def pause():
    """Pause playback."""
    response = run_async(send_command({"command": "pause"}))
    typer.echo(response.get("message", response))

@app.command()
def stop():
    """Stop playback and clear queue."""
    response = run_async(send_command({"command": "stop"}))
    typer.echo(response.get("message", response))

@app.command()
def next():
    """Skip to the next track."""
    response = run_async(send_command({"command": "next"}))
    typer.echo(response.get("message", response))

@app.command()
def skip():
    """Alias for next."""
    next()

@app.command()
def prev():
    """Go back to the previous track."""
    response = run_async(send_command({"command": "prev"}))
    typer.echo(response.get("message", response))

@app.command(name="queue")
def queue(query: Optional[str] = typer.Argument(None, help="Track to add to queue")):
    """View or add to the playback queue."""
    response = run_async(send_command({
        "command": "queue",
        "params": {"query": query}
    }))
    typer.echo(response.get("message", response))

@app.command(name="q", hidden=True)
def q(query: Optional[str] = typer.Argument(None, help="Track to add to queue")):
    """Short handle for queue."""
    queue(query)

@app.command(name="loopqueue")
def loopqueue():
    """Toggle queue looping."""
    response = run_async(send_command({"command": "loopqueue"}))
    typer.echo(response.get("message", response))

@app.command(name="shuffle")
def shuffle():
    """Shuffle the current queue."""
    response = run_async(send_command({"command": "shuffle"}))
    typer.echo(response.get("message", response))

@app.command(name="l", hidden=True)
def l():
    """Short handle for loopqueue."""
    loopqueue()

@app.command(name="list")
def list_tracks():
    """List all available local tracks."""
    response = run_async(send_command({"command": "list"}))
    typer.echo(response.get("message", response))

@app.command(name="ls", hidden=True)
def ls():
    """Alias for list."""
    list_tracks()

@app.command()
def search(query: str):
    """Search for tracks."""
    response = run_async(send_command({
        "command": "search",
        "params": {"query": query}
    }))
    typer.echo(response.get("message", response))

@app.command(name="s", hidden=True)
def s(query: str):
    """Short handle for search."""
    search(query)

@app.command()
def current():
    """Show current track info."""
    response = run_async(send_command({"command": "current"}))
    typer.echo(response.get("message", response))

@app.command()
def status():
    """Show detailed playback status (ideal for watch -n 1)."""
    response = run_async(send_command({"command": "status"}))
    if response.get("status") != "ok":
        typer.echo(f"Error: {response.get('message', 'Unknown error')}")
        return

    data = response.get("data", {})
    track = data.get("track")
    
    if not track:
        typer.echo("Nothing is currently playing.")
        return

    # Formatting time
    def format_time(seconds):
        seconds = int(seconds)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    pos = data.get("position", 0)
    dur = data.get("duration", 0)
    if dur == 0 and track.get("duration"):
        dur = track["duration"]
    
    # Header: Currently Playing
    status_icon = "⏸" if data.get("paused") else "▶"
    typer.secho(f"{status_icon} Currently Playing:", fg=typer.colors.CYAN, bold=True)
    typer.echo(f"  {track['title']} - {track['artist']}")
    
    # ASCII Bar
    bar_width = 40
    if dur > 0:
        progress = min(pos / dur, 1.0)
        filled = int(bar_width * progress)
        bar = "█" * filled + "░" * (bar_width - filled)
        time_str = f"{format_time(pos)} / {format_time(dur)}"
        typer.echo(f"  {bar} {time_str}")
    else:
        typer.echo(f"  {'░' * bar_width} {format_time(pos)} / --:--")

    # Queue
    queue = data.get("queue", [])
    loop_msg = " (Looping Enabled)" if data.get("loop_queue") else ""
    typer.echo()
    typer.secho(f"Upcoming Queue{loop_msg}:", fg=typer.colors.MAGENTA, bold=True)
    if not queue:
        typer.echo("  (Empty)")
    else:
        for i, t in enumerate(queue[:5]): # Show next 5
            typer.echo(f"  {i+1}. {t['title']} - {t['artist']}")
        if len(queue) > 5:
            typer.echo(f"  ... and {len(queue) - 5} more")

@app.command(name="st", hidden=True)
def st():
    """Short handle for status."""
    status()

@app.command()
def volume(value: int = typer.Argument(..., help="Volume level (0-100)")):
    """Set or show volume."""
    response = run_async(send_command({
        "command": "volume",
        "params": {"value": value}
    }))
    typer.echo(response.get("message", response))

@app.command()
def download(query: str):
    """Download a track from YouTube."""
    response = run_async(send_command({
        "command": "download",
        "params": {"query": query}
    }))
    typer.echo(response.get("message", response))

@app.command(name="delete")
def top_delete(name: str):
    """Delete a playlist."""
    response = run_async(send_command({
        "command": "playlist_delete",
        "params": {"name": name}
    }))
    typer.echo(response.get("message", response))

playlist_app = typer.Typer(help="Playlist management commands")
app.add_typer(playlist_app, name="playlist")

@playlist_app.command("create")
def playlist_create(name: str):
    """Create a new empty playlist."""
    response = run_async(send_command({
        "command": "playlist_create",
        "params": {"name": name}
    }))
    typer.echo(response.get("message", response))

@playlist_app.command("remove")
def playlist_remove(name: str):
    """Remove songs from a playlist."""
    # First get the playlist
    response = run_async(send_command({
        "command": "playlist_get",
        "params": {"name": name}
    }))
    if response.get("status") != "ok":
        typer.echo(response.get("message", "Error fetching playlist"))
        return
    
    playlist = response.get("data", {})
    tracks = playlist.get("tracks", [])
    if not tracks:
        typer.echo(f"Playlist '{name}' is empty.")
        return
    
    typer.echo(f"Tracks in playlist '{name}':")
    for i, t in enumerate(tracks):
        typer.echo(f"{i}. {t['title']} - {t['artist']}")
    
    indices_str = typer.prompt("Enter indices to remove (comma-separated)")
    try:
        indices = [int(i.strip()) for i in indices_str.split(",") if i.strip()]
        if not indices:
            return
        
        response = run_async(send_command({
            "command": "playlist_remove_indices",
            "params": {"name": name, "indices": indices}
        }))
        typer.echo(response.get("message", response))
    except ValueError:
        typer.echo("Invalid input. Please enter numbers separated by commas.")

@playlist_app.command("add")
def playlist_add(name: str, query: Optional[str] = typer.Argument(None)):
    """Add a song to a playlist."""
    if query:
        response = run_async(send_command({
            "command": "playlist_add",
            "params": {"name": name, "query": query}
        }))
        typer.echo(response.get("message", response))
    else:
        # Get all local tracks and current playlist tracks
        response = run_async(send_command({"command": "list"}))
        # Wait, 'list' returns a string in current implementation.
        # I should add a command that returns raw track data.
        
        # Let's add 'playlist_get_candidates' to daemon or similar
        # For now, let's use search with '*' or similar if supported, or fix 'list'
        
        # Let's use a new daemon command 'playlist_candidates'
        response = run_async(send_command({
            "command": "playlist_candidates",
            "params": {"name": name}
        }))
        if response.get("status") != "ok":
            typer.echo(response.get("message", "Error fetching candidates"))
            return
        
        candidates = response.get("data", [])
        if not candidates:
            typer.echo("No new local tracks found to add.")
            return
        
        typer.echo(f"Available tracks to add to '{name}':")
        for i, t in enumerate(candidates):
            typer.echo(f"{i}. {t['title']} - {t['artist']}")
        
        indices_str = typer.prompt("Enter indices to add (comma-separated)")
        try:
            indices = [int(i.strip()) for i in indices_str.split(",") if i.strip()]
            if not indices:
                return
            
            # Add them one by one or add a bulk add command
            added = 0
            for idx in indices:
                if 0 <= idx < len(candidates):
                    track = candidates[idx]
                    # We can use the track ID or title
                    run_async(send_command({
                        "command": "playlist_add",
                        "params": {"name": name, "query": track['id']}
                    }))
                    added += 1
            typer.echo(f"Added {added} tracks to playlist '{name}'")
        except ValueError:
            typer.echo("Invalid input. Please enter numbers separated by commas.")

@playlist_app.command("play")
def playlist_play(name: str):
    """Play a playlist (adds all tracks to queue)."""
    response = run_async(send_command({
        "command": "playlist_play",
        "params": {"name": name}
    }))
    typer.echo(response.get("message", response))

@playlist_app.command("list")
def playlist_list():
    """List all available playlists."""
    response = run_async(send_command({"command": "playlist_list"}))
    if response.get("status") == "ok":
        playlists = response.get("data", [])
        if not playlists:
            typer.echo("No playlists found.")
        else:
            typer.echo("Playlists:")
            for pl in playlists:
                typer.echo(f" - {pl}")
    else:
        typer.echo(response.get("message", response))

daemon_app = typer.Typer(help="Daemon management commands")
app.add_typer(daemon_app, name="daemon")

@daemon_app.command("start")
def daemon_start(foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground")):
    """Start the Muse daemon."""
    if foreground:
        from muse.daemon.daemon import MuseDaemon
        daemon = MuseDaemon()
        asyncio.run(daemon.start())
    else:
        import subprocess
        import sys
        import os
        from muse.utils.paths import get_base_dir
        
        log_file = get_base_dir() / "daemon_start.log"
        with open(log_file, "w") as f:
            subprocess.Popen(
                [sys.executable, "-m", "muse.daemon.daemon"],
                stdout=f,
                stderr=f,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                env={**os.environ, "PYTHONPATH": os.getcwd()}
            )
        typer.echo(f"Daemon started in background. Logs: {log_file}")

@daemon_app.command("stop")
def daemon_stop():
    """Stop the Muse daemon."""
    try:
        response = run_async(send_command({"command": "quit"}))
        typer.echo(response.get("message", response))
    except Exception:
        typer.echo("Failed to stop daemon (maybe it's not running).")

if __name__ == "__main__":
    app()
