const SUPABASE_CONFIG = {
    url: import.meta.env.VITE_SUPABASE_URL || 'your_supabase_url',
    anonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || 'your_supabase_anon_key'
};

// Prevent modification of the config
Object.freeze(SUPABASE_CONFIG);

// Export the config
export default SUPABASE_CONFIG; 