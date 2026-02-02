#!/bin/bash
# Setup SSH key for access from Mac

SSH_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEpfclCVpwZSTl/J0cRysSfEqrZduJ/pBx2PTTCajDcy eloy.disano@gmail.com"

# Create .ssh directory if not exists
mkdir -p /root/.ssh

# Add key to authorized_keys
echo "$SSH_KEY" >> /root/.ssh/authorized_keys

# Set correct permissions
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys

# Show what was done
echo "SSH key configured"
echo ""
echo "Keys in authorized_keys:"
cat /root/.ssh/authorized_keys
