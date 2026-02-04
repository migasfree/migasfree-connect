
import sys
import os
import unittest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from migasfree_connect.tunnel import TunnelEngine

class TestTunnelEngine(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.engine = TunnelEngine(local_port=1234, service="ssh")

    def test_init(self):
        self.assertEqual(self.engine.local_port, 1234)
        self.assertEqual(self.engine.service, "ssh")
        self.assertFalse(self.engine.active)

    def test_get_ssl_context_none(self):
        self.engine.relay_url = "ws://relay.example.com"
        ctx = self.engine._get_ssl_context()
        self.assertIsNone(ctx)

    def test_get_ssl_context_wss(self):
        self.engine.relay_url = "wss://relay.example.com"
        with patch('ssl.create_default_context') as mock_ctx:
            ctx = self.engine._get_ssl_context()
            self.assertIsNotNone(ctx)

    async def test_start_fail_no_relay(self):
        with self.assertRaises(ValueError):
            await self.engine.start({})

    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_handle_tcp_client_flow(self, mock_ws_connect):
        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.recv.side_effect = [
            json.dumps({"type": "connect_ok"}),
            json.dumps({"type": "tunnel_started"})
        ]
        # Simulate receiving data from WS
        mock_ws.__aiter__.return_value = [
            json.dumps({"type": "tunnel_data", "data": "48656c6c6f"}), # "Hello" in hex
            json.dumps({"type": "tunnel_closed"})
        ]
        mock_ws_connect.return_value = mock_ws
        
        # Mock StreamReader/Writer
        mock_reader = AsyncMock()
        mock_reader.read.side_effect = [b"World", b""] # Data TO websocket
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        self.engine.active = True
        self.engine.selected_agent = {"id": "agent1", "relay": "ws://relay"}
        self.engine.relay_url = "ws://relay"
        
        await self.engine._handle_tcp_client(mock_reader, mock_writer)
        
        # Check if "World" was sent to WS (hex encoded)
        # One of the calls to ws.send should contain "576f726c64"
        sent_messages = [json.loads(c.args[0]) for c in mock_ws.send.call_args_list]
        self.assertTrue(any(m.get("data") == "576f726c64" for m in sent_messages if m.get("type") == "tunnel_data"))
        
        # Check if "Hello" (from WS) was written to TCP
        mock_writer.write.assert_called_with(b"Hello")

    async def test_stop(self):
        self.engine.server = MagicMock()
        self.engine.server.wait_closed = AsyncMock()
        self.engine.active = True
        
        # Mock active connections
        mock_ws = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.wait_closed = AsyncMock()
        self.engine.active_connections = {
            "t1": {"ws": mock_ws, "writer": mock_writer, "tasks": [MagicMock()]}
        }
        
        await self.engine.stop()
        self.assertFalse(self.engine.active)
        mock_ws.close.assert_called_once()
        mock_writer.close.assert_called_once()
        self.engine.server.close.assert_called_once()

    def test_get_ssl_context_no_ca(self):
        self.engine.relay_url = "wss://relay"
        self.engine.ca = None
        ctx = self.engine._get_ssl_context()
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.verify_mode, __import__('ssl').CERT_NONE)

if __name__ == '__main__':
    unittest.main()
