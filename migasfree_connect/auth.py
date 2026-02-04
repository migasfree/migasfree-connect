
import getpass
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from urllib.parse import urlparse

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

    cmd_cert = ['openssl', 'pkcs12', '-in', str(p12_file), '-clcerts', '-nokeys', '-out', str(cert_file), '-passin', 'stdin']
    cmd_key = ['openssl', 'pkcs12', '-in', str(p12_file), '-nocerts', '-out', str(key_file), '-nodes', '-passin', 'stdin']
    cmd_ca = ['openssl', 'pkcs12', '-in', str(p12_file), '-cacerts', '-nokeys', '-out', str(ca_file), '-passin', 'stdin']

    try:
        subprocess.run(cmd_cert, input=password, text=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(cmd_key, input=password, text=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(cmd_ca, input=password, text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print(f'✅ Credentials extracted to {cert_dir}')
        ca_result = str(ca_file) if ca_file.exists() and ca_file.stat().st_size > 0 else None
        return str(cert_file), str(key_file), ca_result

    except subprocess.CalledProcessError as e:
        print(f'❌ Error extracting certificates. Wrong password?\n{e}')
        sys.exit(1)
