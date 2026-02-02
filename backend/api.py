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
CORS(app)  # Enable CORS for React dev server

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

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
    
    # Build query
    query = """
        SELECT b.id, b.address, b.mkd_code, b.total_sq, b.overhaul_funds_balance,
               r.region_name, mc.name as company_name, mc.phone, mc.email
        FROM buildings b
        LEFT JOIN regions r ON b.region_id = r.id
        LEFT JOIN buildings_management bm ON b.id = bm.building_id
        LEFT JOIN management_companies mc ON bm.company_id = mc.id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (b.address ILIKE %s OR b.mkd_code ILIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if region:
        query += " AND r.region_code = %s"
        params.append(region)
    
    query += f" ORDER BY b.id LIMIT {per_page} OFFSET {offset}"
    
    cur.execute(query, params)
    buildings = cur.fetchall()
    
    # Get total
    count_query = "SELECT COUNT(*) as count FROM buildings b LEFT JOIN regions r ON b.region_id = r.id WHERE 1=1"
    if search:
        count_query += " AND (b.address ILIKE %s OR b.mkd_code ILIKE %s)"
    if region:
        count_query += " AND r.region_code = %s"
    
    cur.execute(count_query, params)
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
