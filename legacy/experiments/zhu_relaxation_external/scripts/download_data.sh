#!/usr/bin/env bash
# Fetch the Zhu 2022 archives from Zenodo (CC BY 4.0) and unpack the two used datasets.
set -euo pipefail
DEST="${1:-./data/raw}"
mkdir -p "$DEST"
BASE="https://zenodo.org/api/records/6405084/files"
for pair in "Dataset_1_NCA_battery.zip:d1" "Dataset_2_NCM_battery.zip:d2"; do
  ARCHIVE="${pair%%:*}"; TAG="${pair##*:}"
  echo "==> $ARCHIVE"
  curl -fL --retry 3 -o "$DEST/$ARCHIVE" "$BASE/$ARCHIVE/content"
  mkdir -p "$DEST/$TAG"
  unzip -o -q -j "$DEST/$ARCHIVE" '*.csv' -d "$DEST/$TAG"
  echo "    $(ls "$DEST/$TAG" | wc -l) CSV files -> $DEST/$TAG"
done
echo "Dataset_3 (NCM+NCA) is deliberately NOT downloaded; see docs/DATA_PROVENANCE.md."
