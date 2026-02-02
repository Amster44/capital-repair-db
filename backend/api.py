"""
Capital Repair Management - REST API
Flask backend for React frontend
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import DB_CONFIG

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Правильная работа с UTF-8
CORS(app)  # Enable CORS for React dev server

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@app.route('/api/regions', methods=['GET'])
def get_regions():
    """Get list of regions from buildings table"""
    conn = get_db()
    cur = conn.cursor()

    # Get distinct regions from buildings (text field, not FK)
    cur.execute("""
        SELECT DISTINCT region
        FROM buildings
        WHERE region IS NOT NULL
        ORDER BY region
    """)
    regions_raw = cur.fetchall()

    # Format as list of region names
    regions = [{'region': r['region']} for r in regions_raw]

    cur.close()
    conn.close()

    return jsonify({'regions': regions})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    conn = get_db()
    cur = conn.cursor()
    
    stats = {}
    
    # Buildings count
    cur.execute("SELECT COUNT(*) as count FROM buildings")
    stats['buildings'] = cur.fetchone()['count']
    
    # Companies count
    cur.execute("SELECT COUNT(*) as count FROM management_companies")
    stats['companies'] = cur.fetchone()['count']
    
    # Companies with contacts
    cur.execute("SELECT COUNT(*) as count FROM management_companies WHERE phone IS NOT NULL")
    stats['with_phone'] = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM management_companies WHERE email IS NOT NULL")
    stats['with_email'] = cur.fetchone()['count']
    
    # Linked buildings
    cur.execute("SELECT COUNT(*) as count FROM buildings_management")
    stats['linked'] = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    
    return jsonify(stats)

@app.route('/api/buildings', methods=['GET'])
def get_buildings():
    """Get buildings list with pagination and filters"""
    conn = get_db()
    cur = conn.cursor()
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # Filters
    search = request.args.get('search', '')
    region = request.args.get('region', '')
    account_type = request.args.get('account_type', '')  # 'SPEC' or 'REGOP'
    min_balance = request.args.get('min_balance', '')
    replacement_year = request.args.get('replacement_year', '')  # Конкретный год замены
    has_lifts = request.args.get('has_lifts', 'true')  # Только с лифтами (по умолчанию true)
    sort_by = request.args.get('sort_by', 'balance')  # balance, address, lifts, date
    sort_order = request.args.get('sort_order', 'desc')  # asc or desc

    # Build query with lifts info
    query = """
        SELECT b.id, b.address, b.mkd_code, b.total_sq, b.overhaul_funds_balance,
               b.spec_account_owner_type, b.region, mc.name as company_name, mc.phone, mc.email, mc.director_name,
               (SELECT COUNT(*) FROM lifts WHERE building_id = b.id) as lifts_count,
               (SELECT MIN(decommissioning_date) FROM lifts WHERE building_id = b.id) as nearest_replacement
        FROM buildings b
        LEFT JOIN buildings_management bm ON b.id = bm.building_id
        LEFT JOIN management_companies mc ON bm.company_id = mc.id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (b.address ILIKE %s OR b.mkd_code ILIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])

    if region:
        query += " AND b.region = %s"
        params.append(region)

    # Filter by account type
    if account_type == 'SPEC':
        query += " AND b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK')"
    elif account_type == 'REGOP':
        query += " AND (b.spec_account_owner_type = 'REGOP' OR b.spec_account_owner_type IS NULL)"

    # Filter by minimum balance (значения уже в тысячах в БД!)
    if min_balance:
        try:
            min_bal = float(min_balance)
            query += " AND b.overhaul_funds_balance >= %s"
            params.append(min_bal)
        except ValueError:
            pass

    # Filter by replacement years (можно выбрать несколько годов через запятую)
    if replacement_year:
        try:
            # Разбираем строку с годами: "2025,2026,2027" -> [2025, 2026, 2027]
            years = [int(y.strip()) for y in replacement_year.split(',') if y.strip()]
            if years:
                placeholders = ','.join(['%s'] * len(years))
                query += f" AND EXISTS (SELECT 1 FROM lifts l WHERE l.building_id = b.id AND EXTRACT(YEAR FROM l.decommissioning_date) IN ({placeholders}))"
                params.extend(years)
        except ValueError:
            pass

    # Filter by lifts presence (только дома с лифтами)
    if has_lifts == 'true':
        query += " AND EXISTS (SELECT 1 FROM lifts WHERE building_id = b.id)"

    # Sorting
    sort_column = 'b.overhaul_funds_balance'  # default
    if sort_by == 'address':
        sort_column = 'b.address'
    elif sort_by == 'lifts':
        sort_column = 'lifts_count'
    elif sort_by == 'date':
        sort_column = 'nearest_replacement'
    elif sort_by == 'balance':
        sort_column = 'b.overhaul_funds_balance'

    sort_dir = 'DESC' if sort_order == 'desc' else 'ASC'
    query += f" ORDER BY {sort_column} {sort_dir} NULLS LAST LIMIT {per_page} OFFSET {offset}"
    
    cur.execute(query, params)
    buildings = cur.fetchall()
    
    # Get total count (using same filters)
    count_query = "SELECT COUNT(*) as count FROM buildings b WHERE 1=1"
    count_params = []

    if search:
        count_query += " AND (b.address ILIKE %s OR b.mkd_code ILIKE %s)"
        count_params.extend([f'%{search}%', f'%{search}%'])

    if region:
        count_query += " AND b.region = %s"
        count_params.append(region)

    if account_type == 'SPEC':
        count_query += " AND b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK')"
    elif account_type == 'REGOP':
        count_query += " AND (b.spec_account_owner_type = 'REGOP' OR b.spec_account_owner_type IS NULL)"

    if min_balance:
        try:
            min_bal = float(min_balance)
            count_query += " AND b.overhaul_funds_balance >= %s"
            count_params.append(min_bal)
        except ValueError:
            pass

    if replacement_year:
        try:
            # Разбираем строку с годами: "2025,2026,2027" -> [2025, 2026, 2027]
            years = [int(y.strip()) for y in replacement_year.split(',') if y.strip()]
            if years:
                placeholders = ','.join(['%s'] * len(years))
                count_query += f" AND EXISTS (SELECT 1 FROM lifts l WHERE l.building_id = b.id AND EXTRACT(YEAR FROM l.decommissioning_date) IN ({placeholders}))"
                count_params.extend(years)
        except ValueError:
            pass

    if has_lifts == 'true':
        count_query += " AND EXISTS (SELECT 1 FROM lifts WHERE building_id = b.id)"

    cur.execute(count_query, count_params)
    total = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    
    return jsonify({
        'buildings': buildings,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/companies', methods=['GET'])
def get_companies():
    """Get management companies list"""
    conn = get_db()
    cur = conn.cursor()
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    search = request.args.get('search', '')
    
    query = """
        SELECT mc.id, mc.name, mc.ogrn, mc.phone, mc.email, mc.director_name,
               COUNT(bm.building_id) as buildings_count
        FROM management_companies mc
        LEFT JOIN buildings_management bm ON mc.id = bm.company_id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (mc.name ILIKE %s OR mc.ogrn ILIKE %s OR mc.phone ILIKE %s)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    query += f" GROUP BY mc.id ORDER BY buildings_count DESC LIMIT {per_page} OFFSET {offset}"
    
    cur.execute(query, params)
    companies = cur.fetchall()
    
    # Get total
    cur.execute("SELECT COUNT(*) as count FROM management_companies")
    total = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    
    return jsonify({
        'companies': companies,
        'total': total,
        'page': page,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/companies/<int:company_id>', methods=['GET'])
def get_company(company_id):
    """Get company details"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT mc.*, COUNT(bm.building_id) as buildings_count
        FROM management_companies mc
        LEFT JOIN buildings_management bm ON mc.id = bm.company_id
        WHERE mc.id = %s
        GROUP BY mc.id
    """, (company_id,))
    
    company = cur.fetchone()
    
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Get buildings for this company
    cur.execute("""
        SELECT b.id, b.address, b.mkd_code, b.total_sq
        FROM buildings b
        JOIN buildings_management bm ON b.id = bm.building_id
        WHERE bm.company_id = %s
        LIMIT 100
    """, (company_id,))
    
    buildings = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'company': company,
        'buildings': buildings
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
