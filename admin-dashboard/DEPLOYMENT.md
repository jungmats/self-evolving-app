# Admin Dashboard Deployment Guide

This document describes how to deploy the Admin Operations Dashboard in various configurations.

## Prerequisites

- Node.js 18+ and npm
- GitHub Personal Access Token with `repo` and `workflow` scopes
- Access to the target repository

## Environment Configuration

The dashboard requires the following environment variables:

```bash
VITE_GITHUB_TOKEN=ghp_your_personal_access_token
VITE_GITHUB_OWNER=your-github-username
VITE_GITHUB_REPO=your-repo-name
VITE_GITHUB_API_BASE_URL=https://api.github.com  # Optional, defaults to this value
```

### Creating a GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "Admin Dashboard")
4. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
5. Click "Generate token"
6. Copy the token immediately (you won't be able to see it again)

## Deployment Options

### Option 1: Co-located with Web Server (Recommended for Development)

Deploy the admin dashboard alongside the main web server application.

#### Steps:

1. **Build the dashboard:**
   ```bash
   cd admin-dashboard
   npm install
   npm run build
   ```

2. **Configure environment variables:**
   Create a `.env` file in the `admin-dashboard` directory:
   ```bash
   cp .env.example .env
   # Edit .env with your GitHub credentials
   ```

3. **Serve static files from Web Server:**
   
   Add to your FastAPI application (e.g., in `app/main.py`):
   ```python
   from fastapi.staticfiles import StaticFiles
   
   # Mount admin dashboard static files
   app.mount("/admin", StaticFiles(directory="admin-dashboard/dist", html=True), name="admin")
   ```

4. **Access the dashboard:**
   Navigate to `http://localhost:8000/admin` (or your server URL)

#### Advantages:
- Single deployment process
- Shared server infrastructure
- Easier for development and testing

#### Disadvantages:
- Coupled deployment with main application
- Requires backend server restart for updates

---

### Option 2: Independent Static Hosting

Deploy the admin dashboard to a dedicated static hosting service.

#### Supported Platforms:

##### Netlify

1. **Build the dashboard:**
   ```bash
   cd admin-dashboard
   npm install
   npm run build
   ```

2. **Deploy to Netlify:**
   ```bash
   # Install Netlify CLI
   npm install -g netlify-cli
   
   # Login to Netlify
   netlify login
   
   # Deploy
   netlify deploy --prod --dir=dist
   ```

3. **Configure environment variables in Netlify:**
   - Go to Site settings → Build & deploy → Environment
   - Add the required environment variables

##### Vercel

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy:**
   ```bash
   cd admin-dashboard
   vercel --prod
   ```

3. **Configure environment variables:**
   ```bash
   vercel env add VITE_GITHUB_TOKEN
   vercel env add VITE_GITHUB_OWNER
   vercel env add VITE_GITHUB_REPO
   ```

##### AWS S3 + CloudFront

1. **Build the dashboard:**
   ```bash
   cd admin-dashboard
   npm install
   npm run build
   ```

2. **Create S3 bucket:**
   ```bash
   aws s3 mb s3://admin-dashboard-your-app
   aws s3 website s3://admin-dashboard-your-app --index-document index.html
   ```

3. **Upload files:**
   ```bash
   aws s3 sync dist/ s3://admin-dashboard-your-app --delete
   ```

4. **Configure CloudFront distribution** (optional, for HTTPS and CDN)

5. **Set environment variables:**
   - Create a `.env.production` file before building
   - Or use AWS Systems Manager Parameter Store for runtime configuration

#### Advantages:
- Independent deployment lifecycle
- Scalable static hosting
- CDN distribution for global performance
- No backend server required

#### Disadvantages:
- Separate deployment process
- Additional infrastructure to manage
- Environment variable management across platforms

---

## Production Build Configuration

### Build Optimization

The production build is optimized automatically by Vite:

```bash
npm run build
```

This creates:
- Minified JavaScript and CSS
- Code splitting for optimal loading
- Asset hashing for cache busting
- Source maps for debugging (optional)

### Build Output

The build output is located in `admin-dashboard/dist/`:
```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js
│   ├── index-[hash].css
│   └── ...
└── vite.svg
```

### Environment-Specific Builds

Create environment-specific configuration files:

**`.env.development`** (for local development):
```bash
VITE_GITHUB_TOKEN=ghp_dev_token
VITE_GITHUB_OWNER=dev-owner
VITE_GITHUB_REPO=dev-repo
```

**`.env.production`** (for production):
```bash
VITE_GITHUB_TOKEN=ghp_prod_token
VITE_GITHUB_OWNER=prod-owner
VITE_GITHUB_REPO=prod-repo
```

Build with specific environment:
```bash
npm run build  # Uses .env.production by default
```

---

## Security Considerations

### GitHub Token Security

**CRITICAL:** Never commit GitHub tokens to version control!

- Use `.env` files (already in `.gitignore`)
- Use environment variables in CI/CD pipelines
- Rotate tokens regularly
- Use tokens with minimal required scopes
- Consider using GitHub Apps for better security

### CORS Configuration

The admin dashboard makes client-side requests to GitHub API. Ensure:

1. GitHub API allows CORS requests (it does by default)
2. Your hosting platform doesn't block CORS
3. Use HTTPS in production to prevent token interception

### Token Storage

The dashboard stores the GitHub token in memory only (via environment variables). It does NOT:
- Store tokens in localStorage
- Store tokens in sessionStorage
- Send tokens to any server except GitHub API

---

## Monitoring and Maintenance

### Rate Limiting

GitHub API has rate limits:
- Authenticated requests: 5,000 requests per hour
- The dashboard displays warnings when rate limit is low

Monitor rate limit usage:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/rate_limit
```

### Error Handling

The dashboard includes built-in error handling:
- Network errors display user-friendly messages
- API errors show retry buttons
- Rate limit warnings appear automatically

### Updates

To update the dashboard:

1. Pull latest changes
2. Install dependencies: `npm install`
3. Run tests: `npm test`
4. Build: `npm run build`
5. Deploy using your chosen method

---

## Troubleshooting

### Dashboard shows "Missing environment variables" error

**Solution:** Ensure all required environment variables are set in `.env` file.

### GitHub API returns 401 Unauthorized

**Solution:** 
- Verify your GitHub token is valid
- Check token has required scopes (`repo`, `workflow`)
- Regenerate token if expired

### Dashboard shows no data

**Solution:**
- Verify repository owner and name are correct
- Check GitHub token has access to the repository
- Verify issues/PRs exist in the repository

### Build fails with TypeScript errors

**Solution:**
- Run `npm install` to ensure dependencies are up to date
- Check TypeScript version compatibility
- Review error messages for specific issues

### Rate limit warnings appear frequently

**Solution:**
- Reduce refresh frequency
- Implement caching (future enhancement)
- Use GitHub Apps instead of Personal Access Tokens

---

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deploy-admin-dashboard.yml`:

```yaml
name: Deploy Admin Dashboard

on:
  push:
    branches: [main]
    paths:
      - 'admin-dashboard/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install dependencies
        working-directory: admin-dashboard
        run: npm ci
      
      - name: Run tests
        working-directory: admin-dashboard
        run: npm test
      
      - name: Build
        working-directory: admin-dashboard
        run: npm run build
        env:
          VITE_GITHUB_TOKEN: ${{ secrets.ADMIN_GITHUB_TOKEN }}
          VITE_GITHUB_OWNER: ${{ secrets.GITHUB_OWNER }}
          VITE_GITHUB_REPO: ${{ secrets.GITHUB_REPO }}
      
      - name: Deploy to Netlify
        uses: netlify/actions/cli@master
        with:
          args: deploy --prod --dir=admin-dashboard/dist
        env:
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
```

---

## Performance Optimization

### Lazy Loading

The dashboard uses React lazy loading for tab components (future enhancement).

### Caching

Consider implementing:
- Browser caching for static assets (handled by hosting platform)
- API response caching (future enhancement)
- Service worker for offline support (future enhancement)

### Bundle Size

Monitor bundle size:
```bash
npm run build
# Check dist/ folder size
```

Current bundle size: ~150KB (gzipped)

---

## Support

For issues or questions:
1. Check this deployment guide
2. Review the main README.md
3. Check GitHub Issues in the repository
4. Contact the development team
