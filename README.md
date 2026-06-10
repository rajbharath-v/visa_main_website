# VISA Pvt. Ltd — Website Project

Full Django website for visapvtltd.net with SEO and lead generation.

## Project Structure

```
visa_group/          ← Django project settings
shared/              ← Models, forms, SEO helpers (shared across all 3 sites)
visa_main/           ← visapvtltd.net — full company website
pump_site/           ← peristalticpump.in — pump specialist site
hart_site/           ← hartcommunicator.in — HART specialist site
```

## Setup — Step by Step

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create PostgreSQL database
```bash
psql -U postgres
CREATE DATABASE visa_db;
\q
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your DB password and email credentials
```

### 4. Run migrations
```bash
python manage.py makemigrations shared
python manage.py migrate
```

### 5. Create admin user
```bash
python manage.py createsuperuser
```

### 6. Add initial data via admin
```
http://localhost:8000/admin/
```
Add divisions → categories → products with images

### 7. Run development server
```bash
python manage.py runserver
```

Visit:
- http://localhost:8000 → VISA main site
- http://localhost:8000/admin/ → Admin panel

## Admin Panel Features

- **Products** — Add/edit all products with image gallery
- **Enquiries** — View all leads, update status, export CSV
- **Blog** — Write and publish SEO articles
- **Divisions/Categories** — Manage the full product hierarchy

## SEO Features

- Unique meta title + description per product (auto-generated if blank)
- JSON-LD schema: Organization, LocalBusiness, Product, BreadcrumbList, WebSite
- Auto sitemap.xml covering all 60+ products
- robots.txt
- Canonical URLs on every page
- OpenGraph tags for social sharing
- WebP image conversion on upload

## Lead Generation Features

- Enquiry form on every page (homepage, product detail, contact, sidebar)
- AJAX submission — no page reload
- Email notification to sales team on every new enquiry
- Auto-reply email to customer
- WhatsApp floating button
- All enquiries saved to database with full details
- Export leads as CSV from admin

## Deploy to Railway

1. Push code to GitHub
2. Create new Railway project → connect GitHub repo
3. Add PostgreSQL plugin
4. Set environment variables (copy from .env)
5. Add custom domain: visapvtltd.net
6. Railway auto-provisions SSL

## 3-Site Architecture

All 3 sites run from this single codebase:

| Domain               | App        | Design      |
|----------------------|------------|-------------|
| visapvtltd.net       | visa_main  | Navy blue   |
| peristalticpump.in   | pump_site  | Dark green  |
| hartcommunicator.in  | hart_site  | Dark amber  |

The `SiteRouterMiddleware` detects which domain the request
came from and routes to the correct app automatically.
