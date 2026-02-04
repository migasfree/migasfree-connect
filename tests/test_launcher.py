
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from migasfree_connect.launcher import execute_client

class TestLauncher(unittest.TestCase):

    @patch('subprocess.Popen')
    def test_execute_client_ssh(self, mock_popen):
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        exit_code = execute_client("ssh", 1234, user="tux")
        
        self.assertEqual(exit_code, 0)
        args, _ = mock_popen.call_args
        cmd = args[0]
        self.assertIn("ssh", cmd)
        self.assertIn("1234", cmd)
        self.assertIn("tux@127.0.0.1", cmd)

    @patch('subprocess.Popen')
    def test_execute_client_vnc(self, mock_popen):
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        exit_code = execute_client("vnc", 5901)
        
        self.assertEqual(exit_code, 0)
        args, _ = mock_popen.call_args
        cmd = args[0]
        self.assertIn("vncviewer", cmd)
        self.assertIn("localhost:5901", cmd)

    @patch('subprocess.Popen')
    def test_execute_client_rdp(self, mock_popen):
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        exit_code = execute_client("rdp", 3389, user="tux")
        
        self.assertEqual(exit_code, 0)
        args, _ = mock_popen.call_args
        cmd = args[0]
        # On Linux it should use xfreerdp
        self.assertIn("xfreerdp", cmd)

    @patch('time.sleep', side_effect=KeyboardInterrupt)
    def test_execute_client_unknown_service(self, mock_sleep):
        # Should enter the while True loop and break on KeyboardInterrupt
        exit_code = execute_client("unknown", 9999)
        self.assertEqual(exit_code, 0)

    def test_execute_client_ssh_no_user(self):
        exit_code = execute_client("ssh", 1234)
        self.assertEqual(exit_code, 1)

if __name__ == '__main__':
    unittest.main()
