<<<<<<< HEAD
<img width="600" height="600" alt="muse logo" src="https://github.com/user-attachments/assets/c5d3bb3b-76b4-405c-8b7a-526d65353498" />

=======
>>>>>>> 35e44b6 (added playlist support)
# Muse

**Muse** is a terminal-first music streamer, downloader, and player inspired by Rhythm. It’s built around speed, low overhead, and a clean CLI workflow.

Unlike most terminal music players, Muse uses a daemon-based architecture. Your music keeps playing even if you close the terminal, disconnect an SSH session, or launch commands from another shell.

---

## Features

* Fast, stateless CLI commands
* Persistent background daemon
* YouTube Music search and streaming
* Fuzzy local library search
* Automatic downloads and caching
* Persistent queue and playback state
* Queue looping and shuffle support
* Playlist management
* Powered by `mpv` for playback

---

## Requirements

| Dependency   | Purpose                         |
| ------------ | ------------------------------- |
| Python 3.12+ | Runtime                         |
| `mpv`        | Audio playback engine           |
| `ffmpeg`     | Audio processing and conversion |

---

## Installation

Clone the repository:

```bash
git clone https://github.com/xRize/muse.git
cd muse
```

Install Muse:

```bash
pipx install .
```
Muse automatically starts its daemon whenever a command is executed, so no extra setup is required.

---

## Quick Start

Play a track:

```bash
muse play "deftones change"
```

Queue a song:

```bash
muse queue "radiohead nude"
```

Create and use a playlist:

```bash
muse playlist create "Favorites"
muse playlist add "Favorites" "Back In Black"
muse playlist play "Favorites"
```

PRO TIP: Miniplayer

```bash
watch -t -n 1 muse status
```

<img width="800" height="503" alt="ezgif-3feedac2e4001ccd" src="https://github.com/user-attachments/assets/551c33d1-68eb-4585-9a01-1bff37f3bdf7" />


---

## Commands

| Command                     | Short Alias | Description                                        |
| --------------------------- | ----------- | -------------------------------------------------- |
| `play [query]`              | `p`         | Play a track or resume playback                    |
| `queue [query]`             | `q`         | Add a track to the queue or show the queue         |
| `shuffle`                   | —           | Shuffle the current queue                          |
| `pause`                     | —           | Pause playback                                     |
| `stop`                      | —           | Stop playback and clear the queue                  |
| `next` / `skip`             | —           | Skip to the next track                             |
| `prev`                      | —           | Return to the previous track                       |
| `loopqueue`                 | `l`         | Toggle queue looping                               |
| `search <query>`            | `s`         | Search local and YouTube tracks                    |
| `list`                      | `ls`        | List available local tracks                        |
| `current`                   | —           | Show the currently playing track                   |
| `status`                    | `st`        | Show detailed playback status                      |
| `volume <0-100>`            | —           | Set playback volume                                |
| `download <query>`          | —           | Download a track to the local library              |
| `playlist create <name>`    | —           | Create a new empty playlist                        |
| `playlist add <name> [q]`   | —           | Add a track to a playlist (interactive if q omitted) |
| `playlist remove <name>`    | —           | Remove tracks from a playlist (interactive)        |
| `playlist list`             | —           | List all available playlists                       |
| `playlist play <name>`      | —           | Add all tracks from a playlist to the queue        |
| `delete <name>`             | —           | Delete a playlist                                  |
| `daemon start/stop`         | —           | Manually manage the daemon                         |

---

## Storage Layout

| Path                  | Purpose                             |
| --------------------- | ----------------------------------- |
| `~/.muse/config.toml` | Configuration                       |
| `~/.muse/state.json`  | Persistent queue and playback state |
| `~/.muse/playlists.json` | Saved playlists                  |
| `~/.muse/downloads/`  | Downloaded tracks                   |
| `~/.muse/muse.log`    | Logs                                |
| `~/.muse/muse.sock`   | Unix socket used by the daemon      |

---

## Architecture

Muse follows a simple client-server model:

1. The CLI sends commands through a Unix socket
2. The daemon receives and processes commands
3. `mpv` handles playback through IPC
4. Playback state is continuously persisted

This approach keeps startup times low while allowing playback to continue independently from the terminal session.

---

## Planned Features

* Lyrics integration
* TUI mode
* Multi-source streaming support

---

## License

MIT License.
