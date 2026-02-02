#!/bin/bash
mkdir -p /root/.ssh
touch /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys

echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEpfclCVpwZSTl/J0cRysSfEqrZduJ/pBx2PTTCajDcy eloy.disano@gmail.com" >> /root/.ssh/authorized_keys

echo "SSH key configured"
cat /root/.ssh/authorized_keys
