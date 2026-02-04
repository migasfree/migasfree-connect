
import sys
import os
import asyncio
import unittest
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from migasfree_connect.cli import execute_remote_command, run_cli

class TestCLI(unittest.IsolatedAsyncioTestCase):

    @patch('websockets.connect')
    @patch('migasfree_connect.manager.ManagerClient.select_agent', new_callable=AsyncMock)
    @patch('migasfree_connect.tunnel.TunnelEngine._get_ssl_context', return_value=None)
    async def test_execute_remote_command_success(self, mock_ssl, mock_select, mock_ws_connect):
        # Setup mocks
        mock_select.return_value = {"id": "agent1", "name": "Agent 1", "relay": "ws://relay"}
        
        class AsyncWSMock:
            def __init__(self):
                self.recv_count = 0
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def send(self, data): pass
            async def recv(self):
                self.recv_count += 1
                if self.recv_count == 1: return json.dumps({"type": "connect_ok"})
                return json.dumps({"type": "exec_started"})
            def __aiter__(self):
                async def gen():
                    yield json.dumps({"type": "exec_output", "data": "hello"})
                    yield json.dumps({"type": "exec_complete", "exit_code": 0})
                return gen()
        
        mock_ws_connect.return_value = AsyncWSMock()
        
        from migasfree_connect.tunnel import TunnelEngine
        from migasfree_connect.manager import ManagerClient
        engine = TunnelEngine(0, "exec")
        manager = ManagerClient("http://manager")
        
        exit_code = await execute_remote_command(engine, manager, "ls")
        self.assertEqual(exit_code, 0)

    @patch('migasfree_connect.cli.argparse.ArgumentParser.parse_args')
    @patch('migasfree_connect.cli.check_credentials')
    @patch('migasfree_connect.cli.ManagerClient.select_agent', new_callable=AsyncMock)
    @patch('migasfree_connect.cli.TunnelEngine.start', new_callable=AsyncMock)
    @patch('migasfree_connect.cli.execute_client')
    @patch('migasfree_connect.cli.TunnelEngine.stop', new_callable=AsyncMock)
    async def test_run_cli_ssh(self, mock_stop, mock_exec_client, mock_start, mock_select, mock_creds, mock_args):
        # Setup mocks
        mock_args.return_value = MagicMock(
            user="tux", type="ssh", agent="agent1", manager="http://manager", port=0, command=None, exec_command=None
        )
        mock_creds.return_value = ("cert", "key", "ca")
        mock_select.return_value = {"id": "agent1", "name": "Agent 1"}
        mock_exec_client.return_value = 0
        
        exit_code = await run_cli()
        self.assertEqual(exit_code, 0)
        mock_start.assert_called_once()
        mock_exec_client.assert_called_once()
        mock_stop.assert_called_once()

    @patch('migasfree_connect.cli.argparse.ArgumentParser.parse_args')
    async def test_run_cli_invalid_ssh(self, mock_args):
        mock_args.return_value = MagicMock(
            user=None, type="ssh", agent="agent1", manager="http://manager", port=0, command=None, exec_command=None
        )
        with patch('sys.stderr', new_callable=MagicMock): # Suppress stderr
            with self.assertRaises(SystemExit):
                await run_cli()

    @patch('migasfree_connect.manager.ManagerClient.select_agent', new_callable=AsyncMock)
    async def test_execute_remote_command_no_agent(self, mock_select):
        mock_select.return_value = None
        from migasfree_connect.tunnel import TunnelEngine
        from migasfree_connect.manager import ManagerClient
        engine = TunnelEngine(0, "exec")
        manager = ManagerClient("http://manager")
        
        exit_code = await execute_remote_command(engine, manager, "ls")
        self.assertEqual(exit_code, 1)

    @patch('migasfree_connect.manager.ManagerClient.select_agent', new_callable=AsyncMock)
    async def test_execute_remote_command_no_relay(self, mock_select):
        mock_select.return_value = {"id": "agent1", "name": "Agent 1"} # No relay
        from migasfree_connect.tunnel import TunnelEngine
        from migasfree_connect.manager import ManagerClient
        engine = TunnelEngine(0, "exec")
        manager = ManagerClient("http://manager")
        
        exit_code = await execute_remote_command(engine, manager, "ls")
        self.assertEqual(exit_code, 1)

if __name__ == '__main__':
    unittest.main()
