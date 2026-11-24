#!/usr/bin/env bash
set -euo pipefail

output_dir="${1:-data/raw}"
mkdir -p "$output_dir"

curl -L --fail --retry 5 --continue-at - \
  https://data.matr.io/1/api/v1/file/5c86c0b5fa2ede00015ddf66/download \
  -o "$output_dir/MATR_batch_20170512.mat"
curl -L --fail --retry 5 --continue-at - \
  https://data.matr.io/1/api/v1/file/5c86bf13fa2ede00015ddd82/download \
  -o "$output_dir/MATR_batch_20170630.mat"
curl -L --fail --retry 5 --continue-at - \
  https://data.matr.io/1/api/v1/file/5c86bd64fa2ede00015ddbb2/download \
  -o "$output_dir/MATR_batch_20180412.mat"
