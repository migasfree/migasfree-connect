
import sys
import os
import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from migasfree_connect.manager import ManagerClient

class TestManagerClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager_url = "https://manager.example.com"
        self.client = ManagerClient(self.manager_url)

    @patch('requests.get')
    async def test_get_agents_success(self, mock_get):
        # Mock successful response
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "agents": [
                {"id": "1", "name": "Agent 1", "services": ["ssh"]},
                {"id": "2", "name": "Agent 2", "services": ["vnc"]}
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        agents = await self.client.get_agents()
        
        self.assertEqual(len(agents), 2)
        self.assertEqual(agents[0]["name"], "Agent 1")
        mock_get.assert_called_once()

    @patch('requests.get')
    async def test_get_agents_failure(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Connection error")

        agents = await self.client.get_agents()
        
        self.assertEqual(agents, [])

    @patch('migasfree_connect.manager.ManagerClient.get_agents', new_callable=AsyncMock)
    async def test_select_agent_direct(self, mock_get_agents):
        mock_get_agents.return_value = [
            {"id": "cid-123", "name": "Test Agent"}
        ]
        
        agent = await self.client.select_agent("cid-123")
        self.assertEqual(agent["name"], "Test Agent")

    @patch('migasfree_connect.manager.ManagerClient.get_agents', new_callable=AsyncMock)
    async def test_select_agent_auto_single(self, mock_get_agents):
        mock_get_agents.return_value = [
            {"id": "1", "name": "Only Agent"}
        ]
        
        agent = await self.client.select_agent()
        self.assertEqual(agent["name"], "Only Agent")

    @patch('builtins.input', return_value="2")
    @patch('migasfree_connect.manager.ManagerClient.get_agents', new_callable=AsyncMock)
    async def test_select_agent_manual(self, mock_get_agents, mock_input):
        mock_get_agents.return_value = [
            {"id": "1", "name": "Agent 1"},
            {"id": "2", "name": "Agent 2"}
        ]
        
        agent = await self.client.select_agent()
        self.assertEqual(agent["name"], "Agent 2")

if __name__ == '__main__':
    unittest.main()
