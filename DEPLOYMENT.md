# Deployment Guide

This guide will help you deploy the Football Betting app using Vercel (frontend) and Render (backend).

## Prerequisites

- GitHub account
- Vercel account (sign up at https://vercel.com)
- Render account (sign up at https://render.com)

## Backend Deployment (Render)

1. **Push your code to GitHub** (if not already done)

2. **Create a new Web Service on Render:**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `football-betting-api` (or your preferred name)
     - **Root Directory**: `backend`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Instance Type**: Free (or your preferred tier)

3. **Set Environment Variables:**
   - Click "Environment" tab
   - Add the following variables:
     - `SECRET_KEY`: Generate a secure random string
     - `FLASK_DEBUG`: `False`
     - `CORS_ORIGINS`: Will be set after frontend deployment (e.g., `https://your-app.vercel.app`)

4. **Deploy:**
   - Click "Create Web Service"
   - Wait for the deployment to complete
   - Note your backend URL (e.g., `https://football-betting-api.onrender.com`)

5. **Update CORS after frontend deployment:**
   - After deploying the frontend, update the `CORS_ORIGINS` environment variable
   - Add your Vercel URL: `https://your-app.vercel.app,http://localhost:5173`

## Frontend Deployment (Vercel)

1. **Deploy to Vercel:**
   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Configure the project:
     - **Framework Preset**: Vite
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build`
     - **Output Directory**: `dist`

2. **Set Environment Variables:**
   - In Vercel project settings → "Environment Variables"
   - Add: `VITE_API_URL` = `https://your-render-backend-url.onrender.com/api`
   - Example: `https://football-betting-api.onrender.com/api`

3. **Deploy:**
   - Click "Deploy"
   - Wait for deployment to complete
   - Note your frontend URL (e.g., `https://football-betting.vercel.app`)

4. **Update Backend CORS:**
   - Go back to Render dashboard
   - Update `CORS_ORIGINS` to include your Vercel URL
   - The service will automatically redeploy

## Post-Deployment

1. **Test the application:**
   - Visit your Vercel URL
   - Check that player data loads correctly
   - Test predictions functionality

2. **Database persistence:**
   - The SQLite database will be created automatically on first run
   - Note: Render's free tier has ephemeral storage, so the database may reset on service restarts
   - For production, consider upgrading to a persistent disk or using PostgreSQL

## Troubleshooting

- **CORS errors**: Make sure `CORS_ORIGINS` in Render includes your exact Vercel URL
- **API not connecting**: Verify `VITE_API_URL` in Vercel matches your Render backend URL
- **Database issues**: Check Render logs for database initialization errors

## Local Development

To run locally after cloning:

1. **Backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Environment variables:**
   - Backend: Create `.env` file based on `.env.example`
   - Frontend: Uses `http://localhost:5000/api` by default
