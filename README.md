# Command-Line Audio Player
A simple Python-based command-line audio player that supports various audio formats. This tool allows users to play individual audio files or all audio files within a specified directory.

## Features
Play individual audio files  
Play all audio files in a specified directory  
Supports multiple audio formats (MP3, WAV, etc.)  

## Prerequisites
Before running the script, ensure you have the following installed:

Python: Version 3.6 or higher  
Pygame: A Python library for multimedia applications  

## Installation
Install Python if it's not already installed on your system.  
Install Pygame using pip:
```
pip install pygame
```
## Usage
The script can be executed from the command line with the following syntax:

```
python3 audio_player.py --dir|-d <path_to_audio_file_or_directory>
```

### Examples
**Play an individual MP3 file:**

```
python audio_player.py --file|-f /path/to/song.mp3
```

**Play all audio files in a directory:**

```
python audio_player.py /path/to/audio/directory/
```

## Limitations and Suggestions
**Metadata Extraction**  
Currently, the script uses Pygame for audio playback, which does not support metadata extraction (e.g., artist, title) from MP3 files. If you require this functionality, consider using alternative libraries like mutagen or ** eyed3**, which provide robust metadata handling.

To install mutagen:

```
pip3 install mutagen
```

## Contributing
Contributions are welcome! If you have suggestions for improving this tool or encounter any issues, please open an issue or submit a pull request on the GitHub repository

## License
This project is distributed under the MIT License. See LICENSE for more details.