# Galleria

A static wedding photo gallery built with Pelican, using AlpineJS for frontend interactions and Tailwind CSS for styling. Photos are processed with UUIDv7-based filenames derived from EXIF data and hosted on Hetzner object storage with BunnyCDN for global distribution.

**Priority**: Speed of development and deployment over feature richness. Get a working, acceptable user experience deployed quickly.

## Stack & Workflow Overview

### Technology Stack
- **Static Site Generator**: Pelican (Python 3.12)
- **Frontend**: AlpineJS + Tailwind CSS (CDN, no build step)
- **Photo Processing**: Python with Pillow, exifread
- **Storage**: Hetzner object storage (private + public buckets)
- **CDN**: BunnyCDN with Hetzner as origin
- **Development**: Local build → Hetzner deployment

### Photo Processing Workflow
```
Photographer's Photos → EXIF Extraction → UUID Generation → 
Thumbnail Creation → Upload to Buckets → Static Site Generation → Deploy
```

### Photo Organization Structure
```
Private Bucket (Hetzner):     Public Bucket (Hetzner):        Static Site:
/originals/                   /wedding-pics/                  Gallery page with:
  IMG_001.jpg                   {uuid}.jpg  (full)             - Thumbnail grid
  IMG_002.jpg                   {uuid}.jpg  (web)              - Infinite scroll
  ...                           {uuid}.webp (thumb)            - Multi-select downloads
```

### Storage Strategy
- **Private Hetzner Bucket**: Original photos with authentication (personal archive)
- **Public Hetzner Bucket**: Full + web + thumbnail versions (for static site)
- **BunnyCDN**: Global CDN caching content from public Hetzner bucket

## Setup

1. Create and activate virtual environment:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Hetzner credentials
   ```

## Project Structure

```
galleria/
├── README.md
├── requirements.txt
├── .gitignore
├── tests/
├── content/
├── themes/wedding/
├── sample-photos/
│   ├── full/          (original resolution test photos)
│   ├── web/           (web-optimized test photos)
│   └── burst/         (burst mode sequence examples)
├── build.py
└── deploy.py
```

## Usage

### Build the gallery:
```bash
python build.py
```

### Deploy to Hetzner:
```bash
python deploy.py
```

## Testing

Run tests with pytest:
```bash
pytest -v
```

## Documentation

All project documentation is located in the [doc/](./doc/) directory. Start with:

- **[Documentation Index](./doc/README.md)** - Overview and guide to all documentation
- **[Development Tasks](./doc/TODO.md)** - Current development tasks, specifications, and project roadmap
- **[Changelog](./doc/CHANGELOG.md)** - History of completed features and major changes