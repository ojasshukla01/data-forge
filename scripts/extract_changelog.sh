#!/usr/bin/env bash
# Extract the CHANGELOG section for a given version (e.g. 0.1.0).
# Usage: ./scripts/extract_changelog.sh 0.1.0
# Output is written to stdout (for use as GitHub release body).

set -e
VERSION="$1"
if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version> (e.g. 0.1.0)" >&2
  exit 1
fi

CHANGELOG="${2:-CHANGELOG.md}"
if [ ! -f "$CHANGELOG" ]; then
  echo "CHANGELOG not found: $CHANGELOG" >&2
  exit 1
fi

# Match ## [X.Y.Z] or ## [X.Y.Z] — ...
found=0
while IFS= read -r line; do
  if [[ "$line" =~ ^##[[:space:]]+\[${VERSION}\] ]]; then
    found=1
    echo "$line"
    continue
  fi
  if [ "$found" -eq 1 ]; then
    if [[ "$line" =~ ^##\ \[ ]]; then
      break
    fi
    echo "$line"
  fi
done < "$CHANGELOG"

if [ "$found" -eq 0 ]; then
  echo "Version $VERSION not found in CHANGELOG" >&2
  exit 1
fi
