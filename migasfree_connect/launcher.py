
import subprocess
import sys
from typing import List, Optional

def execute_client(service: str, local_port: int, user: Optional[str] = None, extra_command: Optional[List[str]] = None) -> int:
    """Executes the appropriate client according to the service and platform."""
    is_windows = sys.platform == 'win32'
    cmd = []

    if service == 'ssh':
        if not user:
            print('❌ User required for SSH')
            return 1

        cmd = [
            'ssh', '-p', str(local_port),
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'LogLevel=ERROR',
            '-o', 'ServerAliveInterval=30',
            '-o', 'ServerAliveCountMax=3',
            '-o', 'TCPKeepAlive=yes',
            '-o', 'NoHostAuthenticationForLocalhost=yes',
            '-o', 'CheckHostIP=no',
            f'{user}@127.0.0.1'
        ]
        if extra_command:
            cmd.extend(extra_command)
        print('\n🚀 Connecting SSH...')

    elif service == 'vnc':
        cmd = ['vncviewer', f'localhost:{local_port}']
        print('\n🖥️  Connecting VNC...')

    elif service == 'rdp':
        if is_windows:
            cmd = ['mstsc', f'/v:localhost:{local_port}']
        else:
            cmd = ['xfreerdp', f'/v:localhost:{local_port}', '/cert-ignore', '/clipboard', '/sound']
            if user:
                cmd.append(f'/u:{user}')
        print('\n🖥️  Connecting RDP...')

    else:
        print(f'⚠️  Service "{service}" has no predefined client')
        print(f'   Tunnel available at localhost:{local_port}')
        print('   Press Ctrl+C to close...')
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return 0
        return 0

    print(f'   Command: {" ".join(cmd)}\n')
    print('=' * 70)

    try:
        process = subprocess.Popen(cmd)
        return process.wait()
    except KeyboardInterrupt:
        print('\n⚠️  Connection interrupted by user')
        process.terminate()
        return 1
    except FileNotFoundError:
        print(f'❌ Client {service.upper()} not found')
        _print_install_help(service, is_windows)
        return 1

def _print_install_help(service: str, is_windows: bool):
    if service == 'ssh':
        print('   👉 Install OpenSSH' if is_windows else '   👉 Install: sudo apt install openssh-client')
    elif service == 'vnc':
        print('   👉 Install a VNC viewer' if is_windows else '   👉 Install: sudo apt install xtightvncviewer')
    elif service == 'rdp':
        print('   👉 mstsc.exe should be available' if is_windows else '   👉 Install: sudo apt install freerdp2-x11')
