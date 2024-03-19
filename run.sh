#!/bin/bash
set -x

initialize_log() {
  echo "Creating logs directory at: $log_directory"
  mkdir -p "$log_directory" # Corrected to use the variable directly

  if [ ! -d "$log_directory" ]; then
    echo "Failed to create the logs directory at '$log_directory'."
    exit 1
  else
    echo "Logs directory verified at '$log_directory'."
  fi

  local log_file_path="$log_directory/script_log_$(date +%Y%m%d_%H%M%S).log"
  echo "Script execution log - $(date)" > "$log_file_path"
  echo "$log_file_path" # This echoes the path for capture by the caller
}


read_config() {
  local config_file=$1
  if [ -f "$config_file" ]; then
    while IFS='=' read -r key value; do
      case "$key" in
        "venv_directory") venv_directory="$value" ;;
        "txt2kb_root") txt2kb_root="$value" ;;
        "txt2kb") txt2kb="$value" ;;

        "newscollector_root") newscollector_root="$value" ;;
        "txt2kb_combined") txt2kb_combined="$value" ;;
        "txt2kb_converted") txt2kb_converted="$value" ;;

        "combine_script") combine_script="$value" ;;
        "convert_script") convert_script="$value" ;;
        "process_script") process_script="$value" ;;
        "archive_script") archive_script="$value" ;;
        "newscollector_script") newscollector_script="$value" ;;

        "log_directory") log_directory="$value" ;;
      esac
    done < "$config_file"
  else
    echo "Config file $config_file not found. Exiting."
    exit 1
  fi
}

# Function to activate the virtual environment
activate_venv() {
  local venv_dir=$1
  local log_file=$2
  if [ -f "$venv_dir/bin/activate" ]; then
    source "$venv_dir/bin/activate"
    echo "Virtual environment activated: $VIRTUAL_ENV" >> "$log_file"
  else
    echo "Virtual environment not found. Ensure '$venv_dir/bin/activate' exists." >> "$log_file"
    exit 1
  fi
}

# Function to navigate to the specified directory
navigate_to_directory() {
  local dir=$1
  local log_file=$2
  dir=$(echo "$dir" | tr -d '[:space:]')  # Remove leading/trailing whitespace
  if [ -d "$dir" ]; then
    cd "$dir" || exit
    if [ -n "$log_file" ]; then
      echo "Moved to the directory: $PWD." >> "$log_file"
    else
      echo "Moved to the directory: $PWD."
    fi
  else
    if [ -n "$log_file" ]; then
      echo "Directory '$dir' not found. Exiting." >> "$log_file"
    else
      echo "Directory '$dir' not found. Exiting."
    fi
    exit 1
  fi
}

# Function to count files in a directory
count_files() {
  local directory=$1
  local pattern=$2
  local count=$(ls $directory/$pattern 2>/dev/null | wc -l)
  echo "$count"
}

# Function to execute scripts
execute_script() {
  local script=$1
  local directory=$2
  local skip_confirmation=$3
  local log_file=$4
  if [ -f "$directory/$script" ]; then
    if [ "$skip_confirmation" != "-y" ]; then
      read -p "Press Enter to execute $script in $directory, or 'q' to quit: " choice
      echo "User choice: $choice"   >> "$log_file"
      [[ "$choice" == "q" ]] && return 1
    fi
    cd "$directory" || exit

    echo "Attempting to execute script: $script in directory: $directory"
    ls -l "$directory/$script"


    python3 "$script"
    echo "$script executed in $directory."   >> "$log_file"
  else
    echo "$script not found in $directory. Skipping execution."   >> "$log_file"
  fi
}

# Function to check for file existence with pattern
check_files_pattern_exist() {
  local directory=$1
  local pattern=$2
  local files=($(ls $directory/$pattern 2>/dev/null))
  [ ${#files[@]} -gt 0 ]
}

# Function to move files
move_files() {
  local source_dir=$1
  local target_dir=$2
  local pattern=$3
  local log_file=$4
  local files=($(ls $source_dir/$pattern 2>/dev/null))
  for file in "${files[@]}"; do
    mv "$source_dir/$file" "$target_dir"
    echo "Moved file: $file from $source_dir to $target_dir"   >> "$log_file"
  done
}

# Function to create JSON from the latest file
create_json_from_latest_file() {
  local directory=$1
  local convert_script=$2
  local log_file=$3
  local recent_file=$(ls -t "$directory" | head -1)
  local output_file="${recent_file%.*}_$(date +%Y_%m_%d).json"
  if [ -f "$directory/$convert_script" ]; then
    python3 "$directory/$convert_script" "$recent_file" "$output_file"
    echo "JSON created from the latest file: $output_file"   >> "$log_file"
  else
    echo "$convert_script not found in $directory. Skipping JSON creation."   >> "$log_file"
  fi
}

main() {
  local skip_confirmation=$1
  local config_file=$2

  # Read configuration to set log_directory and other settings FIRST
  read_config "$config_file"

  log_directory="$log_directory"
  log_file="$log_directory/script_log_$(date +%Y%m%d_%H%M%S).log"
  mkdir -p "$log_directory"
  echo "Log initialized at $(date)" > "$log_file"  # Creates the file and logs the initialization time


  # Step 2: Activate virtual environment
  activate_venv "$venv_directory" "$log_file"

  # Step 3: Check the number of HTML files in the current directory
  local html_count=$(count_files "$txt2kb" "*.html")
  echo "HTML file count: $html_count" >> "$log_file"
  if [ "$html_count" -gt 1 ]; then
    echo "More than 1 HTML file found." >> "$log_file"
  else
    echo "0 HTML files found. Skipping to step 5."   >> "$log_file"
  fi

  # Step 4: Execute the combine.py script
  if [ "$skip_confirmation" != "-y" ]; then
    read -p "Do you want to run the combine.py script? (y/n): " choice
    echo "User choice: $choice"   >> "$log_file"
    [[ "$choice" != "y" ]] && exit 0
  fi
  execute_script "$combine_script" "$txt2kb" "$skip_confirmation" >> "$log_file"

  # Step 5: Check if the combined file exists
  if check_files_pattern_exist "$txt2kb" "combined*"; then
    echo "Combined file found."   >> "$log_file"
  else
    echo "Combined file not found. Skipping to step 15."   >> "$log_file"
    exit 0
  fi

  # Step 6: Move the combined file to the txt2kb/combined directory
  if [ "$skip_confirmation" != "-y" ]; then
    read -p "Do you want to move the combined file to the txt2kb/combined directory? (y/n): " choice
    echo "User choice: $choice"   >> "$log_file"
    [[ "$choice" != "y" ]] && exit 0
  fi
  move_files "$txt2kb" "$txt2kb_combined" "combined*" >> "$log_file"

  # Step 7: Navigate to the txt2kb/converted directory
  navigate_to_directory "$txt2kb_converted" >> "$log_file"

  # Step 8: Create JSON from the latest file in the txt2kb/converted directory
  if [ "$skip_confirmation" != "-y" ]; then
    read -p "Do you want to convert the latest file to JSON? (y/n): " choice
    echo "User choice: $choice"   >> "$log_file"
    [[ "$choice" != "y" ]] && exit 0
  fi
  create_json_from_latest_file "$txt2kb_converted" "$convert_script" >> "$log_file"

  # Step 9: Archive HTML files in the txt2kb directory
  navigate_to_directory "$txt2kb" >> "$log_file"
  if [ "$skip_confirmation" != "-y" ]; then
    read -p "Do you want to archive all HTML files in the txt2kb directory? (y/n): " choice
    echo "User choice: $choice"   >> "$log_file"
    [[ "$choice" != "y" ]] && exit 0
  fi
  execute_script "$archive_script" "$txt2kb" "$skip_confirmation" >> "$log_file"
}

# Check if the -y argument is provided
if [ "$1" == "-y" ]; then
  main "-y" "config.ini"
else
  main "" "config.ini"
fi

echo "Script execution completed. Log file: $log_file"
