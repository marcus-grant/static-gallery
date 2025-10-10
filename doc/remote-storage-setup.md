# Remote Storage Setup Guide

This guide covers setting up S3-compatible object storage for
Galleria using two separate buckets with different security profiles.

## Architecture Overview

**Dual-Bucket Strategy**:

- **Private Archive Bucket**: Store original photos for
  safe-keeping (authenticated access only)
- **Public Gallery Bucket**: Store processed photos for
  public gallery access (via CDN)

## Supported Providers

This guide uses generic S3-compatible configuration that works with:

- Hetzner Object Storage (primary example)
- AWS S3
- DigitalOcean Spaces
- Any S3-compatible storage service

## Part 1: Hetzner Object Storage Account Setup

### 1. Create Hetzner Account

1. Visit [Hetzner Cloud Console](https://console.hetzner.cloud/)
2. Create an account or log in
3. Navigate to "Object Storage" in the sidebar

### 2. Enable Object Storage

1. Click "Enable Object Storage"
2. Choose your preferred region (e.g., `eu-central` for EU, `us-east` for US)
3. Confirm billing understanding

## Part 2: Private Archive Bucket Setup

### 1. Create Private Bucket

1. Click "Create Bucket"
2. **Bucket Name**: `galleria-originals-private` (or your preferred name)
3. **Permissions**: Private (default - do not enable public access)
4. **Region**: Choose same region as your account
5. Click "Create"

### 2. Generate Access Credentials

1. Navigate to "Object Storage" → "S3 Credentials"
2. Click "Generate new credentials"
3. **Description**: "Galleria Private Archive Access"
4. **Permissions**: Full access (read/write)
5. **Note the credentials immediately** - they won't be shown again:
   - Access Key ID
   - Secret Access Key

### 3. Security Configuration

- **Bucket Policy**: Private by default (no additional policy needed)
- **Versioning**: Optional (recommended for backup)
- **Encryption**: Optional (recommended for sensitive photos)

### 4. Manual Upload Instructions

#### Option A: Hetzner Web Interface

1. Navigate to your bucket in Hetzner console
2. Click "Upload Files" or drag and drop
3. Maintain your directory structure when uploading

#### Option B: Command Line (s3cmd)

```bash
# Install s3cmd
apt install s3cmd  # Ubuntu/Debian
brew install s3cmd  # macOS

# Configure s3cmd
s3cmd --configure
# Enter your Hetzner credentials and endpoint

# Upload entire directory preserving structure
s3cmd sync /home/marcus/Pictures/wedding/full/ \
    s3://galleria-originals-private/originals/ --preserve
```

#### Option C: Command Line (AWS CLI)**

```bash
# Install AWS CLI
pip install awscli

# Configure for Hetzner
aws configure set aws_access_key_id YOUR_ACCESS_KEY
aws configure set aws_secret_access_key YOUR_SECRET_KEY
aws configure set default.region us-east-1
aws configure set default.s3.signature_version s3v4

# Upload directory
aws s3 sync /home/marcus/Pictures/wedding/full/ \
    s3://galleria-originals-private/originals/ --endpoint-url https://your-hetzner-endpoint.com
```

## Part 3: Public Gallery Bucket Setup

### 1. Create Public Bucket

1. Click "Create Bucket"
2. **Bucket Name**: `galleria-wedding-public` (or your preferred name)
3. **Permissions**: Enable public read access
4. **Region**: Same region as private bucket
5. Click "Create"

### 2. Configure Public Access

1. Navigate to bucket settings
2. Enable "Public Read Access"
3. Configure CORS for web access:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": [],
        "MaxAgeSeconds": 3600
    }
]
```

### 3. Generate Separate Credentials

1. Create new S3 credentials
2. **Description**: "Galleria Public Gallery Upload"
3. **Permissions**: Write access to public bucket only
4. **Best Practice**: Use separate credentials from private bucket

## Part 4: Environment Configuration

### Environment Variables

Set these in your shell or `.env` file:

```bash
# Private Archive Bucket
export GALLERIA_S3_ARCHIVE_ENDPOINT="https://your-region.hetznerobjects.com"
export GALLERIA_S3_ARCHIVE_ACCESS_KEY="your_private_access_key"
export GALLERIA_S3_ARCHIVE_SECRET_KEY="your_private_secret_key"
export GALLERIA_S3_ARCHIVE_BUCKET="galleria-originals-private"
export GALLERIA_S3_ARCHIVE_REGION="us-east-1"

# Public Gallery Bucket  
export GALLERIA_S3_PUBLIC_ENDPOINT="https://your-region.hetznerobjects.com"
export GALLERIA_S3_PUBLIC_ACCESS_KEY="your_public_access_key"
export GALLERIA_S3_PUBLIC_SECRET_KEY="your_public_secret_key"
export GALLERIA_S3_PUBLIC_BUCKET="galleria-wedding-public"
export GALLERIA_S3_PUBLIC_REGION="us-east-1"
```

### Settings Precedence

Galleria follows this configuration hierarchy:

1. `settings.py` (default values)
2. `settings.local.py` (local overrides)
3. `GALLERIA_*` environment variables (runtime overrides)
4. CLI arguments (command-specific overrides)

**Note**: Only environment variables use the `GALLERIA_` prefix (host-level scope).

### Local Settings Override

Add to `settings.local.py`:

```python
# S3 Storage Configuration
S3_ARCHIVE_ENDPOINT = "https://your-region.hetznerobjects.com"
S3_ARCHIVE_BUCKET = "galleria-originals-private"
S3_PUBLIC_ENDPOINT = "https://your-region.hetznerobjects.com"
S3_PUBLIC_BUCKET = "galleria-wedding-public"

# Don't put secrets in settings.local.py - use environment variables
```

## Part 5: Security Best Practices

### Credential Management

- **Never commit credentials to git**
- Use separate credentials for each bucket
- Rotate credentials periodically
- Use environment variables for secrets

### Bucket Policies

- Private bucket: No public access whatsoever
- Public bucket: Read-only public access, write access only via credentials
- Monitor access logs regularly

### Network Security

- Use HTTPS endpoints only
- Consider IP restrictions if possible
- Enable bucket notifications for monitoring

## Part 6: CDN Integration Overview

For production deployment, the public bucket will be fronted by BunnyCDN for
global performance.

**CDN Setup**: The public gallery bucket serves as the origin for BunnyCDN.
This provides:

- Global edge caching
- Faster photo loading worldwide
- Reduced bandwidth costs
- DDoS protection

### Detailed CDN configuration

TODO: `doc/bunnycdn-setup.md` (to be created during deployment phase)
<!-- TODO: Add link to BunnyCDN setup guide once available -->

## Part 7: Alternative Providers

### AWS S3

```bash
# Endpoints (region-specific)
GALLERIA_S3_ARCHIVE_ENDPOINT=""  # Use default AWS endpoints
GALLERIA_S3_ARCHIVE_REGION="us-east-1"
```

### DigitalOcean Spaces

```bash
# Endpoints
GALLERIA_S3_ARCHIVE_ENDPOINT="https://nyc3.digitaloceanspaces.com"
GALLERIA_S3_ARCHIVE_REGION="nyc3"
```

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check credential permissions and bucket policies
2. **SSL/TLS Errors**: Ensure using HTTPS endpoints
3. **Region Mismatch**: Verify region settings match bucket location
4. **CORS Errors**: Check CORS configuration for web access

### Testing Your Setup

```bash
# Test private bucket access
aws s3 ls s3://galleria-originals-private/ --endpoint-url $GALLERIA_S3_ARCHIVE_ENDPOINT

# Test public bucket access
curl -I https://galleria-wedding-public.your-region.hetznerobjects.com/
```

## Next Steps

1. Complete manual upload of original photos to private bucket
2. Configure Galleria settings with your bucket credentials
3. Test public bucket upload with processed photos
4. Proceed with static site generation and deployment

