from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import socket
import traceback

app = Flask(__name__)
# Configure CORS to allow requests from any origin
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Error handling
@app.errorhandler(Exception)
def handle_error(error):
    print(f"Error: {str(error)}")
    print(traceback.format_exc())
    return jsonify({
        'error': 'An unexpected error occurred',
        'message': str(error)
    }), 500

# Static File Serving
@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# Data storage - In-memory for Vercel, File-based for local
IS_VERCEL = os.environ.get('VERCEL', False)

# Initialize empty data store
store = {
    'users': [],
    'products': [],
    'orders': [],
    'cart': {}
}

def load_data(filename):
    """Load data from either memory store or file system"""
    if IS_VERCEL:
        return store.get(filename.replace('.json', ''), [] if filename != 'cart.json' else {})
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        if filename == 'cart.json':
            return {}
        return []

def save_data(filename, data):
    """Save data to either memory store or file system"""
    key = filename.replace('.json', '')
    store[key] = data  # Always update in-memory store
    
    if not IS_VERCEL:  # Only save to file if not on Vercel
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

# Initialize JSON files for local development and load initial data
def init_json_files():
    files = ['users.json', 'products.json', 'orders.json', 'cart.json']
    for file in files:
        if not IS_VERCEL and not os.path.exists(file):
            with open(file, 'w') as f:
                if file == 'cart.json':
                    json.dump({}, f)
                else:
                    json.dump([], f)
        # Load initial data into memory store
        key = file.replace('.json', '')
        store[key] = load_data(file)

init_json_files()

# User Authentication
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if not data or not all(k in data for k in ['name', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400

        users = load_data('users.json')
        
        if any(user['email'] == data['email'] for user in users):
            return jsonify({'error': 'Email already registered'}), 400
        
        new_user = {
            'id': str(len(users) + 1),
            'name': data['name'],
            'email': data['email'],
            'password': data['password'],
            'is_admin': data.get('is_admin', False)
        }
        
        users.append(new_user)
        save_data('users.json', users)
        return jsonify({
            'message': 'User registered successfully',
            'userId': new_user['id'],
            'name': new_user['name'],
            'is_admin': new_user['is_admin']
        }), 201
    except Exception as e:
        print(f"Registration error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Registration failed', 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data or not all(k in data for k in ['email', 'password']):
            return jsonify({'error': 'Missing email or password'}), 400

        users = load_data('users.json')
        
        user = next((user for user in users 
                     if user['email'] == data['email'] and 
                     user['password'] == data['password']), None)
        
        if user:
            return jsonify({
                'message': 'Login successful',
                'name': user['name'],
                'is_admin': user.get('is_admin', False),
                'userId': user['id']
            }), 200
        return jsonify({'error': 'Invalid email or password'}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Login failed', 'message': str(e)}), 500

# Products
@app.route('/api/products', methods=['GET'])
def get_all_products():
    try:
        products = load_data('products.json')
        if not products:
            return jsonify({'error': 'No products available'}), 404
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': 'Failed to connect with server'}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_single_product(product_id):
    products = load_data('products.json')
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({'error': 'Product not found'}), 404

# Cart
@app.route('/api/cart/<user_id>', methods=['GET', 'POST'])
def manage_cart(user_id):
    carts = load_data('cart.json')
    user_cart = carts.get(user_id, {})
    
    if request.method == 'GET':
        return jsonify(user_cart)
    
    data = request.json
    product_id = str(data['product_id'])
    quantity = int(data['quantity'])
    
    # Validate stock
    products = load_data('products.json')
    product = next((p for p in products if str(p['id']) == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if quantity > product['stock']:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    user_cart[product_id] = quantity
    carts[user_id] = user_cart
    save_data('cart.json', carts)
    return jsonify(user_cart)

@app.route('/api/cart/<user_id>/<product_id>', methods=['DELETE'])
def remove_from_cart(user_id, product_id):
    carts = load_data('cart.json')
    if user_id in carts and str(product_id) in carts[user_id]:
        del carts[user_id][str(product_id)]
        save_data('cart.json', carts)
    return '', 204

# Checkout
@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    orders = load_data('orders.json')
    products = load_data('products.json')
    
    # Validate and update product stock
    total = 0
    order_items = []
    
    for item in data['items']:
        product = next((p for p in products if p['id'] == int(item['id'])), None)
        if not product:
            return jsonify({'error': f"Product not found: {item['id']}"}), 400
        
        quantity = int(item['quantity'])
        if product['stock'] < quantity:
            return jsonify({'error': f"Insufficient stock for product {item['id']}"}), 400
        
        product['stock'] -= quantity
        item_total = float(product['price']) * quantity
        total += item_total
        
        order_items.append({
            'product_id': item['id'],
            'quantity': quantity,
            'price': product['price'],
            'total': item_total
        })
    
    # Create order
    new_order = {
        'id': str(len(orders) + 1),
        'customer': data['customer'],
        'items': order_items,
        'total': total,
        'status': 'pending',
        'orderDate': datetime.now().isoformat()
    }
    
    save_data('products.json', products)
    orders.append(new_order)
    save_data('orders.json', orders)
    
    # Clear cart
    if 'user_id' in data:
        carts = load_data('cart.json')
        if data['user_id'] in carts:
            del carts[data['user_id']]
            save_data('cart.json', carts)
    
    return jsonify(new_order), 201

# Admin
@app.route('/api/admin/products', methods=['GET', 'POST'])
def admin_products():
    if request.method == 'GET':
        return jsonify(load_data('products.json'))
    
    data = request.json
    products = load_data('products.json')
    new_id = max([p['id'] for p in products], default=0) + 1
    
    new_product = {
        'id': new_id,
        'name': data['name'],
        'description': data['description'],
        'price': float(data['price']),
        'stock': int(data['stock']),
        'image': data['image']
    }
    
    products.append(new_product)
    save_data('products.json', products)
    return jsonify(new_product), 201

@app.route('/api/admin/products/<int:product_id>', methods=['PUT', 'DELETE'])
def admin_manage_product(product_id):
    products = load_data('products.json')
    
    if request.method == 'DELETE':
        products = [p for p in products if p['id'] != product_id]
        save_data('products.json', products)
        return '', 204
    
    data = request.json
    for i, product in enumerate(products):
        if product['id'] == product_id:
            products[i].update({
                'name': data['name'],
                'description': data['description'],
                'price': float(data['price']),
                'stock': int(data['stock']),
                'image': data['image']
            })
            save_data('products.json', products)
            return jsonify(products[i])
    
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/admin/orders', methods=['GET'])
def admin_orders():
    return jsonify(load_data('orders.json'))

if __name__ == '__main__':
    print("\nAvailable IP addresses to access the store:")
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Local Access URLs:")
    print(f"- Local:\t\thttp://localhost:5000")
    print(f"- Internal IP:\thttp://{local_ip}:5000")
    print("\nYou can use any of these URLs to access the store.")
    print("Share the Internal IP URL to access from other devices on your network.\n")
    
    app.run(host='0.0.0.0', debug=True, port=5000) 