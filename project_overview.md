# Infraroo: Infrastructure Detection System Design

## Overview
CV system to detect road infrastructure (school crossings, bus lanes, tram tracks, bike lanes, pedestrian crossings, traffic lights, intersection markings) from Google Maps satellite imagery across Victoria, Australia. High precision over recall - when model detects something, it must be confident (>85% precision target).

## Core Design Principles
1. **Temporal tracking** - Track infrastructure changes over time with 20m spatial buffer deduplication
2. **Urban/rural coverage** - 70% urban, 30% rural in dataset to match real distribution
3. **Phased training** - Three phases: easy classes (tram/bus/school) → medium (crossings/bikes/stops) → hard (lights/arrows)
4. **Class-specific thresholds** - Higher confidence required for smaller objects (traffic lights 0.8, others 0.7)
5. **Configuration-driven** - All parameters in YAML, no hardcoding
6. **Future API-ready** - Coordinate-based detection service

---

## Project Structure
```
infraroo/
├── config/              # YAML configs: main config, class definitions
├── data/                # raw/ processed/ labels/ metadata/ test_set/
├── models/              # checkpoints/ configs/
├── notebooks/           # Exploration, training, evaluation notebooks
├── scripts/             # CLI tools: download, train, evaluate, scan
├── src/infraroo/        # Main package
│   ├── core/            # config, database, data models
│   ├── data/            # downloader, preprocessor, dataset
│   ├── tiles/           # geographic grid, coordinate conversion
│   ├── detection/       # detector, tracker, postprocessing
│   ├── evaluation/      # metrics, visualization
│   └── api/             # FastAPI server (future)
├── tests/               # Unit tests
└── docs/                # Documentation
```

---

## Module Architecture

### Core (`src/infraroo/core/`)
- **config.py** - Load/validate YAML configuration, environment variables
- **database.py** - SQLite interface for image metadata, detections, locations, experiments
- **models.py** - Dataclasses: ImageMetadata, Detection, InfrastructureLocation, BoundingBox

### Data (`src/infraroo/data/`)
- **downloader.py** - Google Maps Static API integration with rate limiting and caching
- **preprocessor.py** - Image validation, resizing, quality checks
- **dataset.py** - PyTorch Dataset for YOLO training

### Tiles (`src/infraroo/tiles/`)
- **grid.py** - Generate geographic grid of coordinates for area scanning
- **converter.py** - Bidirectional lat/lon ↔ pixel coordinate conversion (Web Mercator)
- **tiler.py** - Split large images into tiles, merge overlapping detections

### Detection (`src/infraroo/detection/`)
- **detector.py** - YOLO model wrapper with class-specific confidence thresholds
- **tracker.py** - Spatial deduplication (20m buffer), temporal tracking, change detection
- **postprocess.py** - NMS, filtering, coordinate conversion from pixels to lat/lon

### Evaluation (`src/infraroo/evaluation/`)
- **metrics.py** - Calculate mAP, precision, recall, F1, confusion matrices
- **visualizer.py** - Plot training curves, detection samples, performance heatmaps

### API (`src/infraroo/api/`) - Future
- **server.py** - FastAPI endpoints: POST /detect, GET /health
- **schemas.py** - Pydantic models for request/response validation

---

## Configuration Structure

**config/config.yaml** - Main configuration
- data: paths, dataset ratios (70% urban, 30% rural, 35% negatives)
- model: architecture (yolov8n), input size (640), phase definitions, class-specific confidence thresholds
- api: Google Maps key (env var), rate limits, caching
- tracking: buffer radius (20m), confidence thresholds, stability thresholds
- evaluation: target metrics (phase1: 0.85 mAP, phase2: 0.80, phase3: 0.70)

**config/classes.yaml** - Class definitions
- 8 classes with metadata: description, difficulty (easy/medium/hard), urban_only flag, expected appearance

---

## Database Schema (SQLite)

**images** - image_id, filepath, lat/lon, zoom, timestamps, urban_rural, quality_score, in_test_set
**detections** - detection_id, image_id (FK), infrastructure_type, confidence, bbox, lat/lon, model_version
**locations** - location_id, center_lat/lon, buffer_radius, type, first/last_seen, detection_count, avg_confidence, status
**experiments** - experiment_id, timestamp, model_arch, dataset_version, phase, hyperparameters (JSON), metrics (JSON)

All tables have appropriate indexes on location, type, confidence, and timestamps.

---

## Setup & Environment

**Local:** Python 3.9+, venv, install from requirements.txt or Poetry, .env with GOOGLE_MAPS_API_KEY, run setup_database.py

**Colab:** Clone repo, pip install, mount Google Drive for persistence, set API key env var, add src to sys.path

**Git:** Standard .gitignore (exclude data/, models/, .env, logs/), connect to GitHub

**Dependencies:** ultralytics, torch, opencv, numpy, pandas, pyyaml, requests, python-dotenv, shapely, geopy + dev tools (pytest, black, jupyter) + optional API (fastapi, uvicorn)

---

## Key Implementation Details

**Image Naming:** `{lat:.6f}_{lon:.6f}_{zoom}_{YYYYMMDD}.jpg` for traceability and temporal tracking

**Spatial Deduplication:** 20m buffer using haversine distance, merge detections of same type within buffer

**Coordinate Conversion:** Web Mercator projection for pixel ↔ lat/lon, bidirectional conversion in tiles module

**Training Phases:**
- Phase 1 (easy): tram_track, bus_lane, school_crossing → target mAP 0.85
- Phase 2 (medium): add pedestrian_crossing, bike_lane, stop_line → target mAP 0.80
- Phase 3 (hard): add traffic_light, turn_arrow → target mAP 0.70

**Test Set:** Lock after Week 2, never train on it, store locations in test_locations.json

**Rate Limiting:** Track API calls in DB, exponential backoff, cache downloads (never re-download same location)

---

## Critical Design Decisions

1. **Image naming** with lat/lon/date enables temporal tracking and prevents duplicates
2. **SQLite** for metadata (can migrate to PostgreSQL+PostGIS for production scale)
3. **20m buffer** for deduplication based on typical GPS accuracy
4. **Class-specific confidence** higher for small objects (traffic lights 0.8 vs others 0.7)
5. **70/20/10 split** for train/val/test, test set locked after Week 2
6. **YOLOv8-nano** for speed, can upgrade to small/medium if needed
7. **640x640 input** balances speed and detail (traffic lights ~5-10 pixels)
8. **30-40% negatives** in dataset to prevent false positives
9. **Three-phase training** easy→medium→hard for incremental learning
10. **Config-driven** all parameters in YAML, no hardcoding

---

## Known Limitations

- Traffic lights only 5-10 pixels at zoom 20 (resolution limit)
- Google Maps imagery can be months/years old in rural areas
- Trees, vehicles, shadows cause occlusion
- Summer vs winter tree coverage affects visibility
- Victoria-specific training (won't generalize to other regions without retraining)
- Expected 10-15% urban/rural performance gap
- Complex intersections may miss turn arrows/stop lines
- Google Maps API rate limits (10,000/day free tier)
- Tram tracks Melbourne-only (won't detect elsewhere)
- Red bus lanes not universal standard (Melbourne convention)

---

## For Claude Code

**Create this structure with:**
- Standard Python package layout with src/infraroo/
- Type hints throughout, docstrings (Google style)
- Config loading from YAML with pydantic or dataclass validation
- SQLite database with proper indexes
- Error handling for API failures, file I/O, missing data
- Logging for important operations (downloads, detections, database writes)
- Unit test stubs for core functionality
- Scripts with argparse for CLI usage
- Colab notebook template with setup cells

**First implementation priority:**
1. Core module (config loader, database interface, data models as dataclasses)
2. Data module (downloader with rate limiting and caching)
3. Scripts (setup_database.py, download_images.py)
4. Basic tests (test_downloader.py, test_database.py)
5. Empty module stubs for tiles, detection, evaluation (implement later)