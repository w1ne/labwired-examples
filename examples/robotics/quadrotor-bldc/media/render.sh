#!/usr/bin/env bash
# Assemble real Studio browser recordings into a 1280x720 H.264 technical demo.
# No claimed telemetry is composited: overlays identify the verified workflow.
set -euo pipefail
IN="$1"
OUT="$2"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CARD="color=c=0x091521:s=1280x720:r=30"
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "$CARD:d=2.5" \
  -vf "drawtext=fontfile=$BOLD:text='FROM CODE TO ROTOR':fontcolor=white:fontsize=55:x=(w-text_w)/2:y=290,drawtext=fontfile=$FONT:text='LabWired + KernelCAD':fontcolor=0x61d1b8:fontsize=29:x=(w-text_w)/2:y=370,fade=t=in:st=0:d=0.4,fade=t=out:st=2.15:d=0.35" \
  -an -c:v libx264 -threads 2 -preset faster -crf 20 -pix_fmt yuv420p -r 30 "$TMP/00.mp4"
trim_scene() {
  local id="$1" start="$2" duration="$3" title="$4" col="$5"
  ffmpeg -hide_banner -loglevel error -y -ss "$start" -t "$duration" -i "$IN/$id.webm" \
    -vf "fps=30,scale=1280:720:flags=lanczos,drawtext=fontfile=$BOLD:text='$title':fontcolor=$col:fontsize=27:x=50:y=644:shadowcolor=black@0.85:shadowx=2:shadowy=2,fade=t=in:st=0:d=0.22,fade=t=out:st=$(awk -v n="$duration" 'BEGIN{printf "%.3f",n-0.28}'):d=0.28" \
    -an -c:v libx264 -threads 2 -preset faster -crf 20 -pix_fmt yuv420p -r 30 "$TMP/$id.mp4"
}
trim_scene 01-kernelcad 6.0 8.0 "KERNELCAD   PARAMETRIC QUADROTOR" "black"
trim_scene 02-simulation 5.5 6.3 "LABWIRED   REAL STM32 FIRMWARE" "white"
trim_scene 03-fault-injection 5.5 9.1 "INJECT FAULT   INVERTER SHUTDOWN" "white"
trim_scene 04-final-cad 6.0 6.8 "4 ROTOR JOINTS   ONE VERIFIED MOTOR" "white"
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "$CARD:d=2.8" \
  -vf "drawtext=fontfile=$BOLD:text='LabWired + KernelCAD':fontcolor=white:fontsize=49:x=(w-text_w)/2:y=256,drawtext=fontfile=$FONT:text='github.com/w1ne/labwired-examples':fontcolor=0x61d1b8:fontsize=28:x=(w-text_w)/2:y=352,fade=t=in:st=0:d=0.35,fade=t=out:st=2.42:d=0.35" \
  -an -c:v libx264 -threads 2 -preset faster -crf 20 -pix_fmt yuv420p -r 30 "$TMP/99.mp4"
printf "file '%s'\n" "$TMP/00.mp4" "$TMP/01-kernelcad.mp4" "$TMP/02-simulation.mp4" "$TMP/03-fault-injection.mp4" "$TMP/04-final-cad.mp4" "$TMP/99.mp4" > "$TMP/list.txt"
mkdir -p "$(dirname "$OUT")"
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$TMP/list.txt" \
  -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -map 0:v -map 1:a -shortest -c:v copy -c:a aac -b:a 96k -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
echo VIDEO_DONE="$OUT"
