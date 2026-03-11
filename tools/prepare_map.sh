#!/bin/bash
# tools/prepare_map.sh
#
# Downloads Belgium OSM data and preprocesses it for OSRM.
# Run this ONCE on your PC/laptop — NOT on the Pi.
# Then copy osrm/data/ to the Pi.
#
# Requirements: Docker must be running.
# Time: 5-15 minutes. Disk: ~1GB during processing, ~400MB final.

set -e

EXTRACT_URL="https://download.geofabrik.de/europe/belgium-latest.osm.pbf"
EXTRACT_FILE="belgium-latest.osm.pbf"
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)/osrm/data"
OSRM_IMAGE="osrm/osrm-backend:latest"

echo "=================================="
echo "  LiveHaul -- Map Preparation"
echo "  Region: Belgium"
echo "=================================="
echo ""

mkdir -p "$DATA_DIR"

if [ -f "$DATA_DIR/$EXTRACT_FILE" ]; then
    echo "Extract already exists: $EXTRACT_FILE"
else
    echo "Downloading Belgium OSM extract (~350MB)..."
    curl -L --progress-bar "$EXTRACT_URL" -o "$DATA_DIR/$EXTRACT_FILE"
    echo "Download complete"
fi

echo ""
echo "Preprocessing for OSRM (3 steps)..."

echo "  [1/3] osrm-extract"
docker run --rm -v "$DATA_DIR:/data" "$OSRM_IMAGE" \
    osrm-extract -p /opt/car.lua /data/$EXTRACT_FILE

echo "  [2/3] osrm-partition"
docker run --rm -v "$DATA_DIR:/data" "$OSRM_IMAGE" \
    osrm-partition /data/${EXTRACT_FILE%.osm.pbf}.osrm

echo "  [3/3] osrm-customize"
docker run --rm -v "$DATA_DIR:/data" "$OSRM_IMAGE" \
    osrm-customize /data/${EXTRACT_FILE%.osm.pbf}.osrm

echo ""
echo "Done! Start the server with: docker-compose up"
echo ""
echo "To copy to Pi:"
echo "  rsync -av osrm/data/ pi@livehaul.local:~/livehaul-server/osrm/data/"
