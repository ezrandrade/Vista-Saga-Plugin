#!/usr/bin/env bash
# Monta o vídeo vertical (1080x1920, 30 fps, H.264, sem áudio) a partir das cenas de build_pecas.js.
# Uso: bash docs/divulgacao/montar_video.sh <pasta_de_saida_do_build_pecas>
set -euo pipefail
DIR="$1"; V="$DIR/video"
# duração de cada cena (s), na ordem cena_01..cena_10; transição suave de 0,5 s entre cenas
DUR=(3.2 2.8 4.2 2.0 2.0 2.6 4.2 4.6 4.4 4.6)
FADE=0.5
inputs=(); filter=""; i=0
for d in "${DUR[@]}"; do
  n=$(printf "%02d" $((i+1)))
  inputs+=(-loop 1 -t "$d" -framerate 30 -i "$V/cena_$n.png")
  filter+="[$i:v]scale=1080:1920,format=yuv420p,setsar=1[v$i];"
  i=$((i+1))
done
prev="v0"; offset=0
for ((k=1; k<${#DUR[@]}; k++)); do
  offset=$(python3 -c "print(round($offset + ${DUR[$((k-1))]} - $FADE, 3))")
  filter+="[$prev][v$k]xfade=transition=fade:duration=$FADE:offset=$offset[x$k];"
  prev="x$k"
done
ffmpeg -y -loglevel error "${inputs[@]}" -filter_complex "${filter%;}" -map "[$prev]" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart "$DIR/video_vertical_vista_saga_1.6.1.mp4"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$DIR/video_vertical_vista_saga_1.6.1.mp4"
