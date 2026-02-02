#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("62.113.36.101", username="root", password="j4eVZ-g@aPA2U6")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out:
        print(out)
    if err:
        print("ERROR:", err)
    return out + err

print("[1] Checking API logs...")
print(run("tail -30 /var/log/capital-repair-api.out.log"))

print("\n[2] Checking error logs...")
print(run("tail -30 /var/log/capital-repair-api.err.log"))

print("\n[3] Initializing database...")
result = run("cd /opt/capital-repair-db && venv/bin/python3 scripts/init_db.py")

print("\n[4] Restarting API...")
run("supervisorctl restart capital-repair-api")

print("\n[5] Testing API endpoint...")
import time
time.sleep(2)
print(run("curl -s http://127.0.0.1:5000/api/regions"))

ssh.close()
