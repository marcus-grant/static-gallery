# Metadata Consistency and Idempotent Deployment System

The Galleria deployment system ensures consistency between local photo collections and remote state through a dual-hash metadata system that enables selective, idempotent deployments based on file changes and settings modifications.

## Overview

The metadata consistency system solves several key challenges:
- **Selective deployment**: Only upload photos that have actually changed
- **Settings consistency**: Detect when timezone or timestamp settings require redeployment
- **Remote state verification**: Ensure local metadata reflects actual remote state
- **Idempotent operations**: Multiple deployments with same state produce identical results

## Dual-Hash Metadata System

### Hash Types

**`file_hash`** (Original File Hash)
- SHA256 hash of the original source file (unchanged)
- Used for change detection of source photos
- Remains constant unless source file is modified

**`deployment_file_hash`** (Deployment File Hash)  
- SHA256 hash of the photo after EXIF modifications are applied
- Reflects both timestamp corrections and timezone settings
- Changes when `TIMESTAMP_OFFSET_HOURS` or `TARGET_TIMEZONE_OFFSET_HOURS` change

### Metadata Generation Process

1. **Photo Processing Phase** (`process_dual_photo_collection`):
   ```
   Original file → Read EXIF → Apply TIMESTAMP_OFFSET_HOURS → Generate filename
   ↓
   Calculate file_hash (original bytes)
   ↓
   Simulate EXIF modification (corrected timestamp + TARGET_TIMEZONE_OFFSET_HOURS)
   ↓
   Calculate deployment_file_hash (modified bytes)
   ↓
   Store both hashes in gallery-metadata.json
   ```

2. **Metadata Structure**:
   ```json
   {
     "photos": [
       {
         "id": "wedding-20231225-133045-r5a-0",
         "original_path": "pics-full/IMG_001.jpg",
         "file_hash": "abc123...",           // Original file
         "deployment_file_hash": "def456...", // After EXIF modification
         "exif": {
           "original_timestamp": "2023-12-25T17:30:45",
           "corrected_timestamp": "2023-12-25T13:30:45",
           "timezone_original": "+00:00"
         }
       }
     ],
     "settings": {
       "timestamp_offset_hours": -4
     }
   }
   ```

## Consistency Guarantees

### Local Consistency

**Source File Changes**: When a source photo is modified:
- `file_hash` changes → triggers reprocessing
- `deployment_file_hash` recalculated → triggers redeployment
- Metadata reflects new state

**Settings Changes**: When timezone settings change:
- `file_hash` remains unchanged (source file unchanged)  
- `deployment_file_hash` changes (different EXIF modification)
- All photos marked for redeployment despite unchanged source files

### Remote Consistency

**Metadata-Last Upload Pattern**:
1. Upload all changed photos first
2. Upload gallery-metadata.json last (atomic commit)
3. Remote metadata always reflects actual uploaded state

**State Verification**:
- Compare local `deployment_file_hash` with remote metadata
- Only upload photos where hashes differ
- Detect orphaned remote files (exist remotely but not in local metadata)

## Idempotent Deployment Operations

### Change Detection Logic

```python
def needs_deployment(local_photo, remote_metadata):
    remote_hash = remote_metadata.get(local_photo.id, {}).get('deployment_file_hash')
    return local_photo.deployment_file_hash != remote_hash
```

### Settings Change Scenarios

**Scenario 1: Timestamp Offset Change**
- `TIMESTAMP_OFFSET_HOURS`: 0 → -2
- Effect: All photos get new `deployment_file_hash` (corrected timestamps change)
- Result: All photos redeployed with updated EXIF DateTimeOriginal

**Scenario 2: Timezone Change**  
- `TARGET_TIMEZONE_OFFSET_HOURS`: 13 → -5
- Effect: All photos get new `deployment_file_hash` (timezone EXIF changes)
- Result: All photos redeployed with OffsetTimeOriginal: -05:00

**Scenario 3: No Changes**
- Settings unchanged, no new/modified photos
- Effect: All `deployment_file_hash` values match remote
- Result: No uploads performed (idempotent)

### Failure Recovery

**Partial Upload Failure**:
- Some photos uploaded, metadata upload fails
- Next deployment: compares hashes, uploads only remaining photos
- Eventually consistent state achieved

**Metadata Corruption**:
- Remote metadata missing or corrupted
- Deployment compares against empty state
- All photos marked for upload (safe recovery)

## Implementation Examples

### Deployment Plan Generation

```python
def generate_deployment_plan(local_metadata, remote_metadata):
    plan = {
        'upload': [],
        'delete': [],
        'unchanged': []
    }
    
    for photo in local_metadata.photos:
        remote_hash = remote_metadata.get(photo.id, {}).get('deployment_file_hash')
        if photo.deployment_file_hash != remote_hash:
            plan['upload'].append(photo)
        else:
            plan['unchanged'].append(photo)
    
    # Detect orphaned remote files
    for remote_id in remote_metadata:
        if not any(p.id == remote_id for p in local_metadata.photos):
            plan['delete'].append(remote_id)
    
    return plan
```

### Settings Impact Analysis

```python
def analyze_settings_impact(current_settings, new_settings):
    changes = []
    
    if current_settings.timestamp_offset_hours != new_settings.timestamp_offset_hours:
        changes.append("Timestamp corrections changed - all photos will be redeployed")
    
    if current_settings.target_timezone_offset_hours != new_settings.target_timezone_offset_hours:
        changes.append("Timezone settings changed - all photos will be redeployed")
    
    return changes
```

## Operational Benefits

### Development Workflow
- Change settings locally → automatic detection of required redeployments
- Add new photos → only new photos uploaded
- Modify existing photos → only modified photos uploaded

### Production Reliability  
- Multiple deployments with same state are safe (idempotent)
- Partial failures can be resumed without corruption
- Settings changes don't require manual intervention

### Performance Optimization
- Large photo collections: only changed photos transferred
- Bandwidth efficient: metadata comparison before uploads
- Time efficient: skip unnecessary operations

## Monitoring and Debugging

### Deployment Logs
```
Deployment Plan:
- Upload: 3 photos (2 new, 1 modified)
- Unchanged: 142 photos
- Delete: 1 orphaned photo
- Reason: TIMESTAMP_OFFSET_HOURS changed from 0 to -2
```

### Metadata Validation
```python
def validate_metadata_consistency(local_metadata, remote_metadata):
    """Validate that metadata properly reflects actual state."""
    issues = []
    
    # Check for hash mismatches
    for photo in local_metadata.photos:
        if photo.deployment_file_hash == photo.file_hash:
            if settings.TARGET_TIMEZONE_OFFSET_HOURS != 13:
                issues.append(f"Photo {photo.id}: deployment hash should differ from file hash")
    
    return issues
```

This metadata consistency system ensures reliable, efficient deployments while maintaining perfect synchronization between local photo collections and remote gallery state.