#!/usr/bin/env bash
# Battery ALT raw data (MIT licence, ~540 MB zip / 3.4 GB extracted).
set -euo pipefail
DEST="${1:-./data/raw}"
mkdir -p "$DEST"
curl -L -o "$DEST/battery_alt_dataset.zip" \
  "https://data.nasa.gov/docs/legacy/battery_alt_dataset.zip"
unzip -q -o "$DEST/battery_alt_dataset.zip" -d "$DEST"
echo "extracted to $DEST/battery_alt_dataset"
echo "NASA Randomised-Walk steps.parquet is produced by the nasa_randomized_usage_gate package."
