from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Supabase configuration
supabase = create_client(
    os.getenv('SUPABASE_URL', 'https://puwefvbaowdflcidyzto.supabase.co'),
    os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1d2VmdmJhb3dkZmxjaWR5enRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwOTcyODcsImV4cCI6MjA2MzY3MzI4N30.TpZ8rmEP8rPHH66fmB_NJxAceXMoPHmD9DJpCc17cjE')
)

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    try:
        # Check if user already exists
        existing_user = supabase.table('users').select("*").eq('email', data['email']).execute()
        if existing_user.data:
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        response = supabase.table('users').insert({
            'email': data['email'],
            'password': data['password'],
            'full_name': data.get('name', ''),
            'phone_number': data.get('phone', ''),
            'shipping_address': data.get('address', '')
        }).execute()
        
        if response.data:
            user = response.data[0]
            return jsonify({
                'id': user['id'],
                'email': user['email'],
                'name': user.get('full_name', ''),
                'phone': user.get('phone_number', ''),
                'address': user.get('shipping_address', '')
            })
        return jsonify({'error': 'Failed to create user'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    try:
        # Check if it's an admin login
        if data['email'] == 'admin@gmail.com' and data['password'] == 'admin':
            print('Admin login detected')  # Debug log
            return jsonify({
                'id': 'admin',
                'email': 'admin@gmail.com',
                'name': 'Admin',
                'is_admin': True,
                'role': 'admin'  # Added role field
            })
        
        # Regular user login
        response = supabase.table('users').select("*").eq('email', data['email']).eq('password', data['password']).execute()
        
        if response.data:
            user = response.data[0]
                return jsonify({
                'id': user['id'],
                'email': user['email'],
                'name': user.get('full_name', ''),
                'phone': user.get('phone_number', ''),
                'address': user.get('shipping_address', ''),
                'is_admin': False,
                'role': 'user'  # Added role field
            })
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        print('Login error:', str(e))  # Debug log
        return jsonify({'error': str(e)}), 400

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
                response = supabase.table('products').select("*").execute()
                return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/products/<id>', methods=['GET'])
def get_product(id):
    try:
        response = supabase.table('products').select("*").eq('id', id).execute()
        if response.data:
            return jsonify(response.data[0])
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/cart', methods=['GET'])
def get_cart():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    try:
        response = supabase.table('cart_items').select("*, products(*)").eq('user_id', user_id).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    if not data.get('user_id'):
        return jsonify({'error': 'User ID required'}), 400
    
    try:
        # Check if product exists and has stock
        product_response = supabase.table('products').select("*").eq('id', data['product_id']).execute()
        if not product_response.data:
            return jsonify({'error': 'Product not found'}), 404
        
        product = product_response.data[0]
        if product['stock'] <= 0:
            return jsonify({'error': 'Product out of stock'}), 400

        # Check if item already in cart
        existing_item = supabase.table('cart_items').select("*").eq('user_id', data['user_id']).eq('product_id', data['product_id']).execute()
        
        if existing_item.data:
            # Update quantity if item exists
            new_quantity = existing_item.data[0]['quantity'] + data.get('quantity', 1)
            if new_quantity > product['stock']:
                return jsonify({'error': 'Not enough stock available'}), 400
                
            supabase.table('cart_items').update({'quantity': new_quantity}).eq('id', existing_item.data[0]['id']).execute()
        else:
            # Add new item if not in cart
            if data.get('quantity', 1) > product['stock']:
                return jsonify({'error': 'Not enough stock available'}), 400
                
            supabase.table('cart_items').insert({
                'user_id': data['user_id'],
                'product_id': data['product_id'],
                'quantity': data.get('quantity', 1)
            }).execute()
        
        return jsonify({'message': 'Added to cart'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/cart/remove/<id>', methods=['POST'])
def remove_from_cart(id):
    try:
        supabase.table('cart_items').delete().eq('id', id).execute()
        return jsonify({'message': 'Removed from cart'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    try:
        # Create order with exact column names from database schema
        order_response = supabase.table('orders').insert({
            'user_id': data['user_id'],
                        'total': data['total'],
                        'status': 'pending'
                    }).execute()
                    
        if not order_response.data:
            return jsonify({'error': 'Failed to create order'}), 400
            
        order = order_response.data[0]
        
        # Create order items
                    for item in data['items']:
            supabase.table('order_items').insert({
                'order_id': order['id'],
                'product_id': item['product_id'],  # Use product_id from the request
                            'quantity': item['quantity'],
                'price_at_time': item['price']  # Use price from the request
            }).execute()

                    # Clear cart
        supabase.table('cart_items').delete().eq('user_id', data['user_id']).execute()
        
        return jsonify({
            'order_id': order['id'],
            'status': 'success',
            'message': 'Order placed successfully'
        })
                except Exception as e:
        print('Checkout error:', str(e))  # Add logging
        return jsonify({'error': str(e)}), 400

@app.route('/api/orders', methods=['GET'])
def get_orders():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    try:
        # If user_id is 'admin', return all orders
        if user_id == 'admin':
            response = supabase.table('orders').select("*, order_items(*, products(*))").execute()
        else:
            # For regular users, return only their orders
            response = supabase.table('orders').select("*, order_items(*, products(*))").eq('user_id', user_id).execute()
        
        return jsonify(response.data)
    except Exception as e:
        print('Error fetching orders:', str(e))  # Add logging
        return jsonify({'error': str(e)}), 400

# Admin routes
@app.route('/api/admin/products', methods=['GET', 'POST'])
def admin_products():
    try:
        if request.method == 'POST':
            data = request.json
            response = supabase.table('products').insert({
                'name': data['name'],
                'description': data.get('description'),
                'price': data['price'],
                'image_url': data.get('image_url'),
                'category': data.get('category'),
                'stock': data.get('stock', 0)
            }).execute()
            return jsonify(response.data[0] if response.data else {'error': 'Failed to create product'})

        response = supabase.table('products').select("*").execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/admin/products/<id>', methods=['PUT', 'DELETE'])
def admin_product(id):
    try:
        if request.method == 'DELETE':
            supabase.table('products').delete().eq('id', id).execute()
            return jsonify({'message': 'Product deleted'})
        
        data = request.json
        response = supabase.table('products').update({
            'name': data.get('name'),
            'description': data.get('description'),
            'price': data.get('price'),
            'image_url': data.get('image_url'),
            'category': data.get('category'),
            'stock': data.get('stock')
        }).eq('id', id).execute()
        
        return jsonify({'message': 'Product updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/admin/orders', methods=['GET'])
def admin_orders():
    try:
        response = supabase.table('orders').select("*, users!orders_user_id_fkey(*), order_items(*, products(*))").execute()
        # Transform the response to match the frontend's expected format
        orders = []
        for order in response.data:
            user = order.get('users', {})
            order_items = order.get('order_items', [])
            transformed_order = {
                                'id': order['id'],
                'date': order['created_at'],
                'status': order['status'],
                                'total': order['total'],
                                'customer': {
                    'name': user.get('full_name', ''),
                    'email': user.get('email', ''),
                    'phone': user.get('phone_number', ''),
                    'address': user.get('shipping_address', '')
                },
                'items': [{
                    'name': item['products']['name'],
                                        'price': item['price_at_time'],
                                        'quantity': item['quantity'],
                    'image': item['products'].get('image_url', '')
                } for item in order_items]
            }
            orders.append(transformed_order)
        return jsonify(orders)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/admin/orders/<id>', methods=['PATCH', 'DELETE'])
def admin_order(id):
    try:
        if request.method == 'DELETE':
                    # First delete related order items
            supabase.table('order_items').delete().eq('order_id', id).execute()
                    # Then delete the order
            supabase.table('orders').delete().eq('id', id).execute()
                    return jsonify({'message': 'Order deleted successfully'})
        
        # PATCH request for updating order status
        data = request.json
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
            
        # Update order status
                    response = supabase.table('orders').update({
            'status': data['status']
        }).eq('id', id).execute()

                    if not response.data:
                        return jsonify({'error': 'Order not found'}), 404

        return jsonify(response.data[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Serve static files
@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/admin/<path:path>')
def serve_admin(path):
    return send_from_directory('admin', path)

@app.route('/users/<path:path>')
def serve_users(path):
    return send_from_directory('users', path)

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)
