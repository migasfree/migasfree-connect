import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path (required before project imports)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from migasfree_connect.auth import check_credentials  # noqa: E402


class TestAuthCredentials(unittest.TestCase):
    def test_check_credentials_existing(self):
        with patch('migasfree_connect.auth.Path.exists', return_value=True), patch('migasfree_connect.auth.Path.mkdir'):
            cert, key, _ca = check_credentials('https://manager.example.com')
            self.assertTrue(str(cert).endswith('cert.pem'))
            self.assertTrue(str(key).endswith('key.pem'))

    def test_check_credentials_extraction(self):
        """Test full P12 extraction flow using cryptography library mocks."""
        # Build a realistic P12 mock
        mock_cert = MagicMock()
        mock_cert.certificate.public_bytes.return_value = b'CERT_PEM'

        mock_key = MagicMock()
        mock_key.private_bytes.return_value = b'KEY_PEM'

        mock_ca = MagicMock()
        mock_ca.certificate.public_bytes.return_value = b'CA_PEM'

        mock_p12 = MagicMock()
        mock_p12.cert = mock_cert
        mock_p12.key = mock_key
        mock_p12.additional_certs = [mock_ca]

        with patch('migasfree_connect.auth.load_pkcs12', return_value=mock_p12) as mock_load, patch(
            'migasfree_connect.auth.getpass.getpass', return_value='password'
        ), patch('migasfree_connect.auth.input', return_value='admin.p12'), patch(
            'migasfree_connect.auth.Path.exists'
        ) as mock_exists, patch('migasfree_connect.auth.Path.is_file', return_value=True), patch(
            'migasfree_connect.auth.Path.mkdir'
        ), patch('migasfree_connect.auth.Path.read_bytes', return_value=b'P12_DATA'), patch(
            'migasfree_connect.auth.Path.write_bytes'
        ), patch('migasfree_connect.auth.Path.stat') as mock_stat:
            exists_calls = []

            def exists_side_effect(*args):
                exists_calls.append(True)
                # cert.pem and key.pem don't exist yet → trigger extraction
                return not len(exists_calls) <= 2

            mock_exists.side_effect = exists_side_effect
            mock_stat.return_value.st_size = 100

            with patch('migasfree_connect.auth.Path.home', return_value=Path('/tmp/home')):
                cert, key, _ca = check_credentials('https://manager.example.com')

            mock_load.assert_called_once_with(b'P12_DATA', b'password')
            self.assertTrue(str(cert).endswith('cert.pem'))
            self.assertTrue(str(key).endswith('key.pem'))

    def test_check_credentials_wrong_password(self):
        """Test that wrong password causes sys.exit."""
        from cryptography.exceptions import InvalidKey  # noqa: F401

        with patch('migasfree_connect.auth.load_pkcs12', side_effect=ValueError('MAC check failed')), patch(
            'migasfree_connect.auth.getpass.getpass', return_value='wrong'
        ), patch('migasfree_connect.auth.input', return_value='admin.p12'), patch(
            'migasfree_connect.auth.Path.exists'
        ) as mock_exists, patch('migasfree_connect.auth.Path.is_file', return_value=True), patch(
            'migasfree_connect.auth.Path.mkdir'
        ), patch('migasfree_connect.auth.Path.read_bytes', return_value=b'P12_DATA'), patch(
            'migasfree_connect.auth.sys.exit'
        ) as mock_exit:
            mock_exists.side_effect = [False, True]
            mock_exit.side_effect = SystemExit

            with patch('migasfree_connect.auth.Path.home', return_value=Path('/tmp/home')), self.assertRaises(SystemExit):
                check_credentials('https://manager.example.com')

            mock_exit.assert_called_once_with(1)

    def test_check_credentials_invalid_url(self):
        """Test that an empty manager URL calls sys.exit."""
        with patch('migasfree_connect.auth.sys.exit', side_effect=SystemExit) as mock_exit, patch('migasfree_connect.auth.Path.mkdir'), self.assertRaises(SystemExit):
            check_credentials('https://')
            mock_exit.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()
