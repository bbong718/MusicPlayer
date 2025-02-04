# Command-Line Audio Player
A simple Python-based command-line audio player that supports various audio formats. This tool allows users to play individual audio files or all audio files within a specified directory.

## Features
Play individual audio files  
Play all audio files in a specified directory  
Supports multiple audio formats (MP3, WAV, OOG, etc...)  

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
pytohn3 playMusic.py [-h] [--wait-timeout WAIT_TIMEOUT] [--file FILE | --dir DIR]
```

### Examples
**Play an individual MP3 file:**

```
python audio_player.py --file|-f /path/to/song.mp3
```

**Play all audio files in a directory:**

```
python audio_player.py --dir|-d /path/to/audio/directory/
```

## Limitations and Suggestions
Currently for the `--dir|-d` options it plays all files one by one. There is no screen refresh, it just continues with the next file. It does await users input to continue, or uses a timeout to go to the next track.

## Contributing
Contributions are welcome! If you have suggestions for improving this tool or encounter any issues, please open an issue or submit a pull request on the GitHub repository

## License
This project is distributed under the MIT License. See LICENSE for more details.