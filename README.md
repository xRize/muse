<<<<<<< HEAD
# muse
Muse is a terminal-first music streamer, downloader, and player inspired by Rhythm. It’s built around speed, low overhead, and a clean CLI workflow.
=======
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

Pause playback:

```bash
muse pause
```

Skip to the next track:

```bash
muse next
```

PRO TIP: Miniplayer

```bash
watch -t -n 0.1 muse status
```

---

## Commands

| Command             | Short Alias | Description                                |
| ------------------- | ----------- | ------------------------------------------ |
| `play [query]`      | `p`         | Play a track or resume playback            |
| `queue [query]`     | `q`         | Add a track to the queue or show the queue |
| `pause`             | —           | Pause playback                             |
| `stop`              | —           | Stop playback and clear the queue          |
| `next` / `skip`     | —           | Skip to the next track                     |
| `prev`              | —           | Return to the previous track               |
| `loopqueue`         | `l`         | Toggle queue looping                       |
| `search <query>`    | `s`         | Search local and YouTube tracks            |
| `list`              | `ls`        | List available local tracks                |
| `current`           | —           | Show the currently playing track           |
| `volume <0-100>`    | —           | Set playback volume                        |
| `download <query>`  | —           | Download a track to the local library      |
| `daemon start/stop` | —           | Manually manage the daemon                 |

---

## Storage Layout

| Path                  | Purpose                             |
| --------------------- | ----------------------------------- |
| `~/.muse/config.toml` | Configuration                       |
| `~/.muse/state.json`  | Persistent queue and playback state |
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

* Playlist support
* Lyrics integration
* TUI mode
* Multi-source streaming support

---

## License

MIT License.

>>>>>>> ae66f6b (Initial commit)
