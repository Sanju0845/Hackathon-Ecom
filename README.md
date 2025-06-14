# Online Store

A web-based e-commerce platform built with Python and HTML/CSS/JavaScript.

## Features

-   Product catalog
-   Shopping cart functionality
-   User authentication
-   Order management
-   Admin dashboard

## Technologies Used

-   **Backend**: Python, Flask
-   **Frontend**: HTML, CSS, JavaScript
-   **Database**: Supabase
-   **Authentication**: JWT, bcrypt

## Setup

1.  Clone the repository

    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  Install Python dependencies

    ```bash
    pip install -r requirements.txt
    ```

3.  Set up Supabase:

    -   Create a new project on Supabase ([https://supabase.com/](https://supabase.com/))
    -   Update the `.env` file with your Supabase URL and API key

        ```
        SUPABASE_URL=<your_supabase_url>
        SUPABASE_KEY=<your_supabase_key>
        JWT_SECRET=<your_jwt_secret>
        ADMIN_EMAIL=<your_admin_email>
        ADMIN_PASSWORD=<your_admin_password>
        ```

4.  Run the server:

    ```bash
    python server.py
    ```

5.  Open `index.html` in your browser

## Database Setup

The application uses Supabase for data storage. The database schema is defined in `css/database/schema.sql`. You can use this file to create the necessary tables and relationships in your Supabase project.

## API Endpoints

The server exposes the following API endpoints:

-   `POST /api/register`: Registers a new user
-   `POST /api/login`: Logs in an existing user
-   `POST /api/admin/login`: Logs in an admin user
-   `GET /api/products`: Retrieves a list of products
-   `GET /api/products/<id>`: Retrieves a single product by ID
-   `GET /api/cart`: Retrieves the user's shopping cart
-   `POST /api/cart/add`: Adds a product to the user's shopping cart
-   `PUT /api/cart/update/<item_id>`: Updates the quantity of an item in the user's shopping cart
-   `DELETE /api/cart/remove/<item_id>`: Removes an item from the user's shopping cart
-   `DELETE /api/cart/clear`: Clears the user's shopping cart
-   `POST /api/checkout`: Creates a new order
-   `GET /api/orders`: Retrieves a list of orders
-   `GET /api/admin/products`: Retrieves a list of all products (Admin only)
-   `POST /api/admin/products`: Creates a new product (Admin only)
-   `PUT /api/admin/products/<id>`: Updates an existing product (Admin only)
-   `DELETE /api/admin/products/<id>`: Deletes a product (Admin only)
-   `GET /api/admin/orders`: Retrieves all orders with customer and item details (Admin only)
-   `PATCH /api/admin/orders/<id>`: Updates the status of an existing order (Admin only)
-   `DELETE /api/admin/orders/<id>`: Deletes an order (Admin only)

## Project Structure

-   `server.py`: Backend server
-   `index.html`: Main frontend page
-   `assets/`: Static assets (images, etc.)
-   `admin/`: Admin dashboard files
-   `auth/`: Authentication-related files (login, signup)
-   `css/`: CSS stylesheets
-   `js/`: JavaScript files


## License

[MIT](LICENSE)