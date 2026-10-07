#!/bin/bash
# Rebuild static/nd3d.js from tools/3d/nd3d.src.js (needs: npm install three@0.186.1 esbuild)
cd "$(dirname "$0")" && npx esbuild nd3d.src.js --bundle --minify --format=iife --target=es2019 --outfile=../../static/nd3d.js
