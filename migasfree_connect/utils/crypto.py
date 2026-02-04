
import os
import re
import subprocess
from typing import Optional

def extract_cn_from_cert(cert_path: str) -> Optional[str]:
    """Extracts the Common Name (CN) from the certificate."""
    if not cert_path or not os.path.exists(cert_path):
        return None
    try:
        cmd = ['openssl', 'x509', '-in', cert_path, '-noout', '-subject']
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=True,
        )
        subject = result.stdout.strip()

        match = re.search(r'CN\s*=\s*([^/,]+)', subject)
        if match:
            return match.group(1).strip()

        if subject.startswith('subject='):
            return subject[8:].strip()
        return subject
    except (subprocess.CalledProcessError, OSError):
        return None
