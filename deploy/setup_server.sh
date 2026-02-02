#!/bin/bash
# Script to setup Capital Repair Database on Ubuntu server

set -e

echo "=========================================="
echo "Capital Repair Database - Server Setup"
echo "=========================================="

# Update system
echo "Updating system packages..."
apt update
apt upgrade -y

# Install required packages
echo "Installing required packages..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    supervisor

# Install Node.js for React frontend
echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Create project directory
echo "Creating project directory..."
mkdir -p /opt/capital-repair-db
cd /opt/capital-repair-db

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install \
    flask \
    flask-cors \
    psycopg2-binary \
    pandas \
    openpyxl \
    gunicorn

# Setup PostgreSQL
echo "Setting up PostgreSQL database..."
sudo -u postgres psql <<EOF
-- Create database
DROP DATABASE IF EXISTS capital_repair_db;
CREATE DATABASE capital_repair_db;

-- Create user
DROP USER IF EXISTS repair_user;
CREATE USER repair_user WITH PASSWORD 'repair_password_2026';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE capital_repair_db TO repair_user;
\c capital_repair_db
GRANT ALL ON SCHEMA public TO repair_user;
EOF

echo ""
echo "=========================================="
echo "Server setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Upload project files to /opt/capital-repair-db"
echo "2. Run: source /opt/capital-repair-db/venv/bin/activate"
echo "3. Run: python scripts/init_db.py"
echo "4. Run: python scripts/import_*.py to import data"
echo "5. Setup nginx and supervisor for production"
echo ""
