#!/bin/bash
# install-nginx-certbot.sh
# Run this script on your EC2 instance to install Nginx and Certbot.
# Usage: sudo bash install-nginx-certbot.sh

set -e  # Exit immediately if any command fails

echo "==> Updating apt package list..."
apt update

echo "==> Installing Nginx..."
apt install -y nginx

echo "==> Installing Certbot and the Nginx plugin..."
apt install -y certbot python3-certbot-nginx

echo "==> Creating webroot directory for Certbot challenges..."
mkdir -p /var/www/certbot

echo "==> Enabling Nginx to start on boot..."
systemctl enable nginx

echo "==> Starting Nginx..."
systemctl start nginx

echo "==> Checking if UFW firewall is active..."
if ufw status | grep -q "Status: active"; then
    echo "==> UFW is active. Allowing HTTP (80) and HTTPS (443)..."
    ufw allow 'Nginx Full'
else
    echo "==> UFW is not active. Skipping firewall configuration."
    echo "    (Make sure your EC2 Security Group allows ports 80 and 443.)"
fi

echo ""
echo "==> Done! Nginx and Certbot are installed."
echo "    Nginx status:"
systemctl status nginx --no-pager -l
