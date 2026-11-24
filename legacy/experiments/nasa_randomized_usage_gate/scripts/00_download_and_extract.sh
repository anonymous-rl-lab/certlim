#!/usr/bin/env bash
# Fetch the 7 NASA PCoE Randomized Battery Usage archives (CC BY 4.0) and unpack the .mat files.
set -euo pipefail
DEST="${1:-./data/raw}"; mkdir -p "$DEST"; cd "$DEST"
B="https://zenodo.org/api/records/15277374/files"
for f in \
 "1.%20Battery_Uniform_Distribution_Charge_Discharge_DataSet_2Post.zip" \
 "2.%20Battery_Uniform_Distribution_Discharge_Room_Temp_DataSet_2Post.zip" \
 "3.%20Battery_Uniform_Distribution_Variable_Charge_Room_Temp_DataSet_2Post.zip" \
 "4.%20RW_Skewed_High_40C_DataSet_2Post.zip" \
 "5.%20RW_Skewed_High_Room_Temp_DataSet_2Post.zip" \
 "6.%20RW_Skewed_Low_40C_DataSet_2Post.zip" \
 "7.%20RW_Skewed_Low_Room_Temp_DataSet_2Post.zip" ; do
  echo "==> $f"; curl -fL --retry 3 -O "$B/$f/content" -o "$(python3 -c "import urllib.parse,sys;print(urllib.parse.unquote(sys.argv[1]))" "$f")"
  unzip -o -q "$(python3 -c "import urllib.parse,sys;print(urllib.parse.unquote(sys.argv[1]))" "$f")" -x "*/R/*"
done
echo "done -> $DEST"
