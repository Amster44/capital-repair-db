# Automatic deployment script for Capital Repair Database
$ErrorActionPreference = "Stop"

$SERVER = "root@62.113.36.101"
$PASSWORD = "j4eVZ-g@aPA2U6"
$REMOTE_DIR = "/opt/capital-repair-db"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Capital Repair DB - Automatic Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Function to run SSH command
function Run-SSH {
    param($Command)
    Write-Host "Executing: $Command" -ForegroundColor Yellow
    echo "y" | plink -ssh -pw $PASSWORD $SERVER $Command
}

# Function to run SCP upload
function Upload-Files {
    param($Source, $Destination)
    Write-Host "Uploading: $Source -> $Destination" -ForegroundColor Yellow
    echo "y" | pscp -r -pw $PASSWORD $Source "$SERVER`:$Destination"
}

# Step 1: Create remote directory
Write-Host "`n[Step 1] Creating remote directory..." -ForegroundColor Green
Run-SSH "mkdir -p $REMOTE_DIR"

# Step 2: Upload files
Write-Host "`n[Step 2] Uploading project files..." -ForegroundColor Green
Upload-Files "scripts" "$REMOTE_DIR/"
Upload-Files "backend" "$REMOTE_DIR/"
Upload-Files "frontend" "$REMOTE_DIR/"
Upload-Files "deploy" "$REMOTE_DIR/"
Upload-Files "deploy\config_production.py" "$REMOTE_DIR/scripts/config.py"

# Step 3: Install packages
Write-Host "`n[Step 3] Installing packages on server..." -ForegroundColor Green
Run-SSH "apt update && DEBIAN_FRONTEND=noninteractive apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx supervisor curl"

# Step 4: Install Node.js
Write-Host "`n[Step 4] Installing Node.js..." -ForegroundColor Green
Run-SSH "curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt install -y nodejs"

# Step 5: Setup PostgreSQL
Write-Host "`n[Step 5] Setting up PostgreSQL..." -ForegroundColor Green
$sqlCommands = @"
DROP DATABASE IF EXISTS capital_repair_db;
CREATE DATABASE capital_repair_db;
DROP USER IF EXISTS repair_user;
CREATE USER repair_user WITH PASSWORD 'repair_password_2026';
GRANT ALL PRIVILEGES ON DATABASE capital_repair_db TO repair_user;
\c capital_repair_db
GRANT ALL ON SCHEMA public TO repair_user;
"@
Run-SSH "sudo -u postgres psql -c 'DROP DATABASE IF EXISTS capital_repair_db;'"
Run-SSH "sudo -u postgres psql -c 'CREATE DATABASE capital_repair_db;'"
Run-SSH "sudo -u postgres psql -c 'DROP USER IF EXISTS repair_user;'"
Run-SSH "sudo -u postgres psql -c `"CREATE USER repair_user WITH PASSWORD 'repair_password_2026';`""
Run-SSH "sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE capital_repair_db TO repair_user;'"

# Step 6: Setup Python environment
Write-Host "`n[Step 6] Setting up Python environment..." -ForegroundColor Green
Run-SSH "cd $REMOTE_DIR && python3 -m venv venv"
Run-SSH "cd $REMOTE_DIR && source venv/bin/activate && pip install flask flask-cors psycopg2-binary pandas openpyxl gunicorn"

# Step 7: Initialize database
Write-Host "`n[Step 7] Initializing database..." -ForegroundColor Green
Run-SSH "cd $REMOTE_DIR && source venv/bin/activate && python3 scripts/init_db.py"

# Step 8: Build frontend
Write-Host "`n[Step 8] Building frontend..." -ForegroundColor Green
Run-SSH "cd $REMOTE_DIR/frontend && npm install && npm run build"

# Step 9: Configure Nginx
Write-Host "`n[Step 9] Configuring Nginx..." -ForegroundColor Green
Run-SSH "cp $REMOTE_DIR/deploy/nginx.conf /etc/nginx/sites-available/capital-repair-db"
Run-SSH "ln -sf /etc/nginx/sites-available/capital-repair-db /etc/nginx/sites-enabled/"
Run-SSH "rm -f /etc/nginx/sites-enabled/default"
Run-SSH "nginx -t && systemctl restart nginx"

# Step 10: Configure Supervisor
Write-Host "`n[Step 10] Configuring Supervisor..." -ForegroundColor Green
Run-SSH "cp $REMOTE_DIR/deploy/supervisor.conf /etc/supervisor/conf.d/capital-repair-api.conf"
Run-SSH "supervisorctl reread && supervisorctl update"
Run-SSH "supervisorctl start capital-repair-api"

# Final status check
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Checking status..." -ForegroundColor Yellow
Run-SSH "supervisorctl status capital-repair-api"

Write-Host ""
Write-Host "Application is running at: http://62.113.36.101" -ForegroundColor Green
Write-Host ""
Write-Host "To check logs:" -ForegroundColor Yellow
Write-Host "  ssh $SERVER" -ForegroundColor Gray
Write-Host "  tail -f /var/log/capital-repair-api.out.log" -ForegroundColor Gray
Write-Host ""
