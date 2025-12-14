# Migasfree Connect

Client for migasfree remote tunnel sessions. This tool allows you to connect to remote agents via SSH, VNC, or RDP using the Migasfree tunnel infrastructure.

## Requirements

- Python 3
- `python3-websockets`
- `python3-requests`
- `openssl`
- **Clients**:
    - SSH: `openssh-client`
    - VNC: `xtightvncviewer` (or similar)
    - RDP: `freerdp2-x11` (xfreerdp)

## Installation

### From Package (DEB)
```bash
sudo dpkg -i migasfree-connect_*.deb
sudo apt-get install -f  # To install dependencies
```

### Manual
Running directly from source:
```bash
migasfree-connect --help
```

## Setup

First time you run the tool, it will ask for a **Client Certificate** (.p12) to authenticate with the Migasfree Manager. Valid mTLS credentials (admin certificate) are required.

## Usage

```bash
migasfree-connect [USER] [OPTIONS]
```

### Examples

**SSH Connection:**
Connect to an agent via SSH.
```bash
migasfree-connect -t ssh -a CID-4 -m https://<FQDN> root
```

**Execute Remote Command (SSH):**
```bash
migasfree-connect -t ssh -a CID-4 -m https://<FQDN> root -c "ls -la"
```

**VNC Connection:**
Connect to the remote graphical desktop via VNC.
```bash
migasfree-connect -t vnc -a CID-4 -m https://<FQDN>
```

**RDP Connection:**
Connect via Remote Desktop Protocol (Windows).
```bash
migasfree-connect -t rdp -a CID-4 -m https://<FQDN> tux
```

### Options

- `user`: Remote username (required for SSH/RDP).
- `-t, --type {ssh,vnc,rdp}`: Service type to connect to (default: ssh).
- `-a, --agent AGENT_ID`: Connect to a specific agent by ID.
- `-m, --manager URL`: Migasfree Manager URL
- `-p, --port PORT`: Local port to bind the tunnel (0 = random).
- `-c, --command CMD`: Command to execute remotely (SSH only).

## Troubleshooting

- **Certificate Error**: Ensure your `.p12` file is valid and you have the correct password.
- **Connection Refused**: Check if the agent has the selected service (SSH/VNC/RDP) enabled and running.
- **No Agents**: Ensure you are connected to the correct Manager URL (`-m`).
