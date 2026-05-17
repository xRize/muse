import asyncio
import json
import os
from loguru import logger
from muse.utils.paths import get_socket_path

class IPCServer:
    def __init__(self, handler):
        self.handler = handler
        self.socket_path = get_socket_path()

    async def start(self):
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        
        server = await asyncio.start_unix_server(self.handle_client, self.socket_path)
        logger.info(f"IPC Server started at {self.socket_path}")
        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        data = await reader.read()
        if not data:
            writer.close()
            return

        try:
            message = json.loads(data.decode())
            logger.debug(f"Received message: {message}")
            response = await self.handler(message)
            writer.write(json.dumps(response).encode())
            writer.write_eof()
            await writer.drain()
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            writer.write(json.dumps({"status": "error", "message": str(e)}).encode())
            await writer.drain()
        finally:
            writer.close()

async def send_command(command: dict):
    socket_path = get_socket_path()
    if not os.path.exists(socket_path):
        raise ConnectionError("Daemon not running (socket not found)")

    reader, writer = await asyncio.open_unix_connection(socket_path)
    writer.write(json.dumps(command).encode())
    writer.write_eof()
    await writer.drain()

    data = await reader.read()
    writer.close()
    await writer.wait_closed()
    
    if not data:
        return {"status": "error", "message": "No response from daemon"}
    
    return json.loads(data.decode())
