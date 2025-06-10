from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client
import os
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta
import bcrypt
from flask import g

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# JWT Secret Key
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')  # In production, always use environment variable

# Supabase configuration
try:
    supabase = create_client(
        os.getenv('SUPABASE_URL', 'https://qvxeqkzskzkglbsghhfx.supabase.co'),
        os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2eGVxa3pza3prZ2xic2doaGZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg2ODY3NzEsImV4cCI6MjA2NDI2Mjc3MX0.PmQXBYV4SDZtnCwUgRRDtu6wtD6h8TohtyPN4XTEsyA')
    )
    print("Supabase client initialized successfully")
except Exception as e:
    print("Error initializing Supabase client:", str(e))
    raise

# Get admin credentials from environment variables
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# ==============================================
# Helper Functions
# ==============================================

def generate_token(user_data):
    """Generate JWT token for user"""
    try:
        token = jwt.encode({
            'user_id': str(user_data.get('id')),  # Convert ID to string
            'email': user_data.get('email'),
            'exp': datetime.utcnow() + timedelta(days=1)
        }, JWT_SECRET, algorithm='HS256')
        return token
    except Exception as e:
        print('Token generation error:', str(e))
        return None

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        print('Token payload:', payload)  # Debug log
        return payload
    except jwt.ExpiredSignatureError:
        print('Token expired')  # Debug log
        return None
    except jwt.InvalidTokenError as e:
        print('Invalid token:', str(e))  # Debug log
        return None
    except Exception as e:
        print('Token verification error:', str(e))  # Debug log
        return None

def get_token_from_header():
    """Extract token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    print('Auth header:', auth_header)  # Debug log
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        print('Extracted token:', token)  # Debug log
        return token
    return None

def hash_password(password):
    """Hash a password for storing."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# ==============================================
# Authentication Routes
# ==============================================

@app.route('/api/register', methods=['POST'])
def register():
    print('Register endpoint called')
    if not request.is_json:
        print('Request is not JSON')
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.json
    print('Received data:', data)
    if not data:
        print('No data provided')
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['email', 'password', 'name']
    for field in required_fields:
        if field not in data:
            print(f'Missing required field: {field}')
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        print('Checking if user exists...')
        check_user = supabase.table('users').select("id").eq('email', data['email']).execute()
        print('User check result:', check_user.data)
        if check_user.data:
            print('Email already exists')
            return jsonify({'error': 'Email already exists'}), 400
        
        print('Hashing password...')
        hashed_password = hash_password(data['password'])
        print('Password hashed')

        print('Creating user...')
        user_data = {
            'email': data['email'],
            'password': hashed_password.decode('utf-8'),  # Store hashed password
            'name': data['name']
        }

        user_response = supabase.table('users').insert([user_data]).execute()
        print('User creation response:', user_response.data)
        if not user_response.data or 'id' not in user_response.data[0]:
            print('Failed to create user')
            return jsonify({'error': 'Failed to create user'}), 400

        user = user_response.data[0]

        print('Creating user profile...')
        profile_data = {
            'user_id': user['id'],
            'name': data['name'],
            'phone': data.get('phone', ''),
            'address': data.get('address', '')
        }

        profile_response = supabase.table('user_profiles').insert(profile_data).execute()
        print('Profile creation response:', profile_response.data)
        if not profile_response.data:
            print('Failed to create user profile, rolling back user')
            # If profile creation fails, delete the user
            supabase.table('users').delete().eq('id', user['id']).execute()
            return jsonify({'error': 'Failed to create user profile'}), 400

        print('Generating token...')
        token = generate_token({
            'id': user['id'],
            'email': user['email']
        })

        if not token:
            print('Failed to generate token')
            return jsonify({'error': 'Failed to generate token'}), 500

        print('Registration successful')
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'name': profile_data['name'],
            'phone': profile_data['phone'],
            'address': profile_data['address'],
            'token': token
        })

    except Exception as e:
        print('Registration error:', str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400

        # Regular user login
        try:
            # First check if user exists
            user_response = supabase.table('users').select("*").eq('email', data['email']).execute()
            
            if not user_response.data:
                return jsonify({'error': 'User not found'}), 401
                
            user = user_response.data[0]
            
            # Verify password
            if not bcrypt.checkpw(data['password'].encode('utf-8'), user.get('password').encode('utf-8')):
                return jsonify({'error': 'Invalid password'}), 401
            
            # Generate token
            token = generate_token(user)
            if not token:
                return jsonify({'error': 'Failed to generate token'}), 500

            # Return user data with token
            return jsonify({
                'id': user['id'],
                'email': user['email'],
                'name': user.get('name', ''),
                'phone': user.get('phone', ''),
                'address': user.get('address', ''),
                'is_admin': False,
                'role': 'user',
                'token': token
            })
            
        except Exception as supabase_error:
            print('Supabase error:', str(supabase_error))
            return jsonify({'error': 'Database error occurred', 'details': str(supabase_error)}), 500
            
    except Exception as e:
        print('Login error:', str(e))
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400

        # Verify admin credentials
        if data['email'] != ADMIN_EMAIL or data['password'] != ADMIN_PASSWORD:
            return jsonify({'error': 'Invalid admin credentials'}), 401

        # Generate admin token with additional security claims
        admin_data = {
            'id': 'admin',
            'email': ADMIN_EMAIL,
            'name': 'Admin',
            'is_admin': True,
            'role': 'admin',
            'admin_access': True,
            'timestamp': datetime.utcnow().timestamp()
        }
        
        token = generate_token(admin_data)
        if not token:
            return jsonify({'error': 'Failed to generate token'}), 500
            
        admin_data['token'] = token
        return jsonify(admin_data)
        
    except Exception as e:
        print('Admin login error:', str(e))
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

# ==============================================
# Product Routes
# ==============================================

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        # Add support for category filter
        category = request.args.get('category')
        query = supabase.table('products').select("*")
        
        if category and category != 'all':
            query = query.eq('category', category)
            
        response = query.execute()
        
        # Fix and validate image URLs
        products = response.data
        for product in products:
            image_url = product.get('image_url', '')
            
            # Fix common URL issues
            if image_url:
                # Fix double 'h' in https
                if image_url.startswith('hhttps://'):
                    image_url = image_url[1:]
                # Fix missing scheme
                elif not image_url.startswith(('http://', 'https://')):
                    image_url = 'https://' + image_url
                
                # Update the image URL
                product['image_url'] = image_url
            else:
                # Set default image if none provided
                product['image_url'] = f'https://via.placeholder.com/300x300?text={product["name"].replace(" ", "+")}'
        
        return jsonify(products)
    except Exception as e:
        print('Error in get_products:', str(e))  # Add logging
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

# ==============================================
# Cart Routes
# ==============================================

@app.route('/api/cart', methods=['GET'])
def get_cart():
    print('GET /api/cart - Headers:', dict(request.headers))  # Debug log
    
    # Verify token
    token = get_token_from_header()
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Special handling for admin user
        if payload.get('user_id') == 'admin':
            return jsonify([])  # Return empty cart for admin

        print('Getting cart for user:', payload['user_id'])  # Debug log
        
        # First get cart items
        cart_response = supabase.table('cart_items')\
            .select('*')\
            .eq('user_id', payload['user_id'])\
            .execute()
            
        if not cart_response.data:
            return jsonify([])
            
        # Get all product IDs from cart items
        product_ids = [item['product_id'] for item in cart_response.data]
        
        # Get product details for all cart items
        products_response = supabase.table('products')\
            .select('*')\
            .in_('id', product_ids)\
            .execute()
            
        # Create a lookup dictionary for products
        products_dict = {product['id']: product for product in products_response.data}
        
        # Combine cart items with product details
        cart_items = []
        for item in cart_response.data:
            if item['product_id'] in products_dict:
                cart_items.append({
                    **item,
                    'products': products_dict[item['product_id']]
                })

        print('Cart response:', cart_items)  # Debug log
        return jsonify(cart_items)
        
    except Exception as e:
        print('Get cart error:', str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    print('POST /api/cart/add - Headers:', dict(request.headers))  # Debug log
    print('Request data:', request.json)  # Debug log
    
    # Verify token
    token = get_token_from_header()
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Special handling for admin user
        if payload.get('user_id') == 'admin':
            return jsonify({'error': 'Admin users cannot add items to cart'}), 403

        data = request.json
        if not data.get('product_id'):
            return jsonify({'error': 'Product ID required'}), 400
        
        print('Adding to cart for user:', payload['user_id'])  # Debug log
        
        # Check if product exists and has stock
        product_response = supabase.table('products').select("*").eq('id', data['product_id']).execute()
        if not product_response.data:
            return jsonify({'error': 'Product not found'}), 404
        
        product = product_response.data[0]
        print('Product found:', product)  # Debug log
        
        if product['stock'] <= 0:
            return jsonify({'error': 'Product out of stock'}), 400

        # Check if item already in cart
        existing_item = supabase.table('cart_items')\
            .select("*")\
            .eq('user_id', payload['user_id'])\
            .eq('product_id', data['product_id'])\
            .execute()
        
        print('Existing cart item:', existing_item.data)  # Debug log
        
        quantity = data.get('quantity', 1)
        
        if existing_item.data:
            # Update quantity if item exists
            new_quantity = existing_item.data[0]['quantity'] + quantity
            if new_quantity > product['stock']:
                return jsonify({'error': 'Not enough stock available'}), 400
                
            print('Updating quantity to:', new_quantity)  # Debug log
            supabase.table('cart_items')\
                .update({'quantity': new_quantity})\
                .eq('id', existing_item.data[0]['id'])\
                .execute()
        else:
            # Add new item if not in cart
            if quantity > product['stock']:
                return jsonify({'error': 'Not enough stock available'}), 400
                
            print('Adding new cart item')  # Debug log
            supabase.table('cart_items').insert({
                'user_id': payload['user_id'],
                'product_id': data['product_id'],
                'quantity': quantity
            }).execute()
        
        return jsonify({'message': 'Added to cart'})
    except Exception as e:
        print('Add to cart error:', str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/api/cart/update/<item_id>', methods=['PUT'])
def update_cart_item(item_id):
    print(f"Received update request for item {item_id}")  # Debug log
    
    # Verify token
    token = get_token_from_header()
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        print("Token verified successfully") # Debug log

        # Special handling for admin user
        if payload.get('user_id') == 'admin':
            return jsonify({'error': 'Admin users cannot update cart'}), 403

        # Get request data
        if not request.is_json:
            print("Request is not JSON")  # Debug log
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        print(f"Request data: {data}")  # Debug log
        
        if not data:
            print("No data provided in request")  # Debug log
            return jsonify({'error': 'No data provided'}), 400
            
        if 'quantity' not in data:
            print("Quantity not provided in request")  # Debug log
            return jsonify({'error': 'Quantity is required'}), 400

        try:
            quantity = int(data['quantity'])
            print(f"Parsed quantity: {quantity}")  # Debug log
            if quantity < 1:
                return jsonify({'error': 'Quantity must be at least 1'}), 400
        except (ValueError, TypeError) as e:
            print(f"Error parsing quantity: {str(e)}")  # Debug log
            return jsonify({'error': 'Invalid quantity value'}), 400

        print("Getting cart item...") # Debug log
        # Get cart item with product details
        try:
            cart_item = supabase.table('cart_items')\
                .select("*, products(*)")\
                .eq('id', item_id)\
                .execute()
                
            print(f"Cart item response: {cart_item.data}")  # Debug log
            print(f"Cart item error: {cart_item.error}") # Debug log

            if not cart_item.data:
                print("Cart item not found")  # Debug log
                return jsonify({'error': 'Cart item not found'}), 404

            # Verify user owns this cart item
            if cart_item.data[0]['user_id'] != payload['user_id']:
                print("Unauthorized access attempt")  # Debug log
                return jsonify({'error': 'Unauthorized'}), 403

            # Check stock availability
            product = cart_item.data[0]['products']
            print(f"Product stock: {product['stock']}")  # Debug log
            
            if quantity > product['stock']:
                return jsonify({'error': 'Not enough stock available'}), 400

            # Update quantity
            try:
                response = supabase.table('cart_items')\
                    .update({'quantity': quantity})\
                    .eq('id', item_id)\
                    .execute()
                    
                print(f"Update response: {response.data}")  # Debug log
                print(f"Update error: {response.error}") # Debug log

                if not response.data:
                    return jsonify({'error': 'Failed to update cart item'}), 500

                return jsonify({
                    'message': 'Cart updated successfully',
                    'updated_item': response.data[0]
                })
            except Exception as update_error:
                print(f"Update failed: {str(update_error)}")
                return jsonify({'error': 'Failed to update cart item'}), 500

        except Exception as db_error:
            print(f"Database error: {str(db_error)}")  # Debug log
            return jsonify({'error': 'Database error occurred'}), 500
            
    except Exception as e:
        print('Update cart error:', str(e))  # Debug log
        return jsonify({'error': str(e)}), 400

@app.route('/api/cart/remove/<item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    # Verify token
    token = get_token_from_header()
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Special handling for admin user
        if payload.get('user_id') == 'admin':
            return jsonify({'error': 'Admin users cannot remove items from cart'}), 403

        # Verify user owns this cart item
        cart_item = supabase.table('cart_items')\
            .select("*")\
            .eq('id', item_id)\
            .execute()

        if cart_item.data and cart_item.data[0]['user_id'] != payload['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403

        # Remove item
        supabase.table('cart_items')\
            .delete()\
            .eq('id', item_id)\
            .execute()

        return jsonify({'message': 'Item removed from cart'})
    except Exception as e:
        print('Remove from cart error:', str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/api/cart/clear', methods=['DELETE'])
def clear_cart():
    # Verify token
    token = get_token_from_header()
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    try:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        # Special handling for admin user
        if payload.get('user_id') == 'admin':
            return jsonify({'error': 'Admin users cannot clear cart'}), 403
        # Delete all cart items for this user
        supabase.table('cart_items').delete().eq('user_id', payload['user_id']).execute()
        return jsonify({'message': 'Cart cleared successfully'})
    except Exception as e:
        print('Clear cart error:', str(e))
        return jsonify({'error': str(e)}), 400

# ==============================================
# Order Routes
# ==============================================

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    try:
        # Create order with exact column names from database schema
        order_data = {
            'user_id': data['user_id'],
            'total': data['total'],
            'status': 'pending',
            'name': data.get('name'),
            'phone': data.get('phone'),
            'address': data.get('address'),
            'payment_method': data.get('payment_method'),
            'upi_id': data.get('upi_id'),
            'items': data.get('items')
        }
        
        order_response = supabase.table('orders').insert(order_data).execute()
                    
        if not order_response.data:
            return jsonify({'error': 'Failed to create order'}), 400
            
        order = order_response.data[0]
        
        # Create order items
        for item in data['items']:
            supabase.table('order_items').insert({
                'order_id': order['id'],
                'product_id': item['product_id'],
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

# ==============================================
# Admin Routes
# ==============================================

@app.route('/api/admin/products', methods=['GET', 'POST'])
def admin_products():
    try:
        if request.method == 'POST':
            data = request.json
            # Accept images as array and image_url as main image
            response = supabase.table('products').insert({
                'name': data['name'],
                'description': data.get('description'),
                'price': data['price'],
                'image_url': data.get('image_url'),
                'images': data.get('images', []),
                'category': data.get('category', 'other'),
                'stock': data.get('stock', 0)
            }).execute()
            return jsonify(response.data[0] if response.data else {'error': 'Failed to create product'})

        # GET request - return all products
        response = supabase.table('products').select("*").execute()
        if not response.data:
            return jsonify([])  # Return empty array if no products
        return jsonify(response.data)
    except Exception as e:
        print('Error in admin_products:', str(e))  # Add logging
        return jsonify({'error': str(e)}), 400

@app.route('/api/admin/products/<id>', methods=['PUT', 'DELETE'])
def admin_product(id):
    try:
        if request.method == 'DELETE':
            try:
                supabase.table('products').delete().eq('id', id).execute()
                return jsonify({'message': 'Product deleted'})
            except Exception as e:
                return jsonify({'error': f'Failed to delete product: {str(e)}'}), 400
        
        data = request.json
        # Accept images as array and image_url as main image
        response = supabase.table('products').update({
            'name': data.get('name'),
            'description': data.get('description'),
            'price': data.get('price'),
            'image_url': data.get('image_url'),
            'images': data.get('images', []),
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
                    'name': user.get('name', ''),
                    'email': user.get('email', ''),
                    'phone': user.get('phone', ''),
                    'address': user.get('address', '')
                },
                'items': [{
                    'name': item['products']['name'],
                    'price': item['products']['price'],  # Use product price instead of price_at_time
                    'quantity': item['quantity'],
                    'image': item['products'].get('image_url', '')
                } for item in order_items]
            }
            orders.append(transformed_order)
        return jsonify(orders)
    except Exception as e:
        print('Error in admin_orders:', str(e))  # Add logging
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

# ==============================================
# Review Routes
# ==============================================

@app.route('/api/reviews', methods=['POST'])
def post_review():
    token = get_token_from_header()
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    try:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        data = request.json
        product_id = data.get('product_id')
        rating = data.get('rating')
        review = data.get('review')
        if not product_id or not rating or not review:
            return jsonify({'error': 'Missing required fields'}), 400
        user_id = payload['user_id']
        user_name = payload.get('name', 'Anonymous')
        review_data = {
            'product_id': product_id,
            'user_id': user_id,
            'user_name': user_name,
            'rating': rating,
            'review': review
        }
        response = supabase.table('reviews').insert([review_data]).execute()
        if not response.data:
            return jsonify({'error': 'Failed to save review'}), 500
        return jsonify({'message': 'Review submitted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/reviews/<product_id>', methods=['GET'])
def get_reviews(product_id):
    try:
        response = supabase.table('reviews').select('*').eq('product_id', product_id).order('created_at', desc=True).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/reviews/ratings', methods=['GET'])
def get_all_product_ratings():
    try:
        # Get average rating and count for each product
        response = supabase.table('reviews').select('product_id, rating').execute()
        ratings = {}
        for r in response.data:
            pid = r['product_id']
            if pid not in ratings:
                ratings[pid] = {'sum': 0, 'count': 0}
            ratings[pid]['sum'] += r['rating']
            ratings[pid]['count'] += 1
        # Calculate average
        result = {pid: {'avg': (v['sum']/v['count']) if v['count'] else 0, 'count': v['count']} for pid, v in ratings.items()}
        return jsonify(result)
    except Exception as e:
        return jsonify({}), 200

# ==============================================
# Static File Routes
# ==============================================

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/admin/<path:path>')
def serve_admin(path):
    return send_from_directory('admin', path)

@app.route('/users/<path:path>')
def serve_users(path):
    return send_from_directory('users', path)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# ==============================================
# Error Handling & Middleware
# ==============================================

@app.errorhandler(Exception)
def handle_error(error):
    print("Server error:", str(error))
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ==============================================
# Server Startup
# ==============================================

if __name__ == '__main__':
    print("Starting Flask server...")
    try:
        # Test Supabase connection
        test_response = supabase.table('users').select("count").limit(1).execute()
        print("Supabase connection test successful")
        
        # Start server
        print("Server running at http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    except Exception as e:
        print("Error starting server:", str(e))
        print("Please check your internet connection and Supabase credentials")
        raise 