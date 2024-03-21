#!/bin/env python3

import os
import shutil
import glob

# Create the archive directory if it doesn't exist
os.makedirs("./archive", exist_ok=True)

# Move HTML files matching the pattern to the archive directory
for file_path in glob.glob("./multiday_*.html"):
    shutil.move(file_path, "./archive")

# Move JSON files matching the pattern to the archive directory
for file_path in glob.glob("./multiday_*.json"):
    shutil.move(file_path, "./archive")
