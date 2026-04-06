import getpass
import sys
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization.pkcs12 import load_pkcs12


def check_credentials(
    manager_url: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Checks for mTLS credentials or extracts them from a .p12 file."""
    try:
        parsed = urlparse(manager_url)
        fqdn = parsed.hostname or ''
    except ValueError:
        fqdn = ''

    if manager_url == 'https://':
        print('❌ Invalid Manager URL. Please provide a valid URL.')
        print('   Example: migasfree-connect -a CID-4 -t ssh -m https://<FQDN> <user>')
        sys.exit(1)

    home = Path.home()
    cert_dir = home / '.migasfree-connect' / fqdn
    cert_dir.mkdir(parents=True, exist_ok=True)

    cert_file = cert_dir / 'cert.pem'
    key_file = cert_dir / 'key.pem'
    ca_file = cert_dir / 'ca.pem'

    if cert_file.exists() and key_file.exists():
        return str(cert_file), str(key_file), str(ca_file) if ca_file.exists() else None

    print('\n🔐 mTLS Credentials missing. Please provide a .p12 certificate (e.g., admin.p12)')

    while True:
        p12_path = input('👉 Path to .p12 file: ').strip()
        p12_file = Path(p12_path)
        if p12_file.exists() and p12_file.is_file():
            break
        print('❌ File not found. Try again.')

    password = getpass.getpass('👉 .p12 Password: ')

    print('⚙️ Extracting certificates...')

    try:
        p12_data = p12_file.read_bytes()
        p12 = load_pkcs12(p12_data, password.encode())

        # Extract client certificate
        if p12.cert:
            cert_pem = p12.cert.certificate.public_bytes(serialization.Encoding.PEM)
            cert_file.write_bytes(cert_pem)

        # Extract private key
        if p12.key:
            key_pem = p12.key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
            key_file.write_bytes(key_pem)

        # Extract CA certificates (optional)
        if p12.additional_certs:
            ca_pem = b''.join(
                c.certificate.public_bytes(serialization.Encoding.PEM)
                for c in p12.additional_certs
            )
            ca_file.write_bytes(ca_pem)

        print(f'✅ Credentials extracted to {cert_dir}')
        ca_result = str(ca_file) if ca_file.exists() and ca_file.stat().st_size > 0 else None
        return str(cert_file), str(key_file), ca_result

    except (ValueError, TypeError) as e:
        print(f'❌ Error extracting certificates. Wrong password or invalid P12 file?\n{e}')
        sys.exit(1)
