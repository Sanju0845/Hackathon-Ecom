from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client
import os
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# JWT Secret Key
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')  # In production, always use environment variable

# Supabase configuration
supabase = create_client(
    os.getenv('SUPABASE_URL', 'https://puwefvbaowdflcidyzto.supabase.co'),
    os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1d2VmdmJhb3dkZmxjaWR5enRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwOTcyODcsImV4cCI6MjA2MzY3MzI4N30.TpZ8rmEP8rPHH66fmB_NJxAceXMoPHmD9DJpCc17cjE')
)

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

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    try:
        # Check if user already exists
        existing_user = supabase.table('users').select("*").eq('email', data['email']).execute()
        if existing_user.data:
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user with only the fields we have in our schema
        user_data = {
            'email': data['email'],
            'password': data['password'],
            'name': data.get('name', '')
        }
        
        # Add optional fields only if they exist in the request
        if 'phone' in data:
            user_data['phone'] = data['phone']
        if 'address' in data:
            user_data['address'] = data['address']
        
        response = supabase.table('users').insert(user_data).execute()
        
        if response.data:
            user = response.data[0]
            return jsonify({
                'id': user['id'],
                'email': user['email'],
                'name': user.get('name', ''),
                'phone': user.get('phone', ''),
                'address': user.get('address', '')
            })
        return jsonify({'error': 'Failed to create user'}), 400
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

        # Check if it's an admin login
        if data['email'] == 'admin@gmail.com' and data['password'] == 'admin':
            admin_data = {
                'id': 'admin',
                'email': 'admin@gmail.com',
                'name': 'Admin',
                'is_admin': True,
                'role': 'admin'
            }
            token = generate_token(admin_data)
            if not token:
                return jsonify({'error': 'Failed to generate token'}), 500
            admin_data['token'] = token
            return jsonify(admin_data)
        
        # Regular user login
        try:
            response = supabase.table('users').select("*").eq('email', data['email']).eq('password', data['password']).execute()
            
            if not response.data:
                return jsonify({'error': 'Invalid credentials'}), 401
                
            user = response.data[0]
            token = generate_token(user)
            if not token:
                return jsonify({'error': 'Failed to generate token'}), 500

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
            return jsonify({'error': 'Database error occurred'}), 500
            
    except Exception as e:
        print('Login error:', str(e))
        return jsonify({'error': 'An unexpected error occurred'}), 500

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

@app.route('/api/cart/<item_id>', methods=['PUT'])
def update_cart_item(item_id):
    # Verify token
    token = get_token_from_header()
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        data = request.json
        if 'quantity' not in data:
            return jsonify({'error': 'Quantity is required'}), 400

        # Get cart item with product details
        cart_item = supabase.table('cart_items')\
            .select("*, products(*)")\
            .eq('id', item_id)\
            .execute()

        if not cart_item.data:
            return jsonify({'error': 'Cart item not found'}), 404

        # Verify user owns this cart item
        if cart_item.data[0]['user_id'] != payload['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403

        # Check stock availability
        product = cart_item.data[0]['products']
        if data['quantity'] > product['stock']:
            return jsonify({'error': 'Not enough stock available'}), 400

        # Update quantity
        supabase.table('cart_items')\
            .update({'quantity': data['quantity']})\
            .eq('id', item_id)\
            .execute()

        return jsonify({'message': 'Cart updated'})
    except Exception as e:
        print('Update cart error:', str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/api/cart/remove/<item_id>', methods=['POST'])
def remove_from_cart(item_id):
    # Verify token
    token = get_token_from_header()
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

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
                'category': data.get('category', 'other'),  # Default category
                'stock': data.get('stock', 0)
            }).execute()
            return jsonify(response.data[0] if response.data else {'error': 'Failed to create product'})

        # Add support for category filter in GET request
        category = request.args.get('category')
        query = supabase.table('products').select("*")
        
        if category and category != 'all':
            query = query.eq('category', category)
            
        response = query.execute()
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

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Server running at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True) 