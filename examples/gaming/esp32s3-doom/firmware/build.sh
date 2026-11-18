#!/usr/bin/env bash
set -euo pipefail
firmware_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
image='espressif/idf@sha256:55ab243e87584859c9af3acc124b0b9423a9d8b44fc99a5d5055d7bd7312722d'
python3 "$firmware_dir/prepare_wad.py"
mkdir -p "$firmware_dir/artifacts"
# Start from the reviewed configuration; do not inherit a previous menuconfig.
cp "$firmware_dir/source/sdkconfig.defaults" "$firmware_dir/source/sdkconfig"
docker run --rm --user "$(id -u):$(id -g)" \
  -e IDF_TARGET=esp32s3 -e IDF_COMPONENT_CACHE_PATH=/project/.idf-cache \
  -e CCACHE_DIR=/project/.ccache \
  -v "$firmware_dir/source:/project" -v "$firmware_dir/artifacts:/artifacts" -w /project "$image" bash -ec '
    idf.py -B build -DPROJECT_VER=labwired-doom-rev-a build
    python -m esptool --chip esp32s3 merge_bin -o /artifacts/doom-s3-flash.bin \
      --flash_mode dio --flash_size 16MB --flash_freq 80m \
      0x0 build/bootloader/bootloader.bin 0x8000 build/partition_table/partition-table.bin \
      0x10000 build/doom-s3.bin 0x410000 wad/doom1.wad
    xtensa-esp32s3-elf-gcc --version > /artifacts/compiler-version.txt
    idf.py --version > /artifacts/idf-version.txt
  '
python3 "$firmware_dir/record_build.py"
