# Online Store

A modern e-commerce website built with HTML, CSS, JavaScript, and Supabase.

## Deployment Instructions

1. Fork this repository to your GitHub account
2. Go to [Vercel](https://vercel.com) and sign in with your GitHub account
3. Click "New Project" and select your forked repository
4. Add the following environment variables in Vercel:
   - `VITE_SUPABASE_URL`: Your Supabase project URL
   - `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key
5. Click "Deploy"

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Features

- User authentication
- Product browsing and filtering
- Shopping cart functionality
- Order management
- Responsive design
- Dark/Light theme support

## Tech Stack

- HTML5
- CSS3
- JavaScript
- Supabase (Backend)
- Vercel (Hosting)

## Local Development

1. Clone the repository
2. Create a `.env` file with your Supabase credentials
3. Open `index.html` in your browser

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 