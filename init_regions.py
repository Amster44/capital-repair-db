#!/usr/bin/env python3
"""Initialize regions in database"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("62.113.36.101", username="root", password="j4eVZ-g@aPA2U6")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='ignore')

print("="*60)
print("INITIALIZE REGIONS")
print("="*60)

# Volga FD regions
regions = [
    ('02', 'Республика Башкортостан'),
    ('12', 'Республика Марий Эл'),
    ('13', 'Республика Мордовия'),
    ('16', 'Республика Татарстан'),
    ('18', 'Удмуртская Республика'),
    ('21', 'Чувашская Республика'),
    ('43', 'Кировская область'),
    ('52', 'Нижегородская область'),
    ('56', 'Оренбургская область'),
    ('58', 'Пензенская область'),
    ('59', 'Пермский край'),
    ('63', 'Самарская область'),
    ('64', 'Саратовская область'),
    ('73', 'Ульяновская область')
]

print("\nInserting regions...")
for code, name in regions:
    sql = f"INSERT INTO regions (region_code, region_name, federal_district) VALUES ('{code}', '{name}', 'Приволжский ФО') ON CONFLICT (region_code) DO NOTHING;"
    result = run(f"""PGPASSWORD='repair_password_2026' psql -h localhost -U repair_user -d capital_repair_db -c "{sql}" 2>&1""")
    if "INSERT" in result:
        print(f"  [OK] {code} - {name}")
    else:
        print(f"  [SKIP] {code} - {name} (already exists)")

print("\nVerifying...")
result = run("""PGPASSWORD='repair_password_2026' psql -h localhost -U repair_user -d capital_repair_db -c "SELECT region_code, region_name FROM regions ORDER BY region_code;" 2>&1""")
print(result)

ssh.close()

print("\n" + "="*60)
print("REGIONS INITIALIZED!")
print("="*60)
