-- Enable UUID extension if not already enabled
-- Used by uuid_generate_v4() and gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- For gen_random_uuid()

-- Drop tables with CASCADE to handle foreign key dependencies
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;

-- Create Tables in correct order (independent tables first)

-- 1. Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create categories table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    image_url TEXT,
    category_id UUID REFERENCES categories(id),
    images TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create user_profiles table
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    total DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    payment_method VARCHAR(50),
    upi_id VARCHAR(100),
    items JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Create order_items table
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price_at_time DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Create cart_items table
CREATE TABLE cart_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

-- 8. Create reviews table
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_name VARCHAR(255) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_cart_items_user_product ON cart_items(user_id, product_id);

-- Insert default categories
INSERT INTO categories (name, description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Clothing', 'Fashion and apparel'),
('Home & Kitchen', 'Home goods and kitchen appliances'),
('Books', 'Books and publications'),
('Sports', 'Sports equipment and accessories'),
('Beauty', 'Beauty and personal care products'),
('Toys', 'Toys and games'),
('Other', 'Miscellaneous items');

-- Create admin user (password should be hashed in the application)
INSERT INTO users (email, password, name) VALUES
('admin@gmail.com', 'admin', 'Admin User');

-- Create admin profile
INSERT INTO user_profiles (user_id, name, phone, address)
SELECT id, 'Admin User', '', 'Admin Address'
FROM users WHERE email = 'admin@gmail.com';

-- Insert sample products
INSERT INTO products (name, description, price, stock, image_url, category_id, images) 
SELECT 
    'iPhone 13 Pro',
    'Latest Apple iPhone with amazing camera and performance',
    999.99,
    50,
    'https://example.com/iphone13.jpg',
    id,
    ARRAY['https://example.com/iphone13_1.jpg', 'https://example.com/iphone13_2.jpg']
FROM categories WHERE name = 'Electronics';

INSERT INTO products (name, description, price, stock, image_url, category_id, images) 
SELECT 
    'Nike Air Max',
    'Comfortable running shoes with great support',
    129.99,
    100,
    'https://example.com/nike.jpg',
    id,
    ARRAY['https://example.com/nike_1.jpg', 'https://example.com/nike_2.jpg']
FROM categories WHERE name = 'Sports';

INSERT INTO products (name, description, price, stock, image_url, category_id, images) 
SELECT 
    'Smart Watch',
    'Track your fitness and stay connected',
    199.99,
    75,
    'https://example.com/watch.jpg',
    id,
    ARRAY['https://example.com/watch_1.jpg', 'https://example.com/watch_2.jpg']
FROM categories WHERE name = 'Electronics';

INSERT INTO products (name, description, price, stock, image_url, category_id, images) 
SELECT 
    'Coffee Maker',
    'Automatic coffee maker with timer',
    79.99,
    30,
    'https://example.com/coffee.jpg',
    id,
    ARRAY['https://example.com/coffee_1.jpg', 'https://example.com/coffee_2.jpg']
FROM categories WHERE name = 'Home & Kitchen';

INSERT INTO products (name, description, price, stock, image_url, category_id, images) 
SELECT 
    'Wireless Earbuds',
    'High-quality sound with noise cancellation',
    149.99,
    60,
    'https://example.com/earbuds.jpg',
    id,
    ARRAY['https://example.com/earbuds_1.jpg', 'https://example.com/earbuds_2.jpg']
FROM categories WHERE name = 'Electronics'; 