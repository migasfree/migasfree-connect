
import sys
import os
import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from migasfree_connect.auth import check_credentials

class TestAuthCredentials(unittest.TestCase):

    def test_check_credentials_existing(self):
        with patch('migasfree_connect.auth.Path.exists', return_value=True), \
             patch('migasfree_connect.auth.Path.mkdir'):
            
            cert, key, ca = check_credentials("https://manager.example.com")
            self.assertTrue(str(cert).endswith("cert.pem"))
            self.assertTrue(str(key).endswith("key.pem"))

    def test_check_credentials_extraction(self):
        # We patch everything needed
        with patch('migasfree_connect.auth.subprocess.run') as mock_run, \
             patch('migasfree_connect.auth.getpass.getpass', return_value="password"), \
             patch('migasfree_connect.auth.input', return_value="admin.p12"), \
             patch('migasfree_connect.auth.Path.exists') as mock_exists, \
             patch('migasfree_connect.auth.Path.is_file', return_value=True), \
             patch('migasfree_connect.auth.Path.mkdir'), \
             patch('migasfree_connect.auth.Path.stat') as mock_stat, \
             patch('migasfree_connect.auth.sys.exit') as mock_exit:
            
            # Side effect for exists
            exists_calls = []
            def exists_side_effect(*args):
                exists_calls.append(True)
                # 1: cert.pem, 2: key.pem -> False
                if len(exists_calls) <= 2:
                    return False
                return True
            
            mock_exists.side_effect = exists_side_effect
            mock_stat.return_value.st_size = 100
            
            # We must also mock Path.home() so we don't touch the real home
            with patch('migasfree_connect.auth.Path.home', return_value=Path("/tmp/home")):
                cert, key, ca = check_credentials("https://manager.example.com")
            
            self.assertEqual(mock_run.call_count, 3)
            mock_exit.assert_not_called()

if __name__ == '__main__':
    unittest.main()
