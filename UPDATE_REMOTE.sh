#!/bin/bash
# Run this script after renaming the repository on GitHub

echo "Updating Git remote URL to new repository name..."
git remote set-url origin https://github.com/roelvangils/inspekt.git

echo "Verifying new remote URL..."
git remote -v

echo ""
echo "✅ Remote URL updated successfully!"
echo "New URL: https://github.com/roelvangils/inspekt"
