#!/bin/bash

# Move to directory, activate venv
#cd /home/davtan/code/txt2kb
source .venv/bin/activate
echo "Virtual environment activated."
read -p "Continue to the next step? (y/n): " choice
if [ "$choice" != "y" ]; then
  echo "Script execution stopped."
  exit 1
fi

# Move to directory where files are
cd ./txt2kb
echo "Moved to ./txt2kb directory."
read -p "Continue to the next step? (y/n): " choice
if [ "$choice" != "y" ]; then
  echo "Script execution stopped."
  exit 1
fi

# Check if there are more than 20 files
file_count=$(ls -1 | wc -l)
if [ "$file_count" -gt 20 ]; then
  # Check if combined* exists
  if [ ! -f "combined*" ]; then
    python3 combine.py
    echo "combine.py executed."
    read -p "Continue to the next step? (y/n): " choice
    if [ "$choice" != "y" ]; then
      echo "Script execution stopped."
      exit 1
    fi
  fi

  # Find the most recent file created
  recent_file=$(ls -t | head -1)

  # Move the most recent file to ./combined
  mv "$recent_file" ./combined
  echo "Most recent file moved to ./combined."
  read -p "Continue to the next step? (y/n): " choice
  if [ "$choice" != "y" ]; then
    echo "Script execution stopped."
    exit 1
  fi

  # In the ./combined directory, run combine.py with the most recent file
  cd ./combined
  python3 combine.py "$recent_file"
  echo "combine.py executed with the most recent file."
  read -p "Continue to the next step? (y/n): " choice
  if [ "$choice" != "y" ]; then
    echo "Script execution stopped."
    exit 1
  fi

  # Find the most recent file in ./combined
  recent_combined_file=$(ls -t ./combined | head -1)

  # Move the most recent file to ../converted
  mv "$recent_combined_file" ../converted
  echo "Most recent file moved to ../converted."
  read -p "Continue to the next step? (y/n): " choice
  if [ "$choice" != "y" ]; then
    echo "Script execution stopped."
    exit 1
  fi

  # Run Python script to create JSON from the latest file
  cd ../converted
  # Update output file name with date
  output_file="${recent_combined_file%.*}_$(date +%Y_%m_%d).json"
  python3 "$recent_combined_file" "$output_file"
  echo "JSON created from the latest file."
  read -p "Continue to the next step? (y/n): " choice
  if [ "$choice" != "y" ]; then
    echo "Script execution stopped."
    exit 1
  fi
fi

# Check if a directory with the file date exists
file_date=$(date +%Y_%m_%d)
if [ ! -d "$file_date" ]; then
  mkdir "$file_date"
  echo "Directory $file_date created."
fi

python3 /home/davtan/code/txt2k/txt2kb/archive.py
echo "archive.py executed."
read -p "Continue to the next step? (y/n): " choice
if [ "$choice" != "y" ]; then
  echo "Script execution stopped."
  exit 1
fi

# Move all *.html files to the directory with matching date
mv *.html "$file_date"
echo "HTML files moved to the directory $file_date."
read -p "Continue to the next step? (y/n): " choice
if [ "$choice" != "y" ]; then
  echo "Script execution stopped."
  exit 1
fi

# Check if /home/davtan/code/retrievers/newscollector/newscollector/articles/ has more than 20 JSON files
json_count=$(ls -1 /home/davtan/code/retrievers/newscollector/newscollector/articles/*.json | wc -l)
if [ "$json_count" -gt 20 ]; then
  python3 /home/davtan/code/retrievers/newscollector/newscollector/articles/remove_duplicate.py
  echo "remove_duplicate.py executed."
  read -p "Continue to the next step? (y/n): " choice
  if [ "$choice" != "y" ]; then
    echo "Script execution stopped."
    exit 1
  fi

  python3 process.py /home/davtan/code/retrievers/newscollector/newscollector/articles/.
  echo "process.py executed."
fi

echo "Script execution completed."
