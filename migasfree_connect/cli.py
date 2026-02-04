
import asyncio
import argparse
import sys
import logging
import uuid
import json
import websockets
from typing import Optional, List

from .auth import check_credentials
from .manager import ManagerClient
from .tunnel import TunnelEngine, WEBSOCKET_CONFIG
from .launcher import execute_client

# Try migasfree-client integration
try:
    from migasfree_client import settings
    from migasfree_client.utils import get_config
    FQDN = get_config(settings.CONF_FILE, 'client').get('server', '')
except ImportError:
    FQDN = ''

async def execute_remote_command(engine: TunnelEngine, manager: ManagerClient, command: str) -> int:
    """Executes a command on the remote agent directly via WebSocket."""
    print('=' * 70)
    print('🔧 Remote Command Execution')
    print('=' * 70)

    agent = await manager.select_agent()
    if not agent:
        return 1

    relay_url = agent.get('relay')
    if not relay_url:
        print('❌ Agent has no registered Relay URL')
        return 1

    exec_id = f'exec-{uuid.uuid4()}'
    print(f'✅ Target: {agent["name"]}')
    print(f'✅ Command: {command}')
    print()

    connect_kwargs = WEBSOCKET_CONFIG.copy()
    ssl_ctx = engine._get_ssl_context()
    if ssl_ctx:
        connect_kwargs['ssl'] = ssl_ctx

    try:
        async with websockets.connect(relay_url, **connect_kwargs) as ws:
            await ws.send(json.dumps({'type': 'connect_client', 'mode': 'exec'}))
            await ws.recv()

            await ws.send(json.dumps({
                'type': 'execute_command',
                'id': agent['id'],
                'exec_id': exec_id,
                'command': command,
                'client_cn': engine.client_cn,
            }))

            resp = await ws.recv()
            resp_data = json.loads(resp)
            if resp_data.get('type') != 'exec_started':
                print(f"❌ Error: {resp_data.get('error', 'Unexpected response')}")
                return 1

            print('✅ Execution started\n' + '-' * 70)
            exit_code = None
            async for message_raw in ws:
                message = json.loads(message_raw)
                msg_type = message.get('type')
                if msg_type == 'exec_output':
                    print(message.get('data', ''), end='', flush=True)
                elif msg_type == 'exec_complete':
                    exit_code = message.get('exit_code', 0)
                    break
                elif msg_type == 'exec_error':
                    print(f'\n❌ Execution error: {message.get("error")}')
                    return 1
            
            print('\n' + '-' * 70)
            return exit_code if exit_code is not None else 1
    except Exception as e:
        print(f'❌ Error: {e}')
        return 1

async def run_cli():
    parser = argparse.ArgumentParser(description='Migasfree Connect - Multi-protocol Tunnel Client')
    parser.add_argument('user', nargs='?', help='User for SSH/RDP')
    parser.add_argument('-t', '--type', default='ssh', choices=['ssh', 'vnc', 'rdp', 'exec'], help='Service type')
    parser.add_argument('-a', '--agent', help='Agent ID (CID)')
    parser.add_argument('-m', '--manager', default=f'https://{FQDN}' if FQDN else 'https://', help='Manager URL')
    parser.add_argument('-p', '--port', type=int, default=0, help='Local port')
    parser.add_argument('-c', '--command', help='Remote command (SSH only)')
    parser.add_argument('-e', '--exec-command', help='Remote command (exec mode)')
    
    args = parser.parse_args()
    
    if args.type == 'ssh' and not args.user:
        parser.error('User required for SSH')
    if args.type == 'exec' and not args.exec_command:
        parser.error('Exec command required (-e)')

    # 1. Credentials
    cert, key, ca = check_credentials(args.manager)
    
    # 2. Engines
    manager = ManagerClient(args.manager, cert, key, ca)
    engine = TunnelEngine(args.port, args.type, cert, key, ca)

    if args.type == 'exec':
        return await execute_remote_command(engine, manager, args.exec_command)

    # 3. Connect Flow
    print('=' * 70)
    print(f'🔐 Tunnel {args.type.upper()} over WebSocket')
    print('=' * 70)

    agent = await manager.select_agent(args.agent)
    if not agent:
        return 1

    try:
        await engine.start(agent)
        await asyncio.sleep(0.5)
        
        loop = asyncio.get_event_loop()
        exit_code = await loop.run_in_executor(
            None, execute_client, args.type, engine.local_port, args.user, [args.command] if args.command else None
        )
        
        print(f'\n✅ Session {args.type.upper()} finished')
        return exit_code
    finally:
        await engine.stop()

def main():
    try:
        sys.exit(asyncio.run(run_cli()))
    except KeyboardInterrupt:
        print('\n\n✅ Cancelled by user')
        sys.exit(130)
