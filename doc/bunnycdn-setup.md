# BunnyCDN Setup Guide

This guide covers setting up BunnyCDN for global content delivery of the wedding gallery.

## Prerequisites

- Hetzner object storage bucket configured and deployed
- Photos and site already uploaded to Hetzner via `python manage.py deploy`
- BunnyCDN account created

## Architecture Overview

The gallery uses **relative URLs** that work seamlessly with both local development and CDN deployment:

- **Local development**: `photos/web/photo.jpg` served by dev server
- **Production with CDN**: `photos/web/photo.jpg` served by CDN from bucket
- **No configuration needed** - same URLs work everywhere

## Step 1: Create Pull Zone

1. Log into BunnyCDN dashboard
2. Navigate to "Pull Zones" → "Add Pull Zone"  
3. Configure pull zone:
   - **Name**: `galleria` (or your preferred name)
   - **Origin URL**: Your Hetzner bucket URL (e.g., `https://your-bucket.eu-central-1.s3.hetznerobjects.com`)
   - **Pricing Zone**: Europe (recommended for EU/US audience)

## Step 2: Configure Caching Settings

### Image Caching
- **Browser Cache Expiry**: 7 days (604800 seconds)
- **CDN Cache Expiry**: 30 days (2592000 seconds)
- **Vary Cache**: Disabled (static images)

### File Extensions
Ensure these extensions are cached:
- `.jpg`, `.jpeg`, `.webp` (photos)
- `.html`, `.css`, `.js` (static site files)

## Step 3: Point Domain to CDN

After creating the pull zone, you'll receive a CDN domain (e.g., `galleria.b-cdn.net`).

**No code changes needed** - just point your domain DNS to the CDN:

```dns
yourdomain.com CNAME galleria.b-cdn.net
```

Or use the CDN domain directly for testing.

## Step 4: Test Configuration

1. Deploy your site to Hetzner (if not already done):
   ```bash
   uv run python manage.py deploy
   ```

2. Test photo loading through CDN:
   ```bash
   curl -I https://galleria.b-cdn.net/photos/thumb/wedding-20250809T132034-r5a-0.jpg
   ```

3. Test full site through CDN:
   ```bash
   curl -I https://galleria.b-cdn.net/gallery.html
   ```

## Step 5: Performance Verification

Wait 5-10 minutes for CDN propagation, then test:

1. **Performance tools**: GTmetrix, Pingdom, or WebPageTest
2. **Geographic testing**: Test from different global locations  
3. **Cache verification**: Check cache headers in browser dev tools

### Expected Improvements:
- **US users**: <2 second photo load times
- **EU users**: <1 second photo load times  
- **Cache hit ratio**: >90% after initial warming

## Benefits of Relative URL Approach

✅ **Simplified deployment** - No configuration changes needed
✅ **Same URLs everywhere** - Works in dev, staging, and production  
✅ **CDN flexibility** - Easy to switch CDN providers
✅ **No toggle complexity** - Eliminates CDN_ENABLED settings
✅ **Better security** - All assets served from same origin

## Troubleshooting

### Photos Not Loading
1. Verify origin bucket URL is accessible directly
2. Check BunnyCDN error logs in dashboard
3. Ensure photos exist at `photos/` prefix in bucket
4. Test a direct bucket URL first

### Cache Issues  
1. Use BunnyCDN purge function for specific files
2. Check cache headers in browser dev tools
3. Verify CDN pull zone is active

### Development Testing
- Local dev server handles both `/photos/` and `photos/` paths
- Use `uv run python manage.py serve` to test locally
- Relative URLs work identically in both environments

## Next Steps

After successful CDN setup:
1. Monitor performance metrics for 1 week
2. Document actual CDN domain in deployment notes
3. Consider custom domain pointing to CDN
4. Track photo popularity via BunnyCDN analytics