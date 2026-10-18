#!/bin/bash
# Capture calibration images from the webcam for quantizing DINOv2.
# Move objects around, hold things up and change angles while it runs.
# Usage: scripts/capture_calib.sh [output_folder] [count]
OUT="${1:-$HOME/robo/calib}"
COUNT="${2:-50}"
mkdir -p "$OUT"
for i in $(seq -w 1 "$COUNT"); do
  ffmpeg -loglevel error -y -f v4l2 -video_size 640x480 -i /dev/video0 -frames:v 1 "$OUT/img_$i.jpg"
  sleep 0.5
done
echo "$(ls "$OUT" | wc -l) images in $OUT"
