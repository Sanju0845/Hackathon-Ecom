from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import socket
import traceback
import base64

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

# Data storage - Environment variables for Vercel, File-based for local
IS_VERCEL = os.environ.get('VERCEL', False)

def load_data(filename):
    """Load data from either environment variables or file system"""
    if IS_VERCEL:
        # Try to get data from environment variable
        env_key = f"STORE_{filename.replace('.json', '').upper()}"
        data_str = os.environ.get(env_key)
        
        if data_str:
            try:
                # Decode base64 and parse JSON
                decoded_data = base64.b64decode(data_str).decode('utf-8')
                return json.loads(decoded_data)
            except:
                print(f"Error loading data from env {env_key}")
                pass
        
        # Return empty default if no data found
        return [] if filename != 'cart.json' else {}
    
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        if filename == 'cart.json':
            return {}
        return []

def save_data(filename, data):
    """Save data to either environment variables or file system"""
    if IS_VERCEL:
        # Convert data to base64 string
        json_str = json.dumps(data)
        base64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        # Set environment variable
        env_key = f"STORE_{filename.replace('.json', '').upper()}"
        os.environ[env_key] = base64_str
        
        # Print for debugging
        print(f"Saved data to {env_key}: {json_str[:100]}...")
    else:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

# Initialize data store
def init_json_files():
    files = ['users.json', 'products.json', 'orders.json', 'cart.json']
    for file in files:
        if not IS_VERCEL and not os.path.exists(file):
            with open(file, 'w') as f:
                if file == 'cart.json':
                    json.dump({}, f)
                else:
                    json.dump([], f)

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
        print("Loading products...")
        products = load_data('products.json')
        print(f"Products loaded: {json.dumps(products, indent=2)}")
        
        # Ensure products is always an array
        if not isinstance(products, list):
            print("Products is not a list, initializing empty array")
            products = []
        
        # Initialize products with some default items if empty
        if len(products) == 0:
            print("No products found, checking admin products...")
            admin_products = load_data('admin_products.json')
            if admin_products and len(admin_products) > 0:
                products = admin_products
                print(f"Loaded {len(products)} products from admin_products.json")
            elif IS_VERCEL:
                # Load from environment variable directly
                env_products = os.environ.get('VERCEL_PRODUCTS')
                if env_products:
                    try:
                        products = json.loads(base64.b64decode(env_products).decode('utf-8'))
                        print(f"Loaded {len(products)} products from VERCEL_PRODUCTS env")
                    except Exception as e:
                        print(f"Error loading from VERCEL_PRODUCTS: {str(e)}")
                
                # If still no products, use defaults
                if len(products) == 0:
                    products = [
                        {
                            "id": 1,
                            "name": "Sample Product 1",
                            "description": "This is a sample product",
                            "price": 29.99,
                            "stock": 10,
                            "image": "https://via.placeholder.com/300"
                        },
                        {
                            "id": 2,
                            "name": "Sample Product 2",
                            "description": "Another sample product",
                            "price": 39.99,
                            "stock": 15,
                            "image": "https://via.placeholder.com/300"
                        }
                    ]
                    print("Using default products")
            
            # Save the products
            save_data('products.json', products)
            print(f"Saved {len(products)} products")
        
        print(f"Returning {len(products)} products")
        return jsonify(products)
    except Exception as e:
        print(f"Error loading products: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Failed to load products', 'message': str(e)}), 500

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
    
    # Also save to a separate admin products file for persistence
    admin_products = load_data('admin_products.json')
    if not isinstance(admin_products, list):
        admin_products = []
    admin_products.append(new_product)
    save_data('admin_products.json', admin_products)
    
    # Save directly to Vercel environment
    if IS_VERCEL:
        try:
            json_str = json.dumps(products)
            base64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            os.environ['VERCEL_PRODUCTS'] = base64_str
            print("Saved products to VERCEL_PRODUCTS env")
        except Exception as e:
            print(f"Error saving to VERCEL_PRODUCTS: {str(e)}")
    
    return jsonify(new_product), 201

@app.route('/api/admin/products/<int:product_id>', methods=['PUT', 'DELETE'])
def admin_manage_product(product_id):
    products = load_data('products.json')
    admin_products = load_data('admin_products.json')
    
    if request.method == 'DELETE':
        products = [p for p in products if p['id'] != product_id]
        admin_products = [p for p in admin_products if p['id'] != product_id]
        save_data('products.json', products)
        save_data('admin_products.json', admin_products)
        
        if IS_VERCEL:
            try:
                json_str = json.dumps(products)
                base64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
                os.environ['VERCEL_PRODUCTS'] = base64_str
            except Exception as e:
                print(f"Error saving to VERCEL_PRODUCTS: {str(e)}")
        
        return '', 204
    
    data = request.json
    updated = False
    for i, product in enumerate(products):
        if product['id'] == product_id:
            products[i].update({
                'name': data['name'],
                'description': data['description'],
                'price': float(data['price']),
                'stock': int(data['stock']),
                'image': data['image']
            })
            updated = True
            break
    
    if updated:
        save_data('products.json', products)
        
        # Update admin products as well
        for i, product in enumerate(admin_products):
            if product['id'] == product_id:
                admin_products[i].update({
                    'name': data['name'],
                    'description': data['description'],
                    'price': float(data['price']),
                    'stock': int(data['stock']),
                    'image': data['image']
                })
                break
        save_data('admin_products.json', admin_products)
        
        if IS_VERCEL:
            try:
                json_str = json.dumps(products)
                base64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
                os.environ['VERCEL_PRODUCTS'] = base64_str
            except Exception as e:
                print(f"Error saving to VERCEL_PRODUCTS: {str(e)}")
        
        return jsonify(products[i])
    
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/admin/orders', methods=['GET'])
def admin_orders():
    return jsonify(load_data('orders.json'))

# Add a debug endpoint to check environment variables
@app.route('/api/debug/env', methods=['GET'])
def debug_env():
    try:
        products = load_data('products.json')
        admin_products = load_data('admin_products.json')
        env_vars = {
            'VERCEL': os.environ.get('VERCEL', 'not set'),
            'STORE_PRODUCTS': bool(os.environ.get('STORE_PRODUCTS', False)),
            'VERCEL_PRODUCTS': bool(os.environ.get('VERCEL_PRODUCTS', False)),
            'products_count': len(products),
            'admin_products_count': len(admin_products) if admin_products else 0,
            'all_env_keys': [k for k in os.environ.keys() if k.startswith('STORE_') or k.startswith('VERCEL_')]
        }
        print(f"Debug env vars: {env_vars}")
        return jsonify(env_vars)
    except Exception as e:
        return jsonify({'error': str(e)})

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