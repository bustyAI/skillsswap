#!/bin/bash
# obtain-cert.sh
# Run this script on your EC2 instance AFTER:
#   1. DNS is pointing to this server
#   2. Nginx is installed and running with skillswap.conf
#
# Usage: sudo bash obtain-cert.sh your-email@example.com

set -e  # Exit immediately if any command fails

EMAIL="$1"

if [ -z "$EMAIL" ]; then
    echo "Error: Please provide your email address."
    echo "Usage: sudo bash obtain-cert.sh your-email@example.com"
    echo ""
    echo "The email is used by Let's Encrypt to send expiry warnings"
    echo "(rarely needed since auto-renewal handles it)."
    exit 1
fi

echo "==> Requesting certificate for skillsswap.xyz and www.skillsswap.xyz..."
echo "    Email for notifications: $EMAIL"
echo ""

certbot --nginx \
    -d skillsswap.xyz \
    -d www.skillsswap.xyz \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --redirect

echo ""
echo "==> Certificate obtained successfully!"
echo ""
echo "==> Verifying Nginx configuration..."
nginx -t

echo ""
echo "==> Reloading Nginx with new HTTPS configuration..."
systemctl reload nginx

echo ""
echo "==> Checking auto-renewal timer..."
systemctl status certbot.timer --no-pager

echo ""
echo "==> Done! Your site should now be accessible via HTTPS."
echo "    Test it: https://skillsswap.xyz"
echo ""
echo "    Certificate files are stored in:"
echo "      /etc/letsencrypt/live/skillsswap.xyz/"
echo ""
echo "    Auto-renewal is handled by the certbot.timer systemd service."
echo "    You can test renewal with: sudo certbot renew --dry-run"
