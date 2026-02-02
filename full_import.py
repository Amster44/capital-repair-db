#!/usr/bin/env python3
"""Full import of all regions with logging"""
import paramiko
import time
from datetime import datetime

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("62.113.36.101", username="root", password="j4eVZ-g@aPA2U6")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    return out, err

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

regions = [
    ('02', 'Bashkortostan'),
    ('12', 'Mariy-El'),
    ('13', 'Mordoviya'),
    ('16', 'Tatarstan'),
    ('18', 'Udmurtiya'),
    ('21', 'Chuvashiya'),
    ('43', 'Kirov'),
    ('52', 'Nizhniy-Novgorod'),
    ('56', 'Orenburg'),
    ('58', 'Penza'),
    ('59', 'Perm'),
    ('63', 'Samara'),
    ('64', 'Saratov'),
    ('73', 'Ulyanovsk')
]

print("="*60)
print("FULL IMPORT - ALL REGIONS")
print("="*60)
log(f"Starting import of {len(regions)} regions x 3 KR files = {len(regions)*3} imports")
print()

total_imports = len(regions) * 3
completed = 0

for region_code, region_name in regions:
    log(f"Region [{region_code}] {region_name}")

    for kr in ['1.1', '1.2', '1.3']:
        completed += 1
        log(f"  [{completed}/{total_imports}] KR {kr}...")

        start_time = time.time()
        out, err = run(f"cd /opt/capital-repair-db && venv/bin/python3 scripts/import_csv.py --region {region_code} --kr {kr} 2>&1")
        elapsed = time.time() - start_time

        # Parse output for success
        if 'Imported' in out or 'успешно' in out.lower():
            lines = [l for l in out.split('\n') if 'Imported' in l or 'building' in l.lower() or 'lift' in l.lower()]
            if lines:
                log(f"      {lines[0].strip()[:80]}")
            log(f"      Time: {elapsed:.1f}s")
        elif 'error' in out.lower() or 'ERROR' in out:
            log(f"      [ERROR] {out[:200]}")
        else:
            log(f"      Completed in {elapsed:.1f}s")

    log("")

log("="*50)
log("Stage 2: Linking management companies (OJF data)")
log("="*50)

start_time = time.time()
out, err = run("cd /opt/capital-repair-db && venv/bin/python3 scripts/import_ojf.py 2>&1")
elapsed = time.time() - start_time

log(f"OJF processing completed in {elapsed:.1f}s")
log("")

# Show key lines from output
for line in out.split('\n'):
    if 'linked' in line.lower() or 'processed' in line.lower() or 'found' in line.lower():
        log(f"  {line.strip()}")

log("")
log("="*50)
log("Final Statistics")
log("="*50)

out, err = run("""PGPASSWORD='repair_password_2026' psql -h localhost -U repair_user -d capital_repair_db -c "
SELECT
    (SELECT COUNT(*) FROM buildings) as buildings,
    (SELECT COUNT(*) FROM management_companies) as companies,
    (SELECT COUNT(*) FROM buildings_management) as linked,
    (SELECT COUNT(*) FROM lifts) as lifts,
    (SELECT COUNT(*) FROM regions) as regions;
" 2>&1""")

print(out)

log("")
log("Testing API...")
out, err = run("curl -s http://127.0.0.1:5000/api/stats")
log(f"API response: {out}")

ssh.close()

print("\n" + "="*60)
log("IMPORT COMPLETE!")
log("Website: http://62.113.36.101")
print("="*60)
