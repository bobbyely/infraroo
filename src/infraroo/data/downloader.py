"""
Google Maps Static API downloader for satellite imagery.
"""

import os
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DownloadError(Exception):
    """Raised when image download fails."""
    pass


def download_single_image(
    lat: float,
    lon: float,
    output_path: str,
    zoom: int = 19,
    size: int = 640,
    api_key: Optional[str] = None,
) -> str:
    """
    Download a single satellite image from Google Maps Static API.

    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        output_path: Path where image will be saved (including filename)
        zoom: Zoom level (18-20 recommended for road markings, default 19)
        size: Image size in pixels (max 640x640 for free tier)
        api_key: Google Maps API key (reads from GOOGLE_MAPS_API_KEY env var if not provided)

    Returns:
        Path to downloaded image

    Raises:
        DownloadError: If download fails or API returns error

    Example:
        >>> download_single_image(-37.8136, 144.9631, "data/raw/crossing_001.jpg")
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            raise DownloadError(
                "No API key provided. Set GOOGLE_MAPS_API_KEY environment variable "
                "or pass api_key parameter."
            )

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build API request URL
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "center": f"{lat},{lon}",
        "zoom": zoom,
        "size": f"{size}x{size}",
        "maptype": "satellite",
        "key": api_key,
    }

    # Make request with timeout and error handling
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()

        # Check if response is an image (not an error message)
        content_type = response.headers.get("content-type", "")
        if "image" not in content_type:
            raise DownloadError(
                f"API returned non-image response. "
                f"Status: {response.status_code}, Content-Type: {content_type}"
            )

        # Save image
        with open(output_path, "wb") as f:
            f.write(response.content)

        return output_path

    except requests.exceptions.RequestException as e:
        raise DownloadError(f"Failed to download image: {e}")


def download_with_retry(
    lat: float,
    lon: float,
    output_path: str,
    zoom: int = 19,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> str:
    """
    Download image with retry logic and exponential backoff.

    Args:
        lat: Latitude
        lon: Longitude
        output_path: Output file path
        zoom: Zoom level
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (doubles each retry)

    Returns:
        Path to downloaded image

    Raises:
        DownloadError: If all retries fail
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            return download_single_image(lat, lon, output_path, zoom)
        except DownloadError as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = retry_delay * (2 ** attempt)
                time.sleep(delay)
            continue

    raise DownloadError(
        f"Failed after {max_retries} attempts. Last error: {last_error}"
    )
