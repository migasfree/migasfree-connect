
import asyncio
import json
import logging
import ssl
import subprocess
import sys
import uuid
from contextlib import suppress
from typing import Dict, List, Optional, Tuple, Union

import websockets
from .utils.crypto import extract_cn_from_cert

logger = logging.getLogger(__name__)

BUFFER_SIZE = 8192
WEBSOCKET_CONFIG = {
    'ping_interval': 20,
    'ping_timeout': 60,
    'close_timeout': 10,
    'max_size': 10**7,
}

class TunnelEngine:
    """
    Core engine for establishing TCP-over-WebSocket tunnels.
    """
    def __init__(
        self,
        local_port: int,
        service: str,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        ca: Optional[str] = None,
    ):
        self.local_port = local_port
        self.service = service
        self.cert = cert
        self.key = key
        self.ca = ca
        self.client_cn = extract_cn_from_cert(self.cert) if self.cert else None
        
        self.active = False
        self.server: Optional[asyncio.AbstractServer] = None
        self.active_connections: Dict[str, dict] = {}
        self.relay_url: Optional[str] = None
        self.selected_agent: Optional[dict] = None

    async def start(self, agent: dict) -> None:
        """Starts the local TCP server."""
        self.selected_agent = agent
        self.relay_url = agent.get('relay')
        if not self.relay_url:
            raise ValueError("Agent has no registered Relay URL")

        self.server = await asyncio.start_server(
            self._handle_tcp_client,
            '127.0.0.1',
            self.local_port,
        )
        self.active = True
        print(f'✅ Tunnel listening on port {self.local_port}')

    async def stop(self) -> None:
        """Stops the engine and closes all connections."""
        self.active = False
        for tunnel_id, conn in list(self.active_connections.items()):
            for task in conn.get('tasks', []):
                if not task.done():
                    task.cancel()
            
            ws = conn.get('ws')
            if ws:
                with suppress(Exception):
                    await ws.close()
            
            writer = conn.get('writer')
            if writer:
                with suppress(Exception):
                    writer.close()
                    await writer.wait_closed()
        
        self.active_connections.clear()
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print('🔌 Tunnel closed')

    def _get_ssl_context(self) -> Optional[ssl.SSLContext]:
        if not self.relay_url.startswith('wss://'):
            return None
            
        if self.ca:
            ssl_context = ssl.create_default_context()
            ssl_context.load_verify_locations(cafile=self.ca)
        else:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        if self.cert and self.key:
            ssl_context.load_cert_chain(certfile=self.cert, keyfile=self.key)
        
        return ssl_context

    async def _handle_tcp_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        tunnel_id = f'cli-{uuid.uuid4()}'
        ws = None
        try:
            extra_headers = {}
            if self.selected_agent:
                extra_headers['X-Agent-ID'] = self.selected_agent['id']
                if 'server_ip' in self.selected_agent:
                    extra_headers['X-Server-IP'] = self.selected_agent['server_ip']

            connect_kwargs = WEBSOCKET_CONFIG.copy()
            ssl_ctx = self._get_ssl_context()
            if ssl_ctx:
                connect_kwargs['ssl'] = ssl_ctx

            # Connection logic with fallback for websockets versions
            try:
                connect_kwargs['extra_headers'] = extra_headers
                ws = await asyncio.wait_for(websockets.connect(self.relay_url, **connect_kwargs), timeout=5)
            except TypeError as e:
                if 'extra_headers' in str(e):
                    del connect_kwargs['extra_headers']
                    connect_kwargs['additional_headers'] = extra_headers
                    ws = await asyncio.wait_for(websockets.connect(self.relay_url, **connect_kwargs), timeout=5)
                else:
                    raise

            # Protocol handshake
            await ws.send(json.dumps({'type': 'connect_client', 'mode': 'tcp_tunnel'}))
            await ws.recv()

            await ws.send(json.dumps({
                'type': 'start_tcp_tunnel',
                'id': self.selected_agent['id'],
                'tunnel_id': tunnel_id,
                'service': self.service,
                'client_cn': self.client_cn,
            }))

            resp = await asyncio.wait_for(ws.recv(), timeout=10)
            resp_data = json.loads(resp)
            if resp_data.get('type') != 'tunnel_started':
                logger.error(f"Error starting tunnel: {resp_data.get('message')}")
                return

            async def tcp_to_ws():
                try:
                    while self.active:
                        data = await reader.read(BUFFER_SIZE)
                        if not data: break
                        await ws.send(json.dumps({'type': 'tunnel_data', 'tunnel_id': tunnel_id, 'data': data.hex()}))
                except Exception: pass

            async def ws_to_tcp():
                try:
                    async for msg in ws:
                        if not self.active: break
                        message = json.loads(msg)
                        if message.get('type') == 'tunnel_data':
                            data_hex = message.get('data', '')
                            if data_hex:
                                writer.write(bytes.fromhex(data_hex))
                                await writer.drain()
                        elif message.get('type') == 'tunnel_closed':
                            break
                except Exception: pass

            task_tcp = asyncio.ensure_future(tcp_to_ws())
            task_ws = asyncio.ensure_future(ws_to_tcp())
            self.active_connections[tunnel_id] = {'ws': ws, 'writer': writer, 'tasks': [task_tcp, task_ws]}
            await asyncio.gather(task_tcp, task_ws, return_exceptions=True)

        except Exception as e:
            if self.active: logger.error(f"Tunnel error: {e}")
        finally:
            self.active_connections.pop(tunnel_id, None)
            if ws:
                with suppress(Exception):
                    if hasattr(ws, 'open') and ws.open:
                        await ws.send(json.dumps({'type': 'close_tunnel', 'tunnel_id': tunnel_id}))
                    await ws.close()
            with suppress(Exception):
                writer.close()
                await writer.wait_closed()
