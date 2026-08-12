#!/usr/bin/env bash
# Package FamilyOpsDA.bundle zip for APS (run on Windows after dotnet build).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$ROOT/../../FamilyOpsDA.zip}"
CFG="${CONFIG:-Release}"
BIN="$ROOT/bin/$CFG/net8.0-windows"
STAGE="$ROOT/.bundle_stage/FamilyOpsDA.bundle"
rm -rf "$ROOT/.bundle_stage"
mkdir -p "$STAGE/Contents"
cp "$ROOT/PackageContents.xml" "$STAGE/"
cp "$ROOT/FamilyOpsDA.addin" "$STAGE/Contents/"
cp "$BIN/FamilyOpsDA.dll" "$STAGE/Contents/"
cp "$BIN/Newtonsoft.Json.dll" "$STAGE/Contents/" 2>/dev/null || true
# Do NOT copy RevitAPI.dll into the bundle
(cd "$ROOT/.bundle_stage" && zip -r "$OUT" FamilyOpsDA.bundle)
echo "Wrote $OUT"
