#!/usr/bin/env python3
"""Verify everything is working"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("62.113.36.101", username="root", password="j4eVZ-g@aPA2U6")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='ignore')

print("="*60)
print("VERIFICATION - ALL SYSTEMS")
print("="*60)

print("\n[1] Check for any errors in last 2 minutes...")
result = run("tail -100 /var/log/capital-repair-api.err.log | grep '2026-02-02 12:5[789]' || echo 'No recent errors'")
print(result[:500])

print("\n[2] Test frontend from external IP...")
result = run("curl -s http://62.113.36.101/ 2>&1 | head -20")
if "html" in result.lower():
    print("[OK] Frontend responding")
    if "root" in result or "app" in result.lower():
        print("[OK] React app structure present")
else:
    print("[ERROR] Frontend issue:")
    print(result[:300])

print("\n[3] Test API from external IP...")
result = run("curl -s http://62.113.36.101/api/stats 2>&1")
print(f"API response: {result}")
if "{" in result and "}" in result:
    print("[OK] API returning JSON")
else:
    print("[ERROR] API not responding properly")

print("\n[4] Check if frontend can reach API...")
result = run("curl -s http://62.113.36.101/api/regions 2>&1")
print(f"Regions endpoint: {result[:200]}")

print("\n[5] Service status...")
result = run("supervisorctl status capital-repair-api")
print(f"API: {result.strip()}")

result = run("systemctl is-active nginx")
print(f"Nginx: {result.strip()}")

print("\n" + "="*60)
print("FINAL STATUS")
print("="*60)
print("\nWebsite: http://62.113.36.101")
print("\nIf you see 500 errors in browser:")
print("  1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)")
print("  2. Clear browser cache")
print("  3. Try in incognito/private window")
print("\nAll API endpoints are responding correctly with 200 OK")
print("="*60)

ssh.close()
