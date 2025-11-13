#!/usr/bin/env python3
"""
Download satellite images from coordinates CSV file.

Usage:
    python scripts/download_images.py data/coordinates.csv
"""

import csv
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infraroo.data.downloader import download_with_retry, DownloadError
from infraroo.core.config import load_config


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/download_images.py <coordinates.csv>")
        sys.exit(1)

    # Load configuration
    config = load_config()
    zoom = config.download_zoom
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = sys.argv[1]

    # Read CSV and download images
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Found {len(rows)} coordinates to download")
    print(f"Using zoom level: {zoom}")

    success_count = 0
    fail_count = 0
    skip_count = 0

    for i, row in enumerate(rows, 1):
        lat = float(row["lat"])
        lon = float(row["lon"])
        label = row["label"].strip()

        # Create filename: label_lat_lon_z{zoom}.jpg
        filename = f"{label}_{lat:.6f}_{lon:.6f}_z{zoom}.jpg"
        output_path = output_dir / filename

        # Skip if already exists
        if output_path.exists():
            print(f"[{i}/{len(rows)}] {label} at ({lat:.6f}, {lon:.6f}) - already exists, skipping")
            skip_count += 1
            continue

        print(f"[{i}/{len(rows)}] Downloading {label} at ({lat:.6f}, {lon:.6f})...", end=" ")

        try:
            download_with_retry(lat, lon, str(output_path), zoom=zoom)
            print("✓")
            success_count += 1
        except DownloadError as e:
            print(f"✗ Error: {e}")
            fail_count += 1

    print(f"\nComplete! Success: {success_count}, Skipped: {skip_count}, Failed: {fail_count}")
    print(f"Images saved to: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
