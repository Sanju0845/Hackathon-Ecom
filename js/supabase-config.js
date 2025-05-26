// Your Supabase Project URL and Anon Key
const SUPABASE_URL = 'https://puwefvbaowdflcidyzto.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1d2VmdmJhb3dkZmxjaWR5enRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwOTcyODcsImV4cCI6MjA2MzY3MzI4N30.TpZ8rmEP8rPHH66fmB_NJxAceXMoPHmD9DJpCc17cjE'

// Create Supabase client
const { createClient } = supabase;
const supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Export for use in other files
export { supabaseClient as supabase }; 