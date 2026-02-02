#!/bin/bash
# Complete deployment script for Capital Repair Database

set -e

PROJECT_DIR="/opt/capital-repair-db"

echo "=========================================="
echo "Deploying Capital Repair Database"
echo "=========================================="

# Activate virtual environment
cd $PROJECT_DIR
source venv/bin/activate

# Create database schema
echo "Creating database schema..."
python3 scripts/init_db.py

# Import data (if data files exist)
if [ -d "data" ]; then
    echo "Importing data..."

    # Import regions
    if [ -f "data/regions.csv" ]; then
        echo "Importing regions..."
    fi

    # Note: Large data files should be imported separately
    # python3 scripts/import_ojf.py --all-pfo
    # python3 scripts/import_from_registry.py --all-pfo
fi

# Build React frontend
echo "Building React frontend..."
cd frontend
npm install
npm run build
cd ..

# Setup Nginx
echo "Configuring Nginx..."
cp deploy/nginx.conf /etc/nginx/sites-available/capital-repair-db
ln -sf /etc/nginx/sites-available/capital-repair-db /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Setup Supervisor
echo "Configuring Supervisor..."
cp deploy/supervisor.conf /etc/supervisor/conf.d/capital-repair-api.conf
supervisorctl reread
supervisorctl update
supervisorctl restart capital-repair-api

echo ""
echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo ""
echo "Application is running at: http://62.113.36.101"
echo ""
echo "To check status:"
echo "  - API: supervisorctl status capital-repair-api"
echo "  - Nginx: systemctl status nginx"
echo "  - Logs: tail -f /var/log/capital-repair-api.out.log"
echo ""
echo "To import data:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python3 scripts/import_ojf.py --region 63"
echo "  python3 scripts/import_from_registry.py --region 63"
echo ""
