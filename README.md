# Infraroo

YOLO-based infrastructure detection from Google Maps satellite imagery. Detects road markings and infrastructure (pedestrian crossings, school crossings, traffic signals, bus lanes, parking bays, bike lanes).

## Setup

1. Install dependencies: `uv sync`
2. Copy `.env.example` to `.env` and add your Google Maps API key
3. Add coordinates to `data/coordinates.csv`
4. Download images: `uv run python scripts/download_images.py data/coordinates.csv`
5. Annotate in CVAT, export YOLO format labels

## Configuration

Edit `config/config.yaml` to change download zoom level and training parameters.

## Notebooks

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bobbyely/infraroo/blob/main/notebooks/01_training.ipynb)