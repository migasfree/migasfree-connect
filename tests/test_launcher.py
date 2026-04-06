import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path (required before project imports)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from migasfree_connect.launcher import (  # noqa: E402
    FallbackLauncher,
    LauncherFactory,
    RdpLauncher,
    SshLauncher,
    VncLauncher,
    execute_client,
)


class TestSshLauncher(unittest.TestCase):

    def test_build_command_returns_valid_cmd(self):
        launcher = SshLauncher(1234, user='tux')
        cmd = launcher.build_command()
        self.assertIsNotNone(cmd)
        self.assertIn('ssh', cmd)
        self.assertIn('1234', cmd)
        self.assertIn('tux@127.0.0.1', cmd)

    def test_build_command_with_extra_command(self):
        launcher = SshLauncher(1234, user='tux', extra_command=['ls', '-la'])
        cmd = launcher.build_command()
        self.assertIn('ls', cmd)
        self.assertIn('-la', cmd)

    def test_build_command_no_user_returns_none(self):
        launcher = SshLauncher(1234)
        cmd = launcher.build_command()
        self.assertIsNone(cmd)

    def test_install_hint_linux(self):
        with patch('sys.platform', 'linux'):
            launcher = SshLauncher(1234, user='tux')
            launcher.is_windows = False
            self.assertIn('apt', launcher.install_hint())

    def test_install_hint_windows(self):
        launcher = SshLauncher(1234, user='tux')
        launcher.is_windows = True
        self.assertIn('OpenSSH', launcher.install_hint())


class TestVncLauncher(unittest.TestCase):

    def test_build_command(self):
        launcher = VncLauncher(5901)
        cmd = launcher.build_command()
        self.assertIsNotNone(cmd)
        self.assertIn('vncviewer', cmd)
        self.assertIn('localhost:5901', cmd)

    def test_install_hint_linux(self):
        launcher = VncLauncher(5901)
        launcher.is_windows = False
        self.assertIn('xtightvncviewer', launcher.install_hint())


class TestRdpLauncher(unittest.TestCase):

    def test_build_command_linux(self):
        launcher = RdpLauncher(3389, user='tux')
        launcher.is_windows = False
        cmd = launcher.build_command()
        self.assertIsNotNone(cmd)
        self.assertIn('xfreerdp', cmd)
        self.assertIn('/u:tux', cmd)

    def test_build_command_windows(self):
        launcher = RdpLauncher(3389)
        launcher.is_windows = True
        cmd = launcher.build_command()
        self.assertIsNotNone(cmd)
        self.assertIn('mstsc', cmd)

    def test_install_hint_linux(self):
        launcher = RdpLauncher(3389)
        launcher.is_windows = False
        self.assertIn('freerdp2', launcher.install_hint())


class TestFallbackLauncher(unittest.TestCase):

    @patch('time.sleep', side_effect=KeyboardInterrupt)
    def test_build_command_returns_none(self, _mock_sleep):
        launcher = FallbackLauncher(9999)
        result = launcher.build_command()
        self.assertIsNone(result)

    def test_install_hint_empty(self):
        launcher = FallbackLauncher(9999)
        self.assertEqual(launcher.install_hint(), '')


class TestLauncherFactory(unittest.TestCase):

    def test_resolve_ssh_returns_ssh_launcher(self):
        launcher = LauncherFactory.resolve('ssh', 22, user='tux')
        self.assertIsInstance(launcher, SshLauncher)

    def test_resolve_vnc_returns_vnc_launcher(self):
        launcher = LauncherFactory.resolve('vnc', 5901)
        self.assertIsInstance(launcher, VncLauncher)

    def test_resolve_rdp_returns_rdp_launcher(self):
        launcher = LauncherFactory.resolve('rdp', 3389)
        self.assertIsInstance(launcher, RdpLauncher)

    def test_resolve_unknown_returns_fallback(self):
        launcher = LauncherFactory.resolve('ftp', 21)
        self.assertIsInstance(launcher, FallbackLauncher)

    def test_register_custom_launcher(self):
        class CustomLauncher(FallbackLauncher):
            pass

        LauncherFactory.register('custom', CustomLauncher)
        launcher = LauncherFactory.resolve('custom', 1234)
        self.assertIsInstance(launcher, CustomLauncher)
        # Cleanup
        del LauncherFactory._registry['custom']


class TestExecuteClient(unittest.TestCase):

    @patch('subprocess.Popen')
    def test_execute_client_ssh(self, mock_popen):
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        exit_code = execute_client('ssh', 1234, user='tux')

        self.assertEqual(exit_code, 0)
        args, _ = mock_popen.call_args
        cmd = args[0]
        self.assertIn('ssh', cmd)
        self.assertIn('tux@127.0.0.1', cmd)

    @patch('subprocess.Popen')
    def test_execute_client_vnc(self, mock_popen):
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        exit_code = execute_client('vnc', 5901)
        self.assertEqual(exit_code, 0)

    @patch('subprocess.Popen')
    def test_execute_client_rdp(self, mock_popen):
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        exit_code = execute_client('rdp', 3389, user='tux')
        self.assertEqual(exit_code, 0)

    def test_execute_client_ssh_no_user_returns_1(self):
        exit_code = execute_client('ssh', 1234)
        self.assertEqual(exit_code, 1)

    @patch('time.sleep', side_effect=KeyboardInterrupt)
    def test_execute_client_unknown_service_returns_0(self, _mock_sleep):
        exit_code = execute_client('unknown', 9999)
        self.assertEqual(exit_code, 0)

    @patch('subprocess.Popen', side_effect=FileNotFoundError)
    def test_execute_client_binary_not_found(self, _mock_popen):
        exit_code = execute_client('vnc', 5901)
        self.assertEqual(exit_code, 1)


if __name__ == '__main__':
    unittest.main()
