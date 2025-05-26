import { supabase } from './supabase-config.js'

// Function to fetch all products
async function getProducts() {
    try {
        const { data, error } = await supabase
            .from('products')
            .select('*')
        
        if (error) throw error
        return data
    } catch (error) {
        console.error('Error fetching products:', error)
        return []
    }
}

// Function to add a product (admin only)
async function addProduct(product) {
    try {
        const { data, error } = await supabase
            .from('products')
            .insert([product])
            .select()
        
        if (error) throw error
        return data[0]
    } catch (error) {
        console.error('Error adding product:', error)
        return null
    }
}

// Example usage:
// const products = await getProducts()
// const newProduct = await addProduct({ 
//     name: 'New Product', 
//     price: 99.99, 
//     description: 'Description' 
// }) 