from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from supabase import create_client, Client
import jwt
from datetime import datetime, timedelta
import traceback

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

# Authentication
def create_jwt_token(user_id: str, is_admin: bool) -> str:
    payload = {
        'user_id': user_id,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except:
        return None

def get_user_from_request():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    return verify_jwt_token(token)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if not data or not all(k in data for k in ['name', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if user exists
        user_query = supabase.table('users').select('*').eq('email', data['email']).execute()
        if user_query.data:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        new_user = {
            'name': data['name'],
            'email': data['email'],
            'password': data['password'],  # In production, hash this!
            'is_admin': data.get('is_admin', False)
        }
        
        result = supabase.table('users').insert(new_user).execute()
        user = result.data[0]
        
        # Create JWT token
        token = create_jwt_token(user['id'], user['is_admin'])
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'userId': user['id'],
            'name': user['name'],
            'is_admin': user['is_admin']
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

        # Find user
        user_query = supabase.table('users').select('*').eq('email', data['email']).eq('password', data['password']).execute()
        
        if not user_query.data:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user = user_query.data[0]
        token = create_jwt_token(user['id'], user['is_admin'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'name': user['name'],
            'is_admin': user['is_admin'],
            'userId': user['id']
        }), 200
    except Exception as e:
        print(f"Login error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Login failed', 'message': str(e)}), 500

# Products
@app.route('/api/products', methods=['GET'])
def get_all_products():
    try:
        products = supabase.table('products').select('*').execute()
        return jsonify(products.data)
    except Exception as e:
        print(f"Error loading products: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Failed to load products', 'message': str(e)}), 500

@app.route('/api/products/<product_id>', methods=['GET'])
def get_single_product(product_id):
    try:
        product = supabase.table('products').select('*').eq('id', product_id).execute()
        if not product.data:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify(product.data[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Cart
@app.route('/api/cart/<user_id>', methods=['GET', 'POST'])
def manage_cart(user_id):
    try:
        user = get_user_from_request()
        if not user or user['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        if request.method == 'GET':
            cart = supabase.table('cart_items').select('*, products(*)').eq('user_id', user_id).execute()
            return jsonify(cart.data)
        
        data = request.json
        product_id = data['product_id']
        quantity = int(data['quantity'])
        
        # Check product stock
        product = supabase.table('products').select('*').eq('id', product_id).execute()
        if not product.data:
            return jsonify({'error': 'Product not found'}), 404
        
        if quantity > product.data[0]['stock']:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        # Update or insert cart item
        cart_item = {
            'user_id': user_id,
            'product_id': product_id,
            'quantity': quantity
        }
        
        result = supabase.table('cart_items').upsert(cart_item).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cart/<user_id>/<product_id>', methods=['DELETE'])
def remove_from_cart(user_id, product_id):
    try:
        user = get_user_from_request()
        if not user or user['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        supabase.table('cart_items').delete().eq('user_id', user_id).eq('product_id', product_id).execute()
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Checkout
@app.route('/api/checkout', methods=['POST'])
def checkout():
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.json
        user_id = user['user_id']
        
        # Start transaction
        # Note: Supabase doesn't support true transactions, so we need to be careful
        
        # 1. Get cart items
        cart = supabase.table('cart_items').select('*, products(*)').eq('user_id', user_id).execute()
        if not cart.data:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # 2. Calculate total and validate stock
        total = 0
        order_items = []
        
        for item in cart.data:
            product = item['products']
            if product['stock'] < item['quantity']:
                return jsonify({'error': f"Insufficient stock for product {product['name']}"}), 400
            
            item_total = float(product['price']) * item['quantity']
            total += item_total
            
            order_items.append({
                'product_id': product['id'],
                'quantity': item['quantity'],
                'price_at_time': product['price']
            })
        
        # 3. Create order
        order = {
            'user_id': user_id,
            'total': total,
            'status': 'pending',
            'shipping_address': data.get('shipping_address', '')
        }
        
        order_result = supabase.table('orders').insert(order).execute()
        order_id = order_result.data[0]['id']
        
        # 4. Create order items
        for item in order_items:
            item['order_id'] = order_id
            supabase.table('order_items').insert(item).execute()
        
        # 5. Clear cart
        supabase.table('cart_items').delete().eq('user_id', user_id).execute()
        
        return jsonify(order_result.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin
@app.route('/api/admin/products', methods=['GET', 'POST'])
def admin_products():
    try:
        user = get_user_from_request()
        if not user or not user.get('is_admin'):
            return jsonify({'error': 'Unauthorized'}), 401

        if request.method == 'GET':
            products = supabase.table('products').select('*').execute()
            return jsonify(products.data)
        
        data = request.json
        new_product = {
            'name': data['name'],
            'description': data['description'],
            'price': float(data['price']),
            'stock': int(data['stock']),
            'image': data['image']
        }
        
        result = supabase.table('products').insert(new_product).execute()
        return jsonify(result.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/products/<product_id>', methods=['PUT', 'DELETE'])
def admin_manage_product(product_id):
    try:
        user = get_user_from_request()
        if not user or not user.get('is_admin'):
            return jsonify({'error': 'Unauthorized'}), 401

        if request.method == 'DELETE':
            supabase.table('products').delete().eq('id', product_id).execute()
            return '', 204
        
        data = request.json
        updated_product = {
            'name': data['name'],
            'description': data['description'],
            'price': float(data['price']),
            'stock': int(data['stock']),
            'image': data['image']
        }
        
        result = supabase.table('products').update(updated_product).eq('id', product_id).execute()
        if not result.data:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify(result.data[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/orders', methods=['GET'])
def admin_orders():
    try:
        user = get_user_from_request()
        if not user or not user.get('is_admin'):
            return jsonify({'error': 'Unauthorized'}), 401

        orders = supabase.table('orders').select('*, users(name, email), order_items(*)').execute()
        return jsonify(orders.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")
        exit(1)
    
    app.run(host='0.0.0.0', debug=True, port=5000) 