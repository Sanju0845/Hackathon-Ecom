// Supabase configuration
export const SUPABASE_CONFIG = {
    url: '', // Add your Supabase project URL
    anonKey: '', // Add your Supabase anon key
    authHeader: 'Authorization',
    storage: {
        tokenKey: 'auth_token',
        userKey: 'user_data'
    }
}; 