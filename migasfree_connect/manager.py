
import asyncio
import logging
import requests
from typing import Optional, Union, Tuple, List

logger = logging.getLogger(__name__)
CONNECTION_TIMEOUT = 5

class ManagerClient:
    def __init__(self, manager_url: str, cert: Optional[str] = None, key: Optional[str] = None, ca: Optional[str] = None):
        self.manager_url = manager_url.rstrip('/')
        self.cert = cert
        self.key = key
        self.ca = ca

    def _get_agents_request(self, verify: Union[str, bool], cert: Optional[Tuple[str, str]]) -> requests.Response:
        """Performs the synchronous request to get agents."""
        return requests.get(
            f'{self.manager_url}/manager/v1/private/tunnel/agents',
            timeout=CONNECTION_TIMEOUT,
            verify=verify,
            cert=cert,
        )

    async def get_agents(self) -> List[dict]:
        """Queries the Manager for available agents."""
        try:
            verify_param = self.ca if self.ca else False
            cert_param = (self.cert, self.key) if self.cert and self.key else None

            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                self._get_agents_request,
                verify_param,
                cert_param,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get('agents', [])
        except requests.RequestException as e:
            logger.error(f"Error contacting Manager: {e}")
            return []

    async def select_agent(self, target_agent_id: Optional[str] = None) -> Optional[dict]:
        """Interactive or direct agent selection."""
        print(f'📋 Querying Manager at {self.manager_url}')
        agents = await self.get_agents()

        if not agents:
            print('❌ No agents available')
            return None

        # Direct selection
        if target_agent_id:
            target = target_agent_id.replace('CID-', '')
            for agent in agents:
                agent_id = str(agent['id'])
                if target == agent_id or target_agent_id == agent_id:
                    print(f'\n✅ Agent selected: {agent["name"]}')
                    return agent
            print(f'❌ Agent {target_agent_id} not found')
            return None

        # Auto-selection if only one
        if len(agents) == 1:
            agent = agents[0]
            print(f'\n✅ Using: {agent["name"]}')
            return agent

        # Manual selection
        print(f'\n📊 Available Agents ({len(agents)}):')
        for idx, agent in enumerate(agents, 1):
            services = agent.get('services', [])
            services_str = f' [{", ".join(services)}]' if services else ''
            print(f'   [{idx}] {agent["name"]}{services_str}')
            print(f'       ID: {agent["id"][:24]}...')

        while True:
            try:
                selection = input(f'\n👉 Select an agent [1-{len(agents)}]: ').strip()
                idx = int(selection) - 1
                if 0 <= idx < len(agents):
                    agent = agents[idx]
                    print(f'✅ Selected: {agent["name"]}')
                    return agent
                print('❌ Invalid number')
            except (ValueError, KeyboardInterrupt):
                print('\n❌ Cancelled or invalid input')
                return None
