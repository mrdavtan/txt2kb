import os
import shutil
from datetime import datetime

# Define the directory path where the HTML files are located
source_directory = "./."

# Iterate over the files in the source directory
for filename in os.listdir(source_directory):
    if filename.endswith("_network.html"):
        file_path = os.path.join(source_directory, filename)

        try:
            # Split the filename into parts
            parts = filename.split("_")

            # Find the date part by iterating from the end
            date_string = None
            for part in reversed(parts):
                if len(part) == 8 and part.isdigit():
                    date_string = part
                    break

            if date_string:
                file_date = datetime.strptime(date_string, "%Y%m%d").strftime("%Y-%m-%d")

                # Create the destination directory path
                destination_directory = os.path.join(source_directory, file_date)

                # Check if the directory already exists
                if not os.path.exists(destination_directory):
                    # Create the directory if it doesn't exist
                    os.makedirs(destination_directory)
                    print(f"Created directory: {destination_directory}")

                # Move the file to the destination directory
                destination_path = os.path.join(destination_directory, filename)
                shutil.move(file_path, destination_path)
                print(f"Moved {filename} to {destination_directory}")
            else:
                print(f"Skipping file {filename} due to missing date format.")
        except ValueError:
            print(f"Skipping file {filename} due to invalid date format.")
