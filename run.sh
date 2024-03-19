#!/bin/bash
set -x

# Initialize global log variables
log_directory="/path/to/your/logs" # Change this path to your actual log directory path
log_file="$log_directory/script_log_$(date +%Y%m%d_%H%M%S).log"

# Function to append messages to the log file
log_message() {
  echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" >> "$log_file"
}

# Create the log directory if it doesn't exist and initialize the log file
mkdir -p "$log_directory"
log_message "Log initialization started."

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
    log_message "Configuration loaded successfully."
  else
    log_message "Config file $config_file not found. Exiting."
    exit 1
  fi
}

# Function to activate the virtual environment
activate_venv() {
  local venv_dir="$1"
  if [ -f "$venv_dir/bin/activate" ]; then
    source "$venv_dir/bin/activate"
    log_message "Virtual environment activated: $VIRTUAL_ENV"
  else
    log_message "Virtual environment not found. Ensure '$venv_dir/bin/activate' exists."
    exit 1
  fi
}

# Function to navigate to the specified directory
navigate_to_directory() {
  local dir="$1"
  dir=$(echo "$dir" | tr -d '[:space:]')  # Remove leading/trailing whitespace
  if [ -d "$dir" ]; then
    cd "$dir" || exit
    log_message "Moved to the directory: $PWD."
  else
    log_message "Directory '$dir' not found. Exiting."
    exit 1
  fi
}

# Function to count files in a directory
count_files() {
  local directory="$1"
  local pattern="$2"
  local count=$(ls $directory/$pattern 2>/dev/null | wc -l)
  echo "$count"
}

# Function to execute scripts
execute_script() {
  local script="$1"
  local directory="$2"
  local skip_confirmation="$3"
  if [ -f "$directory/$script" ]; then
    if [ "$skip_confirmation" != "-y" ]; then
      read -p "Press Enter to execute $script in $directory, or 'q' to quit: " choice
      log_message "User choice: $choice"
      [[ "$choice" == "q" ]] && return 1
    fi
    cd "$directory" || exit
    python3 "$script"
    log_message "$script executed in $directory."
  else
    log_message "$script not found in $directory. Skipping execution."
  fi
}

check_files_pattern_exist() {
  local directory="$1"
  local pattern="$2"
  local files=($(ls $directory/$pattern 2>/dev/null))
  local exists=0

  if [ ${#files[@]} -gt 0 ]; then
    exists=1
    log_message "Files matching pattern '$pattern' exist in directory '$directory'."
  else
    log_message "No files matching pattern '$pattern' found in directory '$directory'."
  fi

  return $exists
}

move_files() {
  local source_dir="$1"
  local target_dir="$2"
  local pattern="$3"
  local files=($(ls $source_dir/$pattern 2>/dev/null))

  for file in "${files[@]}"; do
    mv "$source_dir/$file" "$target_dir"
    log_message "Moved file: $file from $source_dir to $target_dir"
  done

  if [ ${#files[@]} -eq 0 ]; then
    log_message "No files matching pattern '$pattern' to move from '$source_dir'."
  fi
}


create_json_from_latest_file() {
  local directory="$1"
  local convert_script="$2"
  local recent_file=$(ls -t "$directory"/* 2>/dev/null | head -1) # Ensure this captures the full path
  local output_file="${recent_file%.*}_$(date +%Y_%m_%d).json"

  if [ -f "$directory/$convert_script" ] && [ -n "$recent_file" ]; then
    python3 "$directory/$convert_script" "$recent_file" "$output_file"
    log_message "JSON created from the latest file: $output_file"
  else
    if [ ! -f "$directory/$convert_script" ]; then
      log_message "$convert_script not found in $directory. Skipping JSON creation."
    elif [ -z "$recent_file" ]; then
      log_message "No recent file found in $directory for JSON creation."
    fi
  fi
}

main() {
  local skip_confirmation=$1
  local config_file=$2

  # Read configuration to set log_directory and other settings
  read_config "$config_file"

  # Initialize log file for the session
  log_directory="${log_directory:-/path/to/your/logs}" # Default path if not set
  log_file="$log_directory/script_log_$(date +%Y%m%d_%H%M%S).log"
  mkdir -p "$log_directory"
  log_message "Log initialization started."

  # Activate virtual environment
  activate_venv "$venv_directory"

  # Check the number of HTML files in the txt2kb directory
  local html_count=$(count_files "$txt2kb" "*.html")
  log_message "HTML file count in '$txt2kb': $html_count"
  if [ "$html_count" -gt 1 ]; then
    log_message "More than 1 HTML file found."
  else
    log_message "0 HTML files found. Skipping to next steps."
  fi

  # Execute the combine.py script if confirmation is not skipped or is affirmative
  if [ "$skip_confirmation" != "-y" ]; then
    read -p "Do you want to run the combine.py script? (y/n): " choice
    log_message "User choice for running combine.py: $choice"
    [[ "$choice" != "y" ]] && return
  fi
  execute_script "$combine_script" "$txt2kb" "$skip_confirmation"

  # Check if the combined file exists
  if check_files_pattern_exist "$txt2kb" "combined*"; then
    log_message "Combined file found."
  else
    log_message "Combined file not found. Exiting."
    return
  fi

  # Move the combined file to the txt2kb/combined directory
  if [ "$skip_confirmation" != "-y" ]; then
    read -p "Do you want to move the combined file to the txt2kb/combined directory? (y/n): " choice
    log_message "User choice for moving combined file: $choice"
    [[ "$choice" != "y" ]] && return
  fi
  move_files "$txt2kb" "$txt2kb_combined" "combined*"

  # Navigate to the txt2kb/converted directory
  navigate_to_directory "$txt2kb_converted"

  # Create JSON from the latest file in the txt2kb/converted directory
  if [ "$skip_confirmation" != "-y" ]; then
    read -p "Do you want to convert the latest file to JSON? (y/n): " choice
    log_message "User choice for converting to JSON: $choice"
    [[ "$choice" != "y" ]] && return
  fi
  create_json_from_latest_file "$txt2kb_converted" "$convert_script"

  # Archive HTML files in the txt2kb directory
  navigate_to_directory "$txt2kb"
  if [ "$skip_confirmation" != "-y" ]; then
    read -p "Do you want to archive all HTML files in the txt2kb directory? (y/n): " choice
    log_message "User choice for archiving HTML files: $choice"
    [[ "$choice" != "y" ]] && return
  fi
  execute_script "$archive_script" "$txt2kb" "$skip_confirmation"

  log_message "Script execution completed."
}


# Check if the -y argument is provided
if [ "$1" == "-y" ]; then
  main "-y" "config.ini"
else
  main "" "config.ini"
fi

log_message "Script execution completed."
