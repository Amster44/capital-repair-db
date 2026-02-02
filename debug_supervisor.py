#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("62.113.36.101", username="root", password="j4eVZ-g@aPA2U6")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='ignore') + stderr.read().decode('utf-8', errors='ignore')

print("=== Supervisor Config ===")
print(run("cat /etc/supervisor/conf.d/capital-repair-api.conf"))

print("\n=== Supervisor Logs ===")
print(run("tail -20 /var/log/supervisor/supervisord.log"))

print("\n=== Try Manual Start ===")
print(run("cd /opt/capital-repair-db && venv/bin/gunicorn --bind 127.0.0.1:5000 backend.api:app &"))

print("\n=== Wait and Check ===")
import time
time.sleep(2)
print(run("ps aux | grep gunicorn"))

print("\n=== Test Direct API ===")
print(run("curl -s http://127.0.0.1:5000/api/regions"))

ssh.close()
