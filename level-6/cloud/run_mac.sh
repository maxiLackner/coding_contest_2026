#!/bin/bash
# Runs the C++ annealer on large and enormous for MINUTES minutes on all cores; results land in level-6/cloud/mac_out/.
set -u
cd "$(dirname "$0")/.."
MINUTES=${1:-35}
CORES=$(sysctl -n hw.ncpu 2>/dev/null || nproc)
c++ -O3 -std=c++17 -pthread -o cloud/sa cloud/sa.cpp || exit 1
mkdir -p cloud/mac_out
cp out_level-6_3-large.txt cloud/mac_out/out_level-6_3-large.txt
cp out_level-6_4-enormous.txt cloud/mac_out/out_level-6_4-enormous.txt
END=$(( $(date +%s) + MINUTES * 60 ))
SEED=101
while [ "$(date +%s)" -lt "$END" ]; do
  for TAG in 4-enormous 3-large; do
    ./cloud/sa in_level-6_$TAG.txt cloud/mac_out/out_level-6_$TAG.txt cloud/mac_out/next_$TAG.txt 1500000 "$CORES" "$SEED" 0.30 0.05 \
      && mv cloud/mac_out/next_$TAG.txt cloud/mac_out/out_level-6_$TAG.txt
    SEED=$((SEED + 1))
    [ "$(date +%s)" -ge "$END" ] && break
  done
done
echo "done: send cloud/mac_out/out_level-6_3-large.txt and cloud/mac_out/out_level-6_4-enormous.txt"
