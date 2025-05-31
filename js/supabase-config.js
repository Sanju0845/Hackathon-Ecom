// Your Supabase Project URL and 
const SUPABASE_URL = 'https://ldubebcnuxdzolgbrrdm.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxkdWJlYmNudXhkem9sZ2JycmRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg2MjQ0NDEsImV4cCI6MjA2NDIwMDQ0MX0.p-HHjKgR6SynlT67OuPZY5PK5CLzBGDu1AhV5WjvjM4'

// Create Supabase client
const { createClient } = supabase;
const supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Export for use in other files
export { supabaseClient as supabase }; 