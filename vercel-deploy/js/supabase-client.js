import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = 'https://puwefvbaowdflcidyzto.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1d2VmdmJhb3dkZmxjaWR5enRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwOTcyODcsImV4cCI6MjA2MzY3MzI4N30.TpZ8rmEP8rPHH66fmB_NJxAceXMoPHmD9DJpCc17cjE'

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