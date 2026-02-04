import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

import unittest
import subprocess
from unittest.mock import patch, MagicMock

from migasfree_connect.utils import crypto as mfc

class TestExtractCN(unittest.TestCase):

    @patch('subprocess.run')
    def test_extract_cn_success_with_cn_equals(self, mock_run):
        # Mocking openssl output: subject=CN = agent-name, O = organization
        mock_run.return_value = MagicMock(
            stdout="subject=CN = agent-name, O = organization",
            returncode=0
        )
        
        with patch('os.path.exists', return_value=True):
            result = mfc.extract_cn_from_cert("fake_path.pem")
            self.assertEqual(result, "agent-name")

    @patch('subprocess.run')
    def test_extract_cn_success_simple_subject(self, mock_run):
        # Mocking openssl output: subject= agent-name
        mock_run.return_value = MagicMock(
            stdout="subject= agent-name",
            returncode=0
        )
        
        with patch('os.path.exists', return_value=True):
            result = mfc.extract_cn_from_cert("fake_path.pem")
            self.assertEqual(result, "agent-name")

    def test_extract_cn_file_not_found(self):
        result = mfc.extract_cn_from_cert("non_existent.pem")
        self.assertIsNone(result)

    @patch('subprocess.run')
    def test_extract_cn_subprocess_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'openssl')
        
        with patch('os.path.exists', return_value=True):
            result = mfc.extract_cn_from_cert("fake_path.pem")
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
