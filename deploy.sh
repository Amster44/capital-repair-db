#!/bin/bash
# Automatic deployment script
# Usage: Run this script and enter password when prompted

SERVER="root@62.113.36.101"
REMOTE_DIR="/opt/capital-repair-db"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "Capital Repair DB - Deployment"
echo "============================================"
echo ""
echo "Server: $SERVER"
echo "Password: j4eVZ-g@aPA2U6"
echo ""

# Create remote directory
echo "[1/10] Creating remote directory..."
ssh $SERVER "mkdir -p $REMOTE_DIR"

# Upload files
echo "[2/10] Uploading scripts..."
scp -r "$LOCAL_DIR/scripts" $SERVER:$REMOTE_DIR/

echo "[3/10] Uploading backend..."
scp -r "$LOCAL_DIR/backend" $SERVER:$REMOTE_DIR/

echo "[4/10] Uploading frontend..."
scp -r "$LOCAL_DIR/frontend" $SERVER:$REMOTE_DIR/

echo "[5/10] Uploading deploy files..."
scp -r "$LOCAL_DIR/deploy" $SERVER:$REMOTE_DIR/

echo "[6/10] Uploading config..."
scp "$LOCAL_DIR/deploy/config_production.py" $SERVER:$REMOTE_DIR/scripts/config.py

# Create deployment script on server
echo "[7/10] Creating deployment script on server..."
ssh $SERVER "cat > $REMOTE_DIR/deploy_on_server.sh" <<'EOFSCRIPT'
#!/bin/bash
set -e

echo "Installing packages..."
apt update
DEBIAN_FRONTEND=noninteractive apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx supervisor curl

echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

echo "Setting up PostgreSQL..."
sudo -u postgres psql <<'EOF'
DROP DATABASE IF EXISTS capital_repair_db;
CREATE DATABASE capital_repair_db;
DROP USER IF EXISTS repair_user;
CREATE USER repair_user WITH PASSWORD 'repair_password_2026';
GRANT ALL PRIVILEGES ON DATABASE capital_repair_db TO repair_user;
\c capital_repair_db
GRANT ALL ON SCHEMA public TO repair_user;
EOF

echo "Setting up Python environment..."
cd /opt/capital-repair-db
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors psycopg2-binary pandas openpyxl gunicorn

echo "Initializing database..."
python3 scripts/init_db.py

echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Configuring Nginx..."
cp deploy/nginx.conf /etc/nginx/sites-available/capital-repair-db
ln -sf /etc/nginx/sites-available/capital-repair-db /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "Configuring Supervisor..."
cp deploy/supervisor.conf /etc/supervisor/conf.d/capital-repair-api.conf
supervisorctl reread
supervisorctl update
supervisorctl start capital-repair-api

echo ""
echo "Deployment completed!"
echo "Checking status..."
supervisorctl status capital-repair-api
EOFSCRIPT

# Execute deployment on server
echo "[8/10] Executing deployment on server..."
ssh $SERVER "chmod +x $REMOTE_DIR/deploy_on_server.sh && $REMOTE_DIR/deploy_on_server.sh"

# Check status
echo "[9/10] Checking status..."
ssh $SERVER "supervisorctl status capital-repair-api"

echo ""
echo "============================================"
echo "Deployment completed!"
echo "============================================"
echo ""
echo "Application: http://62.113.36.101"
echo ""
echo "Check logs:"
echo "  ssh $SERVER"
echo "  tail -f /var/log/capital-repair-api.out.log"
echo ""
