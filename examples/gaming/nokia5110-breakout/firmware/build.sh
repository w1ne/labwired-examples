#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cargo build --locked --release --target thumbv7em-none-eabihf --target-dir target
mkdir -p build
cp target/thumbv7em-none-eabihf/release/nokia5110-invaders-lab build/nokia-breakout.elf
arm-none-eabi-objcopy -O binary build/nokia-breakout.elf build/nokia-breakout.bin
sha256sum build/nokia-breakout.elf build/nokia-breakout.bin
