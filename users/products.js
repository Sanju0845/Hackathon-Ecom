let cart = {};
let products = []; // Store products globally
let filteredProducts = []; // Store filtered products

// Initialize cart with localStorage fallback
try {
    cart = JSON.parse(localStorage.getItem('cart')) || {};
} catch (error) {
    console.error('Error loading cart from localStorage:', error);
    // Continue with empty cart
}

async function loadProducts() {
    const productsGrid = document.getElementById('productsGrid');
    try {
        productsGrid.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                <span class="material-icons-round" style="font-size: 3rem; margin-bottom: 1rem;">hourglass_empty</span>
                <p>Loading products...</p>
            </div>
        `;
        
        const response = await fetch('/api/products');
        if (!response.ok) {
            throw new Error('Failed to load products');
        }
        
        const data = await response.json();
        
        // Check if response is an error object
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Ensure products is an array
        products = Array.isArray(data) ? data : [];
        filteredProducts = [...products];
        
        if (products.length === 0) {
            productsGrid.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                    <span class="material-icons-round" style="font-size: 3rem; margin-bottom: 1rem;">inventory</span>
                    <p>No products available</p>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem;">Please check back later or contact the administrator.</p>
                </div>
            `;
            return;
        }
        
        displayProducts(filteredProducts);
        updateCartCount();
    } catch (error) {
        console.error('Error loading products:', error);
        productsGrid.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--danger);">
                <span class="material-icons-round" style="font-size: 3rem; margin-bottom: 1rem;">error_outline</span>
                <p>Failed to load products: ${error.message}</p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem;">Please try again later.</p>
                <button onclick="loadProducts()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: var(--primary); color: white; border: none; border-radius: 8px; cursor: pointer;">
                    <span class="material-icons-round" style="font-size: 1rem; margin-right: 0.5rem;">refresh</span>
                    Retry
                </button>
            </div>
        `;
    }
}

function saveCart() {
    try {
        localStorage.setItem('cart', JSON.stringify(cart));
    } catch (error) {
        console.error('Error saving cart to localStorage:', error);
        // Show a warning to user about cart persistence
        const warning = document.createElement('div');
        warning.style.cssText = `
            position: fixed;
            bottom: 1rem;
            right: 1rem;
            background: var(--danger);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            z-index: 1000;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        `;
        warning.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span class="material-icons-round">warning</span>
                <strong>Warning</strong>
            </div>
            <p style="font-size: 0.875rem;">Your cart cannot be saved between sessions. Please complete your purchase in this session.</p>
        `;
        document.body.appendChild(warning);
        setTimeout(() => warning.remove(), 5000);
    }
}

async function updateCartDisplay() {
    const cartItems = document.getElementById('cartItems');
    const cartTotal = document.getElementById('cartTotal');
    
    try {
        if (!checkLogin()) {
            cartItems.innerHTML = `
                <div class="empty-cart">
                    <span class="material-icons-round">shopping_cart</span>
                    <p>Please log in to view your cart</p>
                </div>
            `;
            cartTotal.textContent = '$0.00';
            updateCartCount();
            return;
        }

        // Get cart items from localStorage (try both storage keys)
        let cartData = JSON.parse(localStorage.getItem('cart') || '{}');
        if (Object.keys(cartData).length === 0) {
            cartData = JSON.parse(localStorage.getItem('cartItems') || '{}');
        }
        
        if (Object.keys(cartData).length === 0) {
            cartItems.innerHTML = `
                <div class="empty-cart">
                    <span class="material-icons-round">shopping_cart</span>
                    <p>Your cart is empty</p>
                </div>
            `;
            cartTotal.textContent = '$0.00';
            updateCartCount();
            return;
        }

        let total = 0;
        const cartHTML = Object.entries(cartData).map(([productId, quantity]) => {
            const product = products.find(p => p.id && p.id.toString() === productId.toString());
            if (!product) return '';
            
            const itemTotal = parseFloat(product.price) * parseInt(quantity);
            total += itemTotal;

            return `
                <div class="cart-item" data-product-id="${productId}">
                    <div class="cart-item-image">
                        <img src="${product.image || 'https://via.placeholder.com/300'}" alt="${product.name}">
                    </div>
                    <div class="cart-item-details">
                        <div class="cart-item-name">${product.name}</div>
                        <div class="cart-item-price">$${parseFloat(product.price).toFixed(2)} × ${quantity}</div>
                        <div class="cart-item-total">Total: $${itemTotal.toFixed(2)}</div>
                        <div class="cart-item-quantity">
                            <button class="cart-quantity-btn" onclick="updateCartQuantity('${productId}', ${quantity - 1})">
                                <span class="material-icons-round">remove</span>
                            </button>
                            <span class="quantity">${quantity}</span>
                            <button class="cart-quantity-btn" onclick="updateCartQuantity('${productId}', ${quantity + 1})">
                                <span class="material-icons-round">add</span>
                            </button>
                        </div>
                        <button class="cart-item-remove" onclick="removeFromCart('${productId}')">
                            <span class="material-icons-round">delete</span>
                            Remove
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        cartItems.innerHTML = cartHTML;
        cartTotal.textContent = `$${total.toFixed(2)}`;
        updateCartCount();
    } catch (error) {
        console.error('Error updating cart display:', error);
        cartItems.innerHTML = `
            <div class="empty-cart">
                <span class="material-icons-round">error_outline</span>
                <p>Error loading cart items</p>
            </div>
        `;
        cartTotal.textContent = '$0.00';
    }
}

function updateCartCount() {
    try {
        const cartData = JSON.parse(localStorage.getItem('cartItems') || '{}');
        const count = Object.values(cartData).reduce((sum, quantity) => sum + parseInt(quantity), 0);
        const cartCount = document.querySelector('.cart-count');
        if (cartCount) {
            cartCount.textContent = count.toString();
            cartCount.style.display = count > 0 ? 'block' : 'none';
        }
    } catch (error) {
        console.error('Error updating cart count:', error);
        const cartCount = document.querySelector('.cart-count');
        if (cartCount) {
            cartCount.textContent = '0';
            cartCount.style.display = 'none';
        }
    }
}

// Function to check if user is logged in
function checkLogin() {
    const isAuthenticated = localStorage.getItem('isAuthenticated');
    const userData = localStorage.getItem('user_data');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    // Check both new and old auth methods
    if ((!isAuthenticated && !userData) && !user.id) {
        return false;
    }
    return true;
}

// Function to get user ID
function getUserId() {
    const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return userData.id || user.id;
}

async function addToCart(productId, event) {
    try {
        if (!event) {
            console.error('Event object is missing');
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        
        const user = JSON.parse(localStorage.getItem('user'));
        
        // Check if user is logged in
        if (!user || !user.token) {
            // Store the current URL and pending cart action
            localStorage.setItem('redirectAfterLogin', window.location.href);
            localStorage.setItem('pendingCartAction', JSON.stringify({
                action: 'add',
                productId: productId
            }));
            window.location.href = '/auth/login.html';
            return;
        }

        const product = products.find(p => p.id && p.id.toString() === productId.toString());
        if (!product) {
            console.error('Product not found:', productId);
            return;
        }

        const quantityElement = document.getElementById(`quantity-${productId}`);
        const quantity = quantityElement ? parseInt(quantityElement.textContent) || 1 : 1;

        // Make API call to add to cart
        const response = await fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${user.token}`
            },
            body: JSON.stringify({
                user_id: user.id,
                product_id: productId,
                quantity: quantity
            })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Failed to add to cart');
        }

        // Visual feedback
        const addButton = event.target.closest('.add-to-cart') || event.target;
        const originalText = addButton.innerHTML;
        addButton.innerHTML = '<span class="material-icons-round">check</span>Added to Cart';
        addButton.style.background = 'var(--secondary)';
        
        setTimeout(() => {
            addButton.innerHTML = originalText;
            addButton.style.background = '';
        }, 1500);

        // Update cart display
        await updateCartDisplay();
        
        // Open cart
        openCart();

    } catch (error) {
        console.error('Error adding to cart:', error);
        if (error.message.includes('authentication') || error.message.includes('unauthorized')) {
            localStorage.removeItem('user');
            window.location.href = '/auth/login.html';
            return;
        }
        alert('Failed to add item to cart. Please try again.');
    }
}

async function updateCartQuantity(productId, newQuantity) {
    try {
        const userId = localStorage.getItem('userId');
        if (!userId) {
            alert('Please log in to update cart');
            return;
        }

        if (newQuantity < 1) {
            await removeFromCart(productId);
            return;
        }

        const response = await fetch(`/api/cart/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: newQuantity,
                replace: true // Replace existing quantity
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update cart');
        }

        await updateCartDisplay();
    } catch (error) {
        console.error('Error updating cart quantity:', error);
        alert(error.message);
    }
}

async function removeFromCart(productId) {
    try {
        const userId = localStorage.getItem('userId');
        if (!userId) {
            alert('Please log in to remove items');
            return;
        }

        const response = await fetch(`/api/cart/${userId}/${productId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to remove item from cart');
        }

        await updateCartDisplay();
    } catch (error) {
        console.error('Error removing item from cart:', error);
        alert(error.message);
    }
}

function checkout() {
    // Get cart data from both possible storage locations
    let cartData = JSON.parse(localStorage.getItem('cart') || '{}');
    if (Object.keys(cartData).length === 0) {
        cartData = JSON.parse(localStorage.getItem('cartItems') || '{}');
    }
    
    if (Object.keys(cartData).length === 0) {
        alert('Your cart is empty!');
        return;
    }
    
    // Convert cart data for checkout
    const checkoutItems = Object.entries(cartData).map(([productId, quantity]) => {
        const product = products.find(p => p.id.toString() === productId.toString());
        if (!product) return null;
        return {
            id: productId,
            name: product.name,
            price: product.price,
            quantity: quantity,
            image: product.image || product.image_url || 'https://via.placeholder.com/300'
        };
    }).filter(item => item !== null);

    if (checkoutItems.length === 0) {
        alert('Error preparing checkout. Please try again.');
        return;
    }

    // Save checkout items
    localStorage.setItem('checkoutItems', JSON.stringify(checkoutItems));
    
    // Redirect to billing page
    window.location.href = 'billing.html';
}

function openCart() {
    document.getElementById('cartPanel').classList.add('active');
    document.getElementById('cartOverlay').classList.add('active');
    updateCartDisplay();
}

function closeCart() {
    document.getElementById('cartPanel').classList.remove('active');
    document.getElementById('cartOverlay').classList.remove('active');
}

function sortProducts(sortBy) {
    const sorted = [...filteredProducts];
    switch (sortBy) {
        case 'price-asc':
            sorted.sort((a, b) => a.price - b.price);
            break;
        case 'price-desc':
            sorted.sort((a, b) => b.price - a.price);
            break;
        case 'name-asc':
            sorted.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'name-desc':
            sorted.sort((a, b) => b.name.localeCompare(a.name));
            break;
        default:
            // Featured - keep original order
            break;
    }
    displayProducts(sorted);
}

function filterByCategory(category) {
    // Remove active class from all categories
    document.querySelectorAll('.category-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to clicked category
    event.currentTarget.classList.add('active');

    // For demo, always show all products regardless of category
    filteredProducts = [...products];
    displayProducts(filteredProducts);
}

function displayProducts(productsToShow) {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsToShow || !Array.isArray(productsToShow)) {
        console.error('Invalid products data:', productsToShow);
        return;
    }

    const productsHTML = productsToShow.map(product => `
        <div class="product-card" onclick="openProductDetails(${JSON.stringify(product).replace(/"/g, '&quot;')})">
            <div class="product-image">
                <img src="${product.image || 'https://via.placeholder.com/300'}" alt="${product.name}" 
                     onerror="this.src='https://via.placeholder.com/300'">
            </div>
            <div class="product-info">
                <h3 class="product-name">${product.name}</h3>
                <p class="product-description">${product.description}</p>
                    <div class="product-price">$${parseFloat(product.price).toFixed(2)}</div>
                <div class="product-stock ${product.stock < 5 ? 'low-stock' : ''}">
                    ${product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
                </div>
                <div class="product-actions">
                <div class="quantity-controls">
                        <button onclick="updateQuantity('${product.id}', -1, event)" 
                                class="quantity-btn" ${product.stock === 0 ? 'disabled' : ''}>
                        <span class="material-icons-round">remove</span>
                    </button>
                        <span id="quantity-${product.id}" class="quantity">1</span>
                        <button onclick="updateQuantity('${product.id}', 1, event)" 
                                class="quantity-btn" ${product.stock === 0 ? 'disabled' : ''}>
                        <span class="material-icons-round">add</span>
                    </button>
                </div>
                    <button onclick="addToCart('${product.id}', event)" 
                            class="add-to-cart" ${product.stock === 0 ? 'disabled' : ''}>
                    <span class="material-icons-round">add_shopping_cart</span>
                    Add to Cart
                </button>
                </div>
            </div>
        </div>
    `).join('');

    productsGrid.innerHTML = productsHTML;
}

function updateQuantity(productId, change, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const quantityElement = document.getElementById(`quantity-${productId}`);
    if (!quantityElement) return;

    const product = products.find(p => p.id && p.id.toString() === productId.toString());
    if (!product) return;

    let quantity = parseInt(quantityElement.textContent) || 1;
    quantity = Math.max(1, quantity + change);

    // Check stock limit
    if (quantity > product.stock) {
        const errorMsg = document.createElement('div');
        errorMsg.style.cssText = `
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--danger);
            color: white;
            padding: 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            white-space: nowrap;
            pointer-events: none;
            z-index: 10;
        `;
        errorMsg.textContent = 'Maximum stock reached';
        
        const controls = quantityElement.closest('.quantity-controls');
        if (controls) {
            controls.style.position = 'relative';
            controls.appendChild(errorMsg);
            setTimeout(() => errorMsg.remove(), 2000);
        }
        return;
    }

    quantityElement.textContent = quantity;
}

function openProductDetails(product) {
    const modal = document.getElementById('productDetailsModal');
    const iframe = document.getElementById('productDetailsFrame');
    
    // Show the modal
    modal.style.display = 'block';
    setTimeout(() => modal.classList.add('active'), 10);
    
    // Send product data to iframe
    iframe.onload = () => {
        iframe.contentWindow.postMessage(product, '*');
    };
    
    // Set iframe source if not already set
    if (!iframe.src.includes('productpage.html')) {
        iframe.src = 'productpage.html';
    } else {
        iframe.contentWindow.postMessage(product, '*');
    }
}

// Listen for messages from the product details iframe
window.addEventListener('message', (event) => {
    if (event.data === 'closeProductPage') {
        closeProductDetails();
    } else if (event.data === 'updateCart') {
        updateCartDisplay();
    }
});

function closeProductDetails() {
    const modal = document.getElementById('productDetailsModal');
    modal.classList.remove('active');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

// Update user info in account dropdown
function updateUserInfo() {
    const userName = document.getElementById('userName');
    const userEmail = document.getElementById('userEmail');
    
    try {
        const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
    
        if (userData.name) {
            userName.textContent = userData.name;
        } else if (userData.email) {
            userName.textContent = userData.email;
    } else {
        userName.textContent = 'Guest User';
    }
    
        if (userData.email) {
            userEmail.textContent = userData.email;
    } else {
            userEmail.textContent = 'Signed in';
        }
    } catch (error) {
        console.error('Error updating user info:', error);
        userName.textContent = 'Guest User';
        userEmail.textContent = 'Signed in';
    }
}

// Account dropdown functionality
function toggleAccountMenu() {
    const dropdown = document.getElementById('accountDropdown');
    dropdown.classList.toggle('active');
    
    // Update user info when opening dropdown
    if (dropdown.classList.contains('active')) {
        updateUserInfo();
    }

    // Close dropdown when clicking outside
    const closeDropdown = (e) => {
        if (!e.target.closest('.account-icon')) {
            dropdown.classList.remove('active');
            document.removeEventListener('click', closeDropdown);
        }
    };

    // Add event listener with a slight delay to prevent immediate closure
    setTimeout(() => {
        document.addEventListener('click', closeDropdown);
    }, 0);
}

function logout() {
    // Clear all auth data
    localStorage.clear();
    
    // Show logout feedback
    const feedback = document.createElement('div');
    feedback.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--bg-primary);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: var(--card-shadow);
        text-align: center;
        z-index: 2000;
    `;
    feedback.innerHTML = `
        <span class="material-icons-round" style="font-size: 3rem; color: var(--primary); margin-bottom: 1rem;">check_circle</span>
        <p style="margin-bottom: 1rem;">Successfully logged out!</p>
        <p style="color: var(--text-secondary);">Redirecting to login...</p>
    `;
    document.body.appendChild(feedback);

    // Redirect to login page after a short delay
    setTimeout(() => {
        window.location.href = '../auth/login.html';
    }, 1500);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Load products first
        await loadProducts();
        
        // Then check login and update cart
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (user && user.token) {
            await Promise.all([
                updateCartDisplay(),
                updateCartCount()
            ]);
            updateUserInfo();
        }
        
    } catch (error) {
        console.error('Error during initialization:', error);
    }
});

// Update cart when storage changes
window.addEventListener('storage', async (e) => {
    console.log('Storage event:', e.key, e.newValue);
    if (e.key === 'user') {
        await updateCartCount();
        await updateCartDisplay();
    }
});

// Function to handle login success
window.handleLoginSuccess = function(userData) {
    console.log('Login successful:', userData);
    localStorage.setItem('user', JSON.stringify(userData));
    updateCartDisplay();
};

// Add click handlers for categories
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.category-item').forEach(item => {
        item.addEventListener('click', () => {
            filterByCategory(item.textContent.trim());
        });
    });
});