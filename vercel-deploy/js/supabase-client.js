import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = 'https://qvxeqkzskzkglbsghhfx.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2eGVxa3pza3prZ2xic2doaGZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg2ODY3NzEsImV4cCI6MjA2NDI2Mjc3MX0.PmQXBYV4SDZtnCwUgRRDtu6wtD6h8TohtyPN4XTEsyA'

export const supabase = createClient(supabaseUrl, supabaseKey)

// Auth functions
export const signUp = async (email, password) => {
    const { data, error } = await supabase.auth.signUp({
        email,
        password
    })
    return { data, error }
}

export const signIn = async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
    })
    return { data, error }
}

export const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    return { error }
}

// Database functions
export const getProducts = async () => {
    const { data, error } = await supabase
        .from('products')
        .select('*')
    return { data, error }
}

export const getOrders = async (userId) => {
    const { data, error } = await supabase
        .from('orders')
        .select('*')
        .eq('user_id', userId)
    return { data, error }
}

export const createOrder = async (orderData) => {
    const { data, error } = await supabase
        .from('orders')
        .insert([orderData])
        .select()
    return { data, error }
}

export const updateCart = async (userId, cartData) => {
    const { data, error } = await supabase
        .from('cart')
        .upsert({ user_id: userId, items: cartData })
        .select()
    return { data, error }
}

export const getCart = async (userId) => {
    const { data, error } = await supabase
        .from('cart')
        .select('*')
        .eq('user_id', userId)
        .single()
    return { data, error }
}

// User profile functions
export const updateUserProfile = async (userId, profileData) => {
    const { data, error } = await supabase
        .from('profiles')
        .upsert({ user_id: userId, ...profileData })
        .select()
    return { data, error }
}

export const getUserProfile = async (userId) => {
    const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('user_id', userId)
        .single()
    return { data, error }
} 