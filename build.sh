#!/bin/sh
set -eu

rm -rf dist
mkdir -p dist
cp server.js run.sh package.json dist/
cp -R public dist/public
chmod 755 dist/run.sh
