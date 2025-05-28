# Online Store - Vercel Deployment

This is the Vercel deployment configuration for the Online Store project.

## Deployment Steps

1. Push your code to GitHub
2. Connect your GitHub repository to Vercel
3. Vercel will automatically deploy your site

## Environment Variables

Make sure to set these environment variables in your Vercel project settings:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key

## Project Structure

- All static files (HTML, CSS, JS) are served directly
- Database connections are handled through Supabase client
- No server-side code required

## Local Development

1. Clone the repository
2. Install dependencies: `npm install`
3. Run locally: `vercel dev` 