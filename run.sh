#!/bin/bash
#set -x

# Initialize global log variables
log_directory="./logs" # Change this path to your actual log directory path
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
        "citizenspace") citizenspace="$value" ;;
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

execute_script() {
  local script="$1"
  local latest_html_file="$2"
  log_message "Executing script: $script"
  if [ -f "$script" ]; then
    log_message "Script file exists. Executing..."

    # Get the directory of the script
    local script_directory="$(dirname "$script")"

    # Change to the script's directory
    cd "$script_directory" || return 1

    python3 "$script" "$latest_html_file"
    log_message "Script executed successfully."

    # Change back to the original directory
    cd - >/dev/null || return 1
  else
    log_message "Script file not found: $script. Exiting..."
    return 1
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
  echo "Source directory: $source_dir"
  echo "Target directory: $target_dir"
  echo "File pattern: $pattern"

  local files=($(find "$source_dir" -maxdepth 1 -type f -name "$pattern"))
  echo "Matching files: ${files[@]}"

  for file in "${files[@]}"; do
    echo "Moving file: $file"
    mv "$file" "$target_dir"
    if [ $? -eq 0 ]; then
      log_message "Moved file: $file to $target_dir"
    else
      log_message "Failed to move file: $file to $target_dir"
    fi
  done

  if [ ${#files[@]} -eq 0 ]; then
    log_message "No files matching pattern '$pattern' found in directory '$source_dir'."
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
  local config_file=$1


  # Read configuration to set log_directory and other settings
  read_config "$config_file"

  # Initialize log file for the session
  log_directory="${log_directory:-./logs}" # Default path if not set
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

    # Execute the combine.py script
    execute_script "$combine_script"

    # Move the combined file to the txt2kb/combined directory
    move_files "$txt2kb" "$txt2kb_combined" "combined_*.html"

    # Navigate to the txt2kb/combined directory
    navigate_to_directory "$txt2kb_combined"

    # Execute the combine.py script inside the txt2kb/combined directory
    log_message "Executing combine.py script inside $txt2kb_combined"
    python3 "$txt2kb_combined/combine.py"
    local exit_status=$?
    if [ $exit_status -eq 0 ]; then
      log_message "Script executed successfully."
    else
      log_message "Script execution failed with exit status: $exit_status"
    fi

    # Move the converted file to the txt2kb/converted directory
    move_files "$txt2kb_combined" "$txt2kb_converted" "multiday_network_*.html"

    # Navigate to the txt2kb/converted directory
    navigate_to_directory "$txt2kb_converted"

    # Find and process each HTML file individually
    for html_file in "$txt2kb_converted"/multiday_network_*.html; do
      if [ -f "$html_file" ]; then
        log_message "Processing HTML file: $html_file"

        # Execute the convert.py script for the individual HTML file
        log_message "Executing convert.py script for $html_file"
        python3 "$txt2kb_converted/convert.py" "$html_file"
        exit_status=$?
        if [ $exit_status -eq 0 ]; then
          log_message "Script executed successfully for $html_file"
        else
          log_message "Script execution failed with exit status: $exit_status for $html_file"
        fi
      fi
    done

    log_message "Starting graph update process for citizenspace"
    cp *.json ../../../citizenspace/

    python3 "$txt2kb_converted/archive.py"

    log_message "moving to citizenspace directory"
    navigate_to_directory "$citizenspace"
    log_message "replacing and archiving previous graph"
    bash "$citizenspace/replace.sh"

    # Archive HTML files in the txt2kb directory
    navigate_to_directory "$txt2kb"
    execute_script "$archive_script"

    log_message "Script execution completed."

  exit 0


  # Since there are no html files to combine, check newcollector for articles ready to process.
  else
    log_message "0 HTML files found. Checking newscollector for articles to process."

  # Check for JSON files in newscollector
  json_count=$(count_files "../retrievers/newscollector/newscollector/articles" "*.json")

  if [ "$json_count" -gt 1 ]; then
    echo "More than 1 JSON file found in $newscollector_root/newscollector/articles"
    navigate_to_directory "$txt2kb"
    python3 "$txt2kb/process.py" "../../retrievers/newscollector/newscollector/articles/"

  else
    echo "No JSON files found in $newscollector_root/newscollector/articles"
    python3 "../retrievers/newscollector/newscollector/newscollector.py"
    gnome-terminal --bash -c "python3 '../retrievers/newscollector/newscollector/tech_newscollector.py'; exec bash"
  fi
fi
}
main "config.ini"

