#!/bin/bash


#Step 1. Read Config
#
#Step 2. Activate the virtual environment:
#
#    Check if the virtual environment exists at the specified location (.venv/bin/activate).
#    If the virtual environment exists, activate it.
#    If the virtual environment doesn't exist, print an error message and exit the script.
#
#Step 3. Navigate to the txt2kb directory:
#
#    Check if the txt2kb directory exists.
#    If the directory exists, navigate to it.
#    If the directory doesn't exist, print an error message and exit the script.
#
#Step 4. Check the number of HTML files in the current directory:
#
#    Count the number of HTML files in the current directory.
#    Print the contents of the HTML files.
#    If there are more than 1 HTML files, proceed to step 4.
#    If there are 0 HTML files, skip to step 5.
#
#Step 5. Execute the combine.py script:
#
#    Ask the user if they want to run the combine.py script.
#    If the user confirms, execute the combine.py script.
#    If the user declines, skip to step 15.
#
#Step 6. Check if the combined file exists:
#
#    After the combine.py script is executed (if applicable), check if the combined file exists.
#    If the combined file exists, proceed to step 6.
#    If the combined file doesn't exist, skip to step 15.
#
#Step 7. Move the combined file to the txt2kb/combined directory:
#
#    Ask the user if they want to move the combined file to the txt2kb/combined directory.
#    If the user confirms, move the combined file to the specified directory.
#    If the user declines, skip to step 15.
#
#Step 8. Navigate to the txt2kb/converted directory:
#
#    Check if the txt2kb/converted directory exists.
#    If the directory exists, navigate to it. If it doesn't exist, create it.
#    If the directory doesn't exist, print an error message and exit the script.
#
#Step 9. Create a JSON file from the latest file in the txt2kb/converted directory:
#
#    Find the most recent file in the txt2kb/converted directory.
#    Ask the user if they want to convert this latest file to JSON.
#    If the user confirms, execute the convert.py script with the latest file as an argument name to create a JSON file, with a second argument as the output name.
#    If the user declines, skip to step 15.
#

################################### ARCHIVING ./txt2kb PROJECT  #############################

#Step 10. Archive HTML files in the txt2kb directory:
#
#    Navigate back to the txt2kb directory.
#    Ask the user if they want to archive all HTML files in the txt2kb directory.
#    If the user confirms, execute the archive.py script to archive the HTML files.
#    If the user declines, skip to step 10.
#
################################### ARCHIVING ./newscollector PROJECT ######################
#
#Step 11. Check the status of the articles folder to make sure they are both processed and archived before the next job starts:
#
#    a) Count if more than 0 json files exist in the /articles directory.

#    b) Check if a folder with the date matching the json file exists in the newscollector/articles directory.
#    c) Check if a folder with the matching date exists ./txt2kb directory.

#    d) Check if html files exist in ./txt2kb

#    e) Check for matching files in all both directories of both projects.



#     If a is false and b + c are true and d is false, and e is true, then it means we have archived both project directories, and we can go to step 12.

#     If a is true, and b is true, likely we are running newscollector more than once the same day. process the json articles

#     If a is true, and b is false, likely we ran the newscollector for the first time and have processed html files.
#           If d and e are false, process the json articles.
#           If d and e are true, we can archive them.

#     If a is false, and b is true but c, d, and e are false, it means we may have archived w/out processing the json files to html.
#           check folder with todays date in newscollector.
#           check if there are htmls ./txt2kb and check their UUID for a match.
#                 If yes, then they have already been processed. Articles have been archived and we can run newscollector.py
#                 If no, then process the json articles inside that folder.

#     If a is false, and b is false, we can start the newcollector, but let's check for html files in ./txt2kb, and for any matching folders with today's date in ./txt2kb. But we can probably start the newscollector.py
#             If yes, and htmls are found then go to step 4
#             If no, then we can run newscollector.py

#     If the folder with matching date in newscollector/articles doesn't exist, run remove_duplicates.py and then run archive.py in the same directory.
#


############################### HANDLING UNFINISHED PROCESSES ##############################

#    If there are json files that exist in the articles directory, and a folder with the same date exists, it means that we processed and archived some files on the same day, and ran thenews collection again without finishing the archiving. This means that there may be corresponding html files in the ./txt2kb that may need processing and archiving as well. Go to step 4.

# Implementation to check corresponding files with UUID. (Future work)

#Check if there are html files with same UUID as the json files in the ./tx2kb/, go to step 5
#      if not, check if a folder with the same date exists in ./txt2kb,
#           if yes, check if a combined_network_YYYYMMDDTT.html exists in the combined directory. If it's already there, it means that we can archive them to that directory. but we should probably run it anyway. Go to step 5. If not, we need to combine and conver them first, then archive them. Go to step 5
#           if no, it means that we can process the files and archive them. Go to step 5

#    If there are json files that exist in the articles directory and a folder with the same date doesn't exist in the articles directory, it means that we haven't archived them yet, and probably just finished processing the html files.
     # check that html files exist in ./txt2kb with the same date and number of files.
          # if yes, then we can archive the files in the articles folder.
          # if no, then we can process them.

#############################################################################################

#Step 12. Processing and Archiving is finished for both project directories. Print the log.
#    Ask to start newscollector.py script.
#
#Step 13. Execute the newscollector.py script:
#    Navigate to the newscollector directory.
#    Execute the newscollector.py script.
#
#Step 14. Execute the process.py script:
#
#    Ask the user if they want to run the process.py script inside the txt2kb/combined directory.
#    If the user confirms, navigate to the txt2kb/combined directory and execute the process.py script.
#    If the user declines, proceed to step 15.
#
#Step 15. Exit the script.

####################################### CODE #############################################

# Function to read config file
read_config() {
  local config_file=$1
  if [ -f "$config_file" ]; then
    source <(grep = "$config_file")
  else
    echo "Config file $config_file not found. Exiting."
    exit 1
  fi
}

# Function to initialize the log file
initialize_log() {
  local log_file="script_log_$(date +%Y%m%d_%H%M%S).log"
  echo "Script execution log - $(date)" > "$log_file"
  echo "$log_file"
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
  if [ -d "$dir" ]; then
    cd "$dir" || exit
    echo "Moved to the directory: $PWD." >> "$log_file"
  else
    echo "Directory '$dir' not found. Exiting." >> "$log_file"
    exit 1
  fi
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
    echo "Moved file: $file from $source_dir to $target_dir" >> "$log_file"
  done
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
      echo "User choice: $choice" >> "$log_file"
      [[ "$choice" == "q" ]] && return 1
    fi
    cd "$directory" || exit
    python3 "$script"
    echo "$script executed in $directory." >> "$log_file"
  else
    echo "$script not found in $directory. Skipping execution." >> "$log_file"
  fi
}

# Function to count files in a directory
count_files() {
  local directory=$1
  local pattern=$2
  local count=$(ls $directory/$pattern 2>/dev/null | wc -l)
  echo "$count"
}

# Function to check if a folder exists
check_folder_exists() {
  local folder=$1
  local log_file=$2
  if [ -d "$folder" ]; then
    echo "Folder $folder exists." >> "$log_file"
    return 0
  else
    echo "Folder $folder does not exist." >> "$log_file"
    return 1
  fi
}

# Function to check for file existence with pattern
check_files_pattern_exist() {
  local directory=$1
  local pattern=$2
  local files=($(ls $directory/$pattern 2>/dev/null))
  [ ${#files[@]} -gt 0 ]
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
    echo "JSON created from the latest file: $output_file" >> "$log_file"
  else
    echo "$convert_script not found in $directory. Skipping JSON creation." >> "$log_file"
  fi
}

# Function to check HTML file count and execute combine.py
process_html_files() {
  local directory=$1
  local combine_script=$2
  local skip_confirmation=$3
  local log_file=$4
  local html_count=$(count_files "$directory" "*.html")
  echo "HTML file count: $html_count" >> "$log_file"
  if [ "$html_count" -gt 20 ]; then
    echo "More than 20 HTML files found." >> "$log_file"
    execute_script "$combine_script" "$directory" "$skip_confirmation" "$log_file"
  else
    echo "Less than or equal to 20 HTML files found. Skipping combine.py execution." >> "$log_file"
  fi
}

# Function to check if combined file exists and process it
process_combined_file() {
  local source_directory=$1
  local target_directory=$2
  local process_script=$3
  local skip_confirmation=$4
  local log_file=$5
  if check_files_pattern_exist "$source_directory" "combined*"; then
    echo "Combined file found." >> "$log_file"
    move_files "$source_directory" "$target_directory" "combined*" "$log_file"
    execute_script "$process_script" "$target_directory" "$skip_confirmation" "$log_file"
  else
    echo "No combined file found. Skipping processing." >> "$log_file"
  fi
}

# Function to check the status of articles folder
check_articles_folder() {
  local articles_directory=$1
  local txt2kb_directory=$2
  local log_file=$3
  local current_date=$(date +%Y_%m_%d)
  if check_folder_exists "$articles_directory/$current_date" "$log_file" && check_folder_exists "$txt2kb_directory/$current_date" "$log_file"; then
    echo "Both $articles_directory/$current_date and $txt2kb_directory/$current_date exist. Ready to run newscollector." >> "$log_file"
    return 0
  else
    echo "Either $articles_directory/$current_date or $txt2kb_directory/$current_date does not exist. Skipping newscollector execution." >> "$log_file"
    return 1
  fi
}

# Function to execute newscollector.py
execute_newscollector() {
  local newscollector_script=$1
  local newscollector_directory=$2
  local skip_confirmation=$3
  local log_file=$4
  execute_script "$newscollector_script" "$newscollector_directory" "$skip_confirmation" "$log_file"
}


# Sequence

main() {
  local skip_confirmation=$1
  local config_file=$2
  local log_file=$(initialize_log)

  # Step 1. Read config file
  read_config "$config_file"

  # Step 2: Activate virtual environment
  activate_venv "$venv_directory" "$log_file"

  # Step 3: Navigate to txt2kb directory
  navigate_to_directory "$txt2kb_root" "$log_file"

  # Step 4: Check the number of HTML files in the current directory
  # process_html_files "$txt2kb_root" <- let's break this process function down.

  # Step 5: Execute the combine.py script
   "$combine_script" "$skip_confirmation" "$log_file"

  # Step 6: Check if combined file exists:
  #process_combined_file "$txt2kb_root" "$txt2kb_combined" "$process_script" "$skip_confirmation" "$log_file" # Let's break this function down for later reuse.

  # Step 7: Move the combined file to the txt2kb/combined directory:


  # Step 8: Navigate to the txt2kb/converted directory:   :
  navigate_to_directory "$txt2kb_converted" "$log_file"

  # Step 9: Create JSON from the latest file in the txt2kb_converted directory
  create_json_from_latest_file "$txt2kb_converted" "$convert_script" "$log_file"

  # Step 10: Archive HTML files in the txt2kb directory:
  execute_script "$archive_script" "$txt2kb_root" "$skip_confirmation" "$log_file"

  # Finished Processing and Archiving ./txt2kb Print Log file

########################################################################################

  #Step 11. Check the status of the articles folder to make sure they are both processed and archived before the next job starts:
  #


  #    a) Count if more than 0 json files exist in the /articles directory.

  #    b) Check if a folder with the current date matching the json file exists in the newscollector/articles directory.
  #    c) Check if a folder with the current date exists ./txt2kb directory.
  #    d) Check if html files with matching UUID exist in ./txt2kb directory or in folder with current date in ./txt2kb

  #     If a is false and b + c are true, then it means we have archived both project directories, and we can go to step 12

  #     If a is true, and b is true, process the json articles

  #     If a is true, and b is false, process the json articles

  #     If a is false, and b is true but c is false, it means we may have archive w/out processing the json files to html.
  #           check folder with todays date in newscollector.
  #           check if there are htmls ./txt2kb and check their UUID for a match.
  #                 If yes, then they have already been processed. Articles have been archived.
  #     If a is false, and b is false, and c is false, likely we can start the newcollector, but let's check for html files in ./txt2kb, and for any matching folders with today's date in ./txt2kb. But we can probably start the newscollector.py
  #             If yes, and htmls are found then go to step 4

  #    As a basic rule, if the folder with matching date in newscollector/articles doesn't exist, run remove_duplicates.py and then run archive.py in the same directory.
  #


  if check_articles_folder "$newscollector_root/articles" "$txt2kb_root" "$log_file"; then
    # Step 12: Execute newscollector.py
    execute_newscollector "$newscollector_script" "$newscollector_root" "$skip_confirmation" "$log_file"
  fi
}

# Check if the -y argument is provided
if [ "$1" == "-y" ]; then
  main "-y" "config.ini"
else
  main "" "config.ini"
fi

echo "Script execution completed. Log file: $log_file"
