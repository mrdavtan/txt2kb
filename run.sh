#!/bin/bash

# Function to activate the virtual environment
activate_venv() {
  if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated: $VIRTUAL_ENV"
  else
    echo "Virtual environment not found. Ensure '.venv/bin/activate' exists."
    exit 1
  fi
}

# Function to navigate to the specified directory
navigate_to_directory() {
  local dir=$1
  if [ -d "$dir" ]; then
    cd "$dir" || exit  # Exit if cd fails
    echo "Moved to the directory: $PWD."
  else
    echo "Directory '$dir' not found. Exiting."
    exit 1
  fi
}

# Function to execute combine.py safely
execute_combine_py() {
  if [ -f "combine.py" ]; then
    python3 combine.py
    echo "combine.py executed."
  else
    echo "combine.py not found. Skipping."
  fi
}

# Function to check for file existence with pattern
check_files_pattern_exist() {
  local pattern=$1
  local files=($(ls $pattern 2>/dev/null))
  [ ${#files[@]} -gt 0 ]
}

# Function to move and process files
move_and_process_files() {
  local target_directory=$1
  local script=$2
  local recent_file=$(ls -t | head -1)

  echo "Files in current directory before moving: $(ls -1 | wc -l)"
  mv "$recent_file" "$target_directory"
  echo "Moved file: $recent_file to $target_directory"
  echo "Files in current directory after moving: $(ls -1 | wc -l)"

  if [ -f "$script" ]; then
    cd "$target_directory" || exit  # Exit if cd fails
    python3 "$script" "$recent_file"
    echo "$script executed with the most recent file."
  else
    echo "$script not found. Exiting."
    exit 1
  fi
}

# Function to create JSON from the latest file
create_json_from_latest_file() {
  local recent_file=$(ls -t | head -1)
  local output_file="${recent_file%.*}_$(date +%Y_%m_%d).json"
  # Assuming the correct script to convert to JSON is provided
  python3 convert_to_json.py "$recent_file" "$output_file"
  echo "JSON created from the latest file: $output_file"
}

# Function to archive HTML files
archive_html_files() {
  local file_date=$(date +%Y_%m_%d)
  if [ ! -d "$file_date" ]; then
    mkdir "$file_date"
    echo "Directory $file_date created."
  fi

  local html_files=($(ls *.html 2>/dev/null))
  local html_count=${#html_files[@]}

  echo "HTML files in current directory before moving: $html_count"
  for file in "${html_files[@]}"; do
    mv "$file" "$file_date"
    echo "Moved HTML file to the directory $file_date: $file"
  done
  echo "HTML files in current directory after moving: $(ls -1 *.html | wc -l)"
}

# Function to process articles, either all or by today's date
process_articles() {
  local skip_confirmation=$1
  local articles_dir="/home/davtan/code/retrievers/newscollector/newscollector/articles"
  local current_date=$(date +%Y_%m_%d)
  local articles_count

  if [ -d "$articles_dir" ]; then
    articles_count=$(find "$articles_dir" -maxdepth 1 -type f | wc -l)
    if [ "$articles_count" -gt 20 ]; then
      echo "More than 20 articles found in the 'articles' directory."
      if [ "$skip_confirmation" != "-y" ]; then
        read -p "Press Enter to continue processing the articles, or 'q' to quit: " choice
        [[ "$choice" == "q" ]] && return 1
      fi
      python3 /home/davtan/code/txt2kb/txt2kb/process.py "$articles_dir"
      echo "process.py executed for the 'articles' directory."
    else
      echo "Less than or equal to 20 articles found. Skipping processing."
    fi
  else
    echo "'articles' directory does not exist."
  fi
}

# Main script execution starts here
skip_confirmation=$1

activate_venv
navigate_to_directory "txt2kb"

# Example of bypassing user input with the `-y` flag
if [ "$skip_confirmation" != "-y" ]; then
  read -p "Continue with the next steps? (y/n): " choice
  if [ "$choice" != "y" ]; then
    echo "Script execution stopped."
    exit 1
  fi
fi

# Assuming the continuation of logic that checks and processes files
if check_files_pattern_exist "combined*"; then
  execute_combine_py
  if [ "$skip_confirmation" != "-y" ]; then
    read -p "Press Enter to continue to move the most recent file, or 'q' to quit: " choice
    if [ "$choice" == "q" ]; then
      echo "Script execution stopped."
      exit 1
    fi
  fi

  # Move and process files, assuming 'combined' and 'process.py' as targets
  move_and_process_files "./combined" "process.py"

  # Navigate back to a specific directory if necessary
  # For instance, if we need to operate in the 'converted' directory after moving files
  navigate_to_directory "../converted"

  # Create JSON from the latest file in 'converted' directory
  create_json_from_latest_file

  # Archive HTML files, this function might be called from a directory where HTML files need archiving
  archive_html_files

  # Additional processing or cleanup can be added here
else
  echo "No 'combined*' files found. Skipping combine.py execution."
fi

# Process articles, with or without skipping confirmation
process_articles "$skip_confirmation"

echo "Script execution completed."

