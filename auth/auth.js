import { SUPABASE_CONFIG } from './config.js';

// Auth helper functions
export const auth = {
    // Store token and user data
    setSession(token, userData) {
        localStorage.setItem(SUPABASE_CONFIG.storage.tokenKey, token);
        localStorage.setItem(SUPABASE_CONFIG.storage.userKey, JSON.stringify(userData));
    },

    // Clear session data
    clearSession() {
        localStorage.removeItem(SUPABASE_CONFIG.storage.tokenKey);
        localStorage.removeItem(SUPABASE_CONFIG.storage.userKey);
    },

    // Get current token
    getToken() {
        return localStorage.getItem(SUPABASE_CONFIG.storage.tokenKey);
    },

    // Get current user data
    getUserData() {
        const data = localStorage.getItem(SUPABASE_CONFIG.storage.userKey);
        return data ? JSON.parse(data) : null;
    },

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getToken();
    },

    // Check if user is admin
    isAdmin() {
        const userData = this.getUserData();
        return userData ? userData.is_admin : false;
    },

    // Get auth header for API requests
    getAuthHeader() {
        const token = this.getToken();
        return token ? { [SUPABASE_CONFIG.authHeader]: `Bearer ${token}` } : {};
    }
}; 