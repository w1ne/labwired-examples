# Complete Doom project source

The archive contains the complete reviewed Doom/ESP-IDF project from package commit `188016118ac91dae6fca7cac18ba730b7dd271bd`. It preserves `firmware/source/main/main.c`, the vendored Doom source and license, board pin definitions, build inputs, build scripts, runtime descriptors and the existing title/menu verification harness. It excludes compiled outputs, build caches and the ESP-IDF container filesystem.

The editable catalog entry uses profile `c` and editor path `src/main.c`. That view is the unchanged 4,636-byte `firmware/source/main/main.c` in this archive. A standalone edit of that view is not a replacement for the complete multi-file project.

## Build

Extract the archive, enter `esp32s3-doom`, and run:

```sh
bash firmware/build.sh
```

The build requires Docker and Python 3. It uses ESP-IDF v5.3.1 for ESP32-S3 from the exact container `espressif/idf@sha256:55ab243e87584859c9af3acc124b0b9423a9d8b44fc99a5d5055d7bd7312722d`. The existing build input manifest pins the shareware IWAD source release, source-image hash, offset, length and content hash. `prepare_wad.py` retrieves and verifies those bytes. Dependencies already provided by the immutable container are not copied into this archive.

`firmware/artifacts/build-manifest.json` is the original expected build receipt; the build replaces it with the new receipt. The expected application ELF is 6,371,888 bytes with SHA256 `09e6dcf243659236ffffa103063c183e4c22ff940dba11f09ea4fd0f3418cc7d`. The complete flash image is 8,455,860 bytes with SHA256 `38dd230a754ef167e07ae6350c52b0000bb7dc003c0795330119867dc1f1f2cb`. Program the complete image at address 0, as described in the included package README. The source archive contains the recorded clean replay comparison; packaging does not claim an additional compiler replay.

## Digital runtime replay

Build the CLI from core commit `31730dd16391495aed6045ffb52b1aee62d3ceab`. Obtain the two ROM files from the immutable release named in `runtime/provenance.json`; their exact byte counts and SHA256 values are checked by the harness. After rebuilding the firmware, run:

```sh
python3 authoring/verify_runtime.py --labwired /path/to/labwired --rom /path/to/esp32s3_rom.bin --drom /path/to/esp32s3_drom.bin --output /path/to/new-replay-directory
```

This executes the existing 900-million-step title and Escape-menu cases with the declared `uart0`, the physical firmware and the real mask ROM assets. It requires all runtime assertions, confirmed delivery, the recorded frame hashes and 23,079 changed framebuffer bytes. It does not claim physical hardware, display, cable, thermal or enclosure qualification. The unchanged full package and its retained evidence are at the source commit above.

## Archive verification

`authoring/package_firmware_source.py` in the repository regenerates this archive from the exact source commit. `firmware/source-archive.json` records every member hash and the direct archive identity. Packaging checks every source member against the existing provenance and build manifests, preserves executable script modes, and uses fixed tar/gzip metadata. Two generated archives must be byte-identical.
