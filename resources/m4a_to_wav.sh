#!/bin/bash

# Directory containing .m4a files
DIRECTORY="./robot"

# Loop through all .m4a files in the directory
for file in "$DIRECTORY"/*.m4a; do
  # Get the base name of the file (without extension)
  base_name=$(basename "$file" .m4a)

  # Convert .m4a to .wav using ffmpeg
  ffmpeg -i "$file" "$DIRECTORY/$base_name.wav"
done