#!/usr/bin/env python3
"""Create database schema directly on server"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("62.113.36.101", username="root", password="j4eVZ-g@aPA2U6")

# Read local init_db.py
with open("database/init_db.sql", "r", encoding="utf-8") as f:
    schema_sql = f.read()

print("[1] Creating schema on server...")

# Execute SQL directly
stdin, stdout, stderr = ssh.exec_command(
    f"PGPASSWORD='repair_password_2026' psql -U repair_user -d capital_repair_db"
)
stdin.write(schema_sql)
stdin.close()

output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

if output:
    print(output[:1000])
if error and "ERROR" in error:
    print("ERRORS:", error[:500])

print("\n[2] Testing database...")
stdin, stdout, stderr = ssh.exec_command(
    "PGPASSWORD='repair_password_2026' psql -U repair_user -d capital_repair_db -c '\\dt'"
)
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n[3] Restarting API...")
ssh.exec_command("supervisorctl restart capital-repair-api")

ssh.close()
print("\nDone!")
