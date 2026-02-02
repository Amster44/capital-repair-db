#!/usr/bin/env python3
"""Initialize database schema"""
import paramiko
from scp import SCPClient

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("62.113.36.101", username="root", password="j4eVZ-g@aPA2U6")

print("[1] Uploading SQL files...")
with SCPClient(ssh.get_transport()) as scp:
    scp.put("database/001_initial_schema.sql", "/tmp/")
    scp.put("database/002_views_and_data.sql", "/tmp/")

print("[2] Executing schema...")
stdin, stdout, stderr = ssh.exec_command(
    "PGPASSWORD='repair_password_2026' psql -U repair_user -d capital_repair_db -f /tmp/001_initial_schema.sql"
)
print(stdout.read().decode('utf-8', errors='ignore')[:500])

print("\n[3] Executing views and data...")
stdin, stdout, stderr = ssh.exec_command(
    "PGPASSWORD='repair_password_2026' psql -U repair_user -d capital_repair_db -f /tmp/002_views_and_data.sql"
)
print(stdout.read().decode('utf-8', errors='ignore')[:500])

print("\n[4] Checking tables...")
stdin, stdout, stderr = ssh.exec_command(
    "PGPASSWORD='repair_password_2026' psql -U repair_user -d capital_repair_db -c '\\dt'"
)
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n[5] Restarting API...")
stdin, stdout, stderr = ssh.exec_command("supervisorctl restart capital-repair-api")
print(stdout.read().decode('utf-8', errors='ignore'))

import time
time.sleep(2)

print("\n[6] Testing API...")
stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:5000/api/regions")
result = stdout.read().decode('utf-8', errors='ignore')
print(result[:300])

ssh.close()

if "404" not in result and "<!doctype" not in result.lower():
    print("\n[SUCCESS] API is working!")
else:
    print("\n[WARNING] API may have issues")
