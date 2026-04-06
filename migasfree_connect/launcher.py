import subprocess
import sys
import time
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, List, Optional, Type


class BaseLauncher(ABC):
    """Abstract base for all protocol launchers."""

    def __init__(self, local_port: int, user: Optional[str] = None, extra_command: Optional[List[str]] = None) -> None:
        self.local_port = local_port
        self.user = user
        self.extra_command = extra_command
        self.is_windows = sys.platform == 'win32'

    @abstractmethod
    def build_command(self) -> Optional[List[str]]:
        """Returns the command list to execute, or None if no command needed."""

    @abstractmethod
    def install_hint(self) -> str:
        """Returns a help string for when the client binary is not found."""

    def label(self) -> str:
        return self.__class__.__name__.replace('Launcher', '').upper()


class SshLauncher(BaseLauncher):
    def build_command(self) -> Optional[List[str]]:
        if not self.user:
            print('❌ User required for SSH')
            return None
        cmd = [
            'ssh',
            '-p',
            str(self.local_port),
            '-o',
            'StrictHostKeyChecking=no',
            '-o',
            'UserKnownHostsFile=/dev/null',
            '-o',
            'LogLevel=ERROR',
            '-o',
            'ServerAliveInterval=30',
            '-o',
            'ServerAliveCountMax=3',
            '-o',
            'TCPKeepAlive=yes',
            '-o',
            'NoHostAuthenticationForLocalhost=yes',
            '-o',
            'CheckHostIP=no',
            f'{self.user}@127.0.0.1',
        ]
        if self.extra_command:
            cmd.extend(self.extra_command)
        print('\n🚀 Connecting SSH...')
        return cmd

    def install_hint(self) -> str:
        return '   👉 Install OpenSSH' if self.is_windows else '   👉 Install: sudo apt install openssh-client'


class VncLauncher(BaseLauncher):
    def build_command(self) -> Optional[List[str]]:
        print('\n🖥️  Connecting VNC...')
        return ['vncviewer', f'localhost:{self.local_port}']

    def install_hint(self) -> str:
        return '   👉 Install a VNC viewer' if self.is_windows else '   👉 Install: sudo apt install xtightvncviewer'


class RdpLauncher(BaseLauncher):
    def build_command(self) -> Optional[List[str]]:
        print('\n🖥️  Connecting RDP...')
        if self.is_windows:
            return ['mstsc', f'/v:localhost:{self.local_port}']
        cmd = ['xfreerdp', f'/v:localhost:{self.local_port}', '/cert-ignore', '/clipboard', '/sound']
        if self.user:
            cmd.append(f'/u:{self.user}')
        return cmd

    def install_hint(self) -> str:
        return (
            '   👉 mstsc.exe should be available' if self.is_windows else '   👉 Install: sudo apt install freerdp2-x11'
        )


class FallbackLauncher(BaseLauncher):
    """Used when no specific launcher is registered for a service."""

    def build_command(self) -> Optional[List[str]]:
        print('⚠️  Service has no predefined client')
        print(f'   Tunnel available at localhost:{self.local_port}')
        print('   Press Ctrl+C to close...')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return None

    def install_hint(self) -> str:
        return ''


class LauncherFactory:
    """Factory that registers and resolves protocol launchers."""

    _registry: ClassVar[Dict[str, Type[BaseLauncher]]] = {
        'ssh': SshLauncher,
        'vnc': VncLauncher,
        'rdp': RdpLauncher,
    }

    @classmethod
    def register(cls, service: str, launcher_cls: Type[BaseLauncher]) -> None:
        """Register a new protocol launcher."""
        cls._registry[service] = launcher_cls

    @classmethod
    def resolve(
        cls,
        service: str,
        local_port: int,
        user: Optional[str] = None,
        extra_command: Optional[List[str]] = None,
    ) -> BaseLauncher:
        """Return the appropriate launcher instance for the given service."""
        launcher_cls = cls._registry.get(service, FallbackLauncher)
        return launcher_cls(local_port, user, extra_command)


def execute_client(
    service: str,
    local_port: int,
    user: Optional[str] = None,
    extra_command: Optional[List[str]] = None,
) -> int:
    """Executes the appropriate client according to the service and platform."""
    launcher = LauncherFactory.resolve(service, local_port, user, extra_command)
    cmd = launcher.build_command()

    if cmd is None:
        # FallbackLauncher or validation failure (e.g. SSH without user)
        return 0 if service not in LauncherFactory._registry else 1

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
        print(launcher.install_hint())
        return 1
