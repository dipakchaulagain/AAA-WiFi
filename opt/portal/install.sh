#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: Must run as root." >&2
  exit 1
fi

if ! grep -qi "Ubuntu 22.04" /etc/os-release; then
  echo "ERROR: This installer supports Ubuntu 22.04 only." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y \
  freeradius freeradius-mysql freeradius-ldap freeradius-utils \
  mariadb-server nginx python3 python3-pip python3-venv \
  nodejs npm ufw easy-rsa openssl

install -d -m 0755 /opt/portal

# If running from a repo checkout, sync contents to /opt/portal
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rsync -a --delete "${SCRIPT_DIR}/" /opt/portal/ --exclude ".git" --exclude "node_modules"

DB_PASS="${DB_PASS:-$(openssl rand -base64 24 | tr -d '\n')}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}"
AES_KEY="${AES_KEY:-$(openssl rand -hex 32)}"
PORTAL_VLAN_IP="${PORTAL_VLAN_IP:-127.0.0.1}"

cat > /opt/portal/.env <<EOF
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=radius
DB_USER=portaluser
DB_PASS=${DB_PASS}
JWT_SECRET=${JWT_SECRET}
AES_KEY=${AES_KEY}
FR_CONFIG_DIR=/etc/freeradius/3.0
FR_LOG=/var/log/freeradius/radius.log
PORTAL_VLAN_IP=${PORTAL_VLAN_IP}
EOF

chown root:root /opt/portal/.env
chmod 600 /opt/portal/.env

mysql -uroot <<SQL
CREATE DATABASE IF NOT EXISTS radius;
CREATE USER IF NOT EXISTS 'portaluser'@'127.0.0.1' IDENTIFIED BY '${DB_PASS}';
CREATE USER IF NOT EXISTS 'portaluser'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON radius.* TO 'portaluser'@'127.0.0.1';
GRANT ALL PRIVILEGES ON radius.* TO 'portaluser'@'localhost';
FLUSH PRIVILEGES;
SQL

mysql -uroot radius < /etc/freeradius/3.0/mods-config/sql/main/mysql/schema.sql

mysql -uroot radius <<'SQL'
CREATE TABLE IF NOT EXISTS app_config (
  `key`       VARCHAR(64) PRIMARY KEY,
  value       TEXT,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  admin_user  VARCHAR(128),
  action      VARCHAR(64),
  target      VARCHAR(128),
  detail      JSON,
  ip_address  VARCHAR(45)
);

CREATE TABLE IF NOT EXISTS portal_users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(64) UNIQUE NOT NULL,
  password_hash VARCHAR(128) NOT NULL,
  role          ENUM('admin','viewer') DEFAULT 'admin',
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO app_config (`key`, value) VALUES ('setup_complete', '0')
ON DUPLICATE KEY UPDATE value='0';
SQL

id -u portaluser >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin portaluser

python3 -m venv /opt/portal/backend/.venv
/opt/portal/backend/.venv/bin/pip install --upgrade pip
/opt/portal/backend/.venv/bin/pip install -r /opt/portal/backend/requirements.txt

# Permissions: portal needs to write FR configs and reload service
usermod -a -G freerad portaluser || true
chown -R portaluser:freerad /opt/portal/backend
chown -R portaluser:freerad /etc/freeradius/3.0/mods-enabled /etc/freeradius/3.0/policy.d
chown portaluser:freerad /etc/freeradius/3.0/clients.conf || true

cat > /etc/sudoers.d/portal-freeradius-reload <<'EOF'
portaluser ALL=(ALL) NOPASSWD: /bin/systemctl reload freeradius
EOF
chmod 440 /etc/sudoers.d/portal-freeradius-reload

# Build frontend
cd /opt/portal/frontend
npm ci
npm run build

# Nginx TLS self-signed cert
install -d -m 0700 /etc/nginx/ssl
if [[ ! -f /etc/nginx/ssl/portal.crt ]]; then
  openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout /etc/nginx/ssl/portal.key \
    -out /etc/nginx/ssl/portal.crt \
    -days 825 \
    -subj "/CN=wifi-aaa-portal"
fi

cp /opt/portal/nginx/portal.conf /etc/nginx/sites-available/portal.conf
ln -sf /etc/nginx/sites-available/portal.conf /etc/nginx/sites-enabled/portal.conf
rm -f /etc/nginx/sites-enabled/default

cat > /etc/systemd/system/portal-backend.service <<'EOF'
[Unit]
Description=Wi-Fi AAA Portal Backend (FastAPI)
After=network.target mariadb.service

[Service]
Type=simple
User=portaluser
Group=freerad
WorkingDirectory=/opt/portal/backend
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/portal/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

ufw --force reset
ufw default deny incoming
ufw default allow outgoing
# Management portal (HTTPS) only on management VLAN IP
ufw allow to "${PORTAL_VLAN_IP}" port 443 proto tcp

# RADIUS ports: allow only from AC IP if provided at install time
AC_IP="${AC_IP:-}"
if [[ -n "${AC_IP}" ]]; then
  ufw allow from "${AC_IP}" to any port 1812 proto udp
  ufw allow from "${AC_IP}" to any port 1813 proto udp
fi
ufw --force enable

systemctl daemon-reload
systemctl enable --now mariadb
systemctl enable --now freeradius
systemctl enable --now portal-backend
systemctl enable --now nginx
systemctl restart nginx

echo "Setup complete. Visit https://${PORTAL_VLAN_IP}/setup to configure the portal."

