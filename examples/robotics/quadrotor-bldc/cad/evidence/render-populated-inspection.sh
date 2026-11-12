#!/usr/bin/env bash
# Reproduce the inspection clip from the two hosted render-preview views.
# These are rendered CAD stills, not a recording of live firmware or physics.
set -euo pipefail
cd "$(dirname "$0")"
ffmpeg -v error -loop 1 -t 3 -i populated-iso-20261112.png -loop 1 -t 3 -i populated-front-20261112.png -filter_complex "[0:v]fps=24,scale=960:720,setsar=1,drawtext=text='Native PCB geometry - isometric':fontcolor=white:fontsize=28:x=24:y=24[v0];[1:v]fps=24,scale=960:720,setsar=1,drawtext=text='Native PCB geometry - front':fontcolor=white:fontsize=28:x=24:y=24[v1];[v0][v1]concat=n=2:v=1:a=0[v]" -map "[v]" -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart -y populated-inspection-20261112.mp4
