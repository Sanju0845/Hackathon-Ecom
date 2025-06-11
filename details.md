# Project Presentation Details: Online Store Server (server.py)

## Overview

This document provides a detailed overview of the `server.py` file, which serves as the backend for an online store application. It's built using Flask, a Python web framework, and interacts with a Supabase database for data storage and retrieval.

## Modules Used

*   **flask**: Core framework for building web applications.
    *   `Flask`: Class for creating the Flask application instance.
    *   `request`: Object to access incoming request data (headers, body, parameters).
    *   `jsonify`: Function to convert Python dictionaries into JSON responses.
    *   `send_from_directory`: Function to serve static files (HTML, CSS, JavaScript).
*   **flask\_cors**: Handles Cross-Origin Resource Sharing (CORS) to allow requests from different domains.
    *   `CORS`: Enables CORS for the Flask app.
*   **supabase**: Library for interacting with the Supabase database.
    *   `create_client`: Function to initialize a Supabase client.
*   **os**: Provides a way to interact with the operating system, mainly used for environment variables.
*   **dotenv**: Loads environment variables from a `.env` file.
    *   `load_dotenv`: Loads the environment variables.
*   **jwt**: Library for working with JSON Web Tokens (JWTs) for authentication.
    *   `jwt.encode`: Creates a JWT.
    *   `jwt.decode`: Decodes a JWT.
    *   `jwt.ExpiredSignatureError`: Exception for expired tokens.
    *   `jwt.InvalidTokenError`: Exception for invalid tokens.
*   **datetime**: Provides classes for working with dates and times.
    *   `datetime`: Class for representing dates and times.
    *   `timedelta`: Class for representing time differences.
*   **bcrypt**: Library for hashing passwords.
    *   `bcrypt.hashpw`: Hashes a password.
    *   `bcrypt.gensalt`: Generates a salt for password hashing.
*   **flask**: Provides a way to store data that is globally available to each request.
    *   `g`: Object to store data during a request context.

## Environment Variables

The application relies on several environment variables for configuration:

*   `JWT_SECRET`: Secret key used to sign and verify JWTs.  Defaults to `'your-secret-key'` if not set, but should ALWAYS be set in production.
*   `SUPABASE_URL`: URL of the Supabase project.
*   `SUPABASE_KEY`: API key for the Supabase project.
*   `ADMIN_EMAIL`: Email address for the admin user.
*   `ADMIN_PASSWORD`: Password for the admin user.

## Helper Functions

*   **generate\_token(user\_data)**: Generates a JWT token for a given user.  The token includes the user ID, email, and an expiration time (1 day).
*   **verify\_token(token)**: Verifies a JWT token.  It decodes the token and returns the payload if the token is valid. It handles expired and invalid tokens.
*   **get\_token\_from\_header()**: Extracts the JWT token from the `Authorization` header of the request.  It expects the header to be in the format `Bearer <token>`.
*   **hash\_password(password)**: Hashes a password using bcrypt for secure storage.

## Endpoints

The server exposes the following API endpoints:

### Authentication Routes

*   **POST /api/register**: Registers a new user.
    *   Receives user details (email, password, name, phone, address) in JSON format.
    *   Validates input data.
    *   Hashes the password using bcrypt.
    *   Inserts the user data into the `users` table in Supabase.
    *   Creates a user profile in the `user_profiles` table.
    *   Generates a JWT token for the new user.
    *   Returns the user data along with the token.
*   **POST /api/login**: Logs in an existing user.
    *   Receives user credentials (email, password) in JSON format.
    *   Authenticates the user against the `users` table in Supabase.
    *   Verifies the password using bcrypt.
    *   Generates a JWT token for the user.
    *   Returns the user data along with the token.
*   **POST /api/admin/login**: Logs in an admin user.
    *   Receives admin credentials (email, password) in JSON format.
    *   Validates the credentials against the `ADMIN_EMAIL` and `ADMIN_PASSWORD` environment variables.
    *   Generates a JWT token with admin-specific claims.
    *   Returns the admin data along with the token.

### Product Routes

*   **GET /api/products**: Retrieves a list of products.
    *   Accepts an optional `category` query parameter to filter products by category.
    *   Retrieves product data from the `products` table in Supabase.
    *   Fixes common image URL issues and sets a default image if none is provided.
    *   Returns a JSON array of products.
*   **GET /api/products/<id>**: Retrieves a single product by ID.
    *   Retrieves product data from the `products` table in Supabase.
    *   Returns a JSON object containing the product data.

### Cart Routes

*   **GET /api/cart**: Retrieves the user's shopping cart.
    *   Requires a valid JWT token for authentication.
    *   Retrieves cart items from the `cart_items` table in Supabase, filtered by user ID.
    *   Retrieves product details for each cart item from the `products` table.
    *   Combines cart item data with product details and returns a JSON array.
*   **POST /api/cart/add**: Adds a product to the user's shopping cart.
    *   Requires a valid JWT token for authentication.
    *   Receives the `product_id` in JSON format.
    *   Validates that the product exists and has stock.
    *   If the item is already in the cart, the quantity is updated. Otherwise, a new item is added to the cart.
*   **PUT /api/cart/update/<item\_id>**: Updates the quantity of an item in the user's shopping cart.
    *   Requires a valid JWT token for authentication.
    *   Receives the new `quantity` in JSON format.
    *   Validates that the quantity is valid and does not exceed the available stock.
*   **DELETE /api/cart/remove/<item\_id>**: Removes an item from the user's shopping cart.
    *   Requires a valid JWT token for authentication.
*   **DELETE /api/cart/clear**: Clears the user's shopping cart.
    *   Requires a valid JWT token for authentication.

### Order Routes

*   **POST /api/checkout**: Creates a new order.
    *   Receives order details (user\_id, total, items, name, phone, address, payment details) in JSON format.
    *   Inserts the order data into the `orders` table in Supabase.
    *   Creates order items in the `order_items` table.
    *   Clears the user's shopping cart.
*   **GET /api/orders**: Retrieves a list of orders.
    *   Accepts a `user_id` query parameter to filter orders by user. If the user\_id is "admin", all orders are returned.
    *   Retrieves order data from the `orders` table in Supabase.

### Admin Routes

*   **GET /api/admin/products**: Retrieves a list of all products (Admin only).
*   **POST /api/admin/products**: Creates a new product (Admin only).
*   **PUT /api/admin/products/<id>**: Updates an existing product (Admin only).
*   **DELETE /api/admin/products/<id>**: Deletes a product (Admin only).
*   **GET /api/admin/orders**: Retrieves all orders with customer and item details (Admin only).
*   **PATCH /api/admin/orders/<id>**: Updates the status of an existing order (Admin only).
*   **DELETE /api/admin/orders/<id>**: Deletes an order (Admin only).

### Review Routes

*   **POST   /api/reviews**: Allows users to post a product review.
*   **GET /api/reviews/<product\_id>**: Retrieves all the reviews for a product.
*   **GET /api/reviews/ratings**: Gets all ratings and product IDs.

### Static File Routes

*   **GET /**: Serves the `index.html` file for the root path.
*   **GET /admin/<path:path>**: Serves static files from the `admin` directory.
*   **GET /users/<path:path>**: Serves static files from the `users` directory.
*   **GET /favicon.ico**: Serves the favicon.
*   **GET /<path:path>**: Serves other static files.

## Error Handling & Middleware

*   **Error Handling**: A global error handler is implemented to catch and handle exceptions, returning a JSON response with an error message and a 500 status code.
*   **CORS Middleware**: The `after_request` function adds CORS headers to each response, allowing requests from any origin.

## Server Startup

*   The script initializes a Flask app, configures CORS, and sets up a Supabase client.
*   It retrieves admin credentials from environment variables.
*   It defines several API endpoints for user authentication, product management, cart operations, and order processing.
*   The script includes error handling and middleware for CORS.
*   Finally, it starts the Flask development server on `http://localhost:5000`.