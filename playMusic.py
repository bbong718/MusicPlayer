import pygame
from os import path, walk
import sys
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3._util import ID3TagError as ID3Error, error
from tqdm import tqdm
from timeit import default_timer as timer
import threading
import argparse
from signal import signal, SIGINT, SIGTERM, default_int_handler
import time

# For handling warning messages
import logging
logger = logging.getLogger(__name__)

class AudioPlayer():
    def __init__(self, timeout=10):
        self.metadata = {}
        self.progress_bar = None
        self.audio_files = []
        self.timeout = timeout # Default timeout in seconds

    def get_audio_metadata(self, file_path):
        """Extract metadata from Audio file."""
        try:
            # Read tags using mutagen
            audio = mutagen.File(file_path, easy=True)
            if not audio:
                raise ValueError(f"Could not read file: {file_path}")
            
            # Basic metadata extraction
            self.metadata['length'] = round(audio.info.length, 2)
            self.metadata['bitrate'] = int(audio.info.bitrate / 1000)  # in Kbps
            self.metadata['sample_rate'] = audio.info.sample_rate
            self.metadata['channels'] = audio.info.channels if hasattr(audio.info, 'channels') else "Unknown"
            
            # Extract ID3 tags (artist, title, etc.)
            try:
                # Get all frames
                id3_tags = audio.tags
                
                if id3_tags is not None and isinstance(id3_tags, dict):
                    self.metadata['title'] = str(id3_tags.get("TIT2", [""])[0])  # Title
                    self.metadata['artist'] = str(id3_tags.get("TPE1", [""])[0])  # Artist
                    self.metadata['album'] = str(id3_tags.get("TALB", [""])[0])   # Album
                    self.metadata['genre'] = str(id3_tags.get("TCON", [""])[0])   # Genre
                    
                else:
                    print(f"[{len(self.audio_files)}] No ID3 tags found. Path: {file_path}, length: {self.metadata['length']}/s")
                    for key in ['title', 'artist', 'album', 'genre']:
                        self.metadata[key] = "Unknown"
            
            except (ID3Error, error):
                print("\nError reading ID3 tags. Displaying basic information.\n")
                self.metadata.update({
                    'title':    path.basename(file_path),
                    'artist':  "Unknown",
                    'album':   "Unknown",
                    'genre':   "Unknown"
                })
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
    

    def display_metadata(self, file_path):
        """Print audio file metadata."""
        print("\nPlaying: ", end='')
        if self.metadata.get('title'):
            print(f"{self.metadata['title']} - {self.metadata['artist']}")
        else:
            print(path.basename(file_path))
        
        # Print remaining fields
        if self.metadata['album']:   print(f"Album:       {self.metadata['album']}")
        if self.metadata['genre']:   print(f"Genre:       {self.metadata['genre']}")
        print(f"Duration (s):  {self.metadata['length']:.2f}s")
        print(f"Bitrate:      {self.metadata['bitrate']} Kbps")
        print(f"Sample Rate:  {self.metadata['sample_rate']} Hz")
        print(f"Channels:     {self.metadata['channels']}\n")
    
    def play_audio(self, file_path, metadata=None):
        """Play audio file with progress bar."""
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()
        
        try:
            # Load the audio file
            pygame.mixer.music.load(file_path)
            
        except Exception as e:
            print(f"Error loading file: {e}")
            return

        if metadata is not None:
            self.metadata = metadata
        
        # Print metadata
        self.display_metadata(file_path)
        
        # Start progress bar thread
        total_length = self.metadata.get('length', 0)

        pb_thread = threading.Thread(target=self.update_progress_bar, args=(total_length,))
        pb_thread.start()
        
        # Play the audio file
        pygame.mixer.music.play(1)  # play once
        while pygame.mixer.music.get_busy():
            pass
        
        # Stop progress bar when playback stops
        if self.progress_bar:
            self.progress_bar.close()

        # Clean up
        pygame.mixer.music.unload()

    def update_progress_bar(self, total_length=0.0):
        """Update tqdm progress bar during playback."""
        if total_length == 0:
            print("Unable to show progress bar (unknown length)")
            return
        
        with tqdm(total=total_length, unit='s', desc="Playing", dynamic_ncols=True) as pb:
            self.progress_bar = pb
            start_time = pygame.time.get_ticks() / 1000.0
            
            while True:
                current_time = pygame.time.get_ticks() / 1000.0
                elapsed_time = current_time - start_time

                # Limiting to 3 decimal places to prevent excessive precision
                rounded_elapsed = round(elapsed_time, 3)
                
                # Prevent very small overflows due to timing inaccuracies
                if elapsed_time >= total_length * (1 + 1E-6):
                    break
                    
                if pygame.mixer.music.get_busy():
                    # Ensure the progress doesn't exceed total length
                    pb_pos = min(rounded_elapsed, total_length )
                    pb.update(pb_pos - pb.n)   # Update only the difference
                
            # After loop, properly close the progress bar to prevent any lingering state
            pb.close()

    def get_audio_files(self, directory):
        """
        Scan given directory recursively and return list of audio files with metadata.
        """
        supported_formats = ['mp3', 'wav', 'ogg']  # Add more formats as needed
        
        for root, _, files in walk(directory):
            for file_name in files:
                # Check if file has valid extension
                ext = path.splitext(file_name)[1][1:].lower()
                if ext in supported_formats:
                    file_path = path.join(root, file_name)
                    
                    # Try to extract metadata
                    try:
                        self.get_audio_metadata(file_path)
                        self.audio_files.append({
                            'path': file_path,
                            'album': self.metadata.get('album', ''),
                            'genre': self.metadata.get('genre', ''),
                            'artist': self.metadata.get('artist', ''),
                            'title': self.metadata.get('title', ''),
                            'bitrate': self.metadata.get('bitrate', 0),  # in kbps
                            'length': self.metadata.get('length', 0.0),
                            'sample_rate': self.metadata.get('sample_rate', 0),
                            'channels': self.metadata.get('channels', 0)
                        })

                    except Exception as e:
                        print(f"Error processing {file_name}: {e}")
                    
        return self.audio_files

    def play_sequence(self, audio_list):
        """
        Play each audio file in sequence with progress indication.
        """
        total_tracks = len(audio_list)
        for i, track in enumerate(audio_list, 1):
            print(f"\nPlaying {i}/{total_tracks}: [{track['artist']} - {track['title']}]")
            print(f"Bitrate: {track['bitrate']} kbps, Path: {track['path']}")
            
            # Play the file
            self.play_audio(track['path'], track)
            
            if i < total_tracks:
                self.display_next_track_and_wait(audio_list, i + 1)

    def display_next_track_and_wait(self, audio_list, next_index):
        """"Show next track info and wait for user input or timeout.
            Automatically proceeds to play the next track after the specified timeout."""
        if not audio_list:
            print("No more tracks in this sequence.")
            return

        current_index   = next_index - 1
        current_track  = audio_list[current_index]
        print(f"\nNext up: {current_index + 1}/{len(audio_list)}: {current_track['artist']} - {current_track['title']}, Path: {current_track['path']}")

        start_time = time.time()
        timeout_seconds = self.timeout
        user_input_received = False

        if not sys.stdin.isatty():
            print("Cannot run with pipe input; starting playback directly.", file=sys.stderr)
            return

        # Read input non-blocking each second without threads
        while (time.time() - start_time) < timeout_seconds and not user_input_received:
            elapsed_time = time.time()-start_time
            remaining = int(timeout_seconds - elapsed_time)
            if remaining > 0:
                print(f"Starting next track in {remaining} seconds...", end='\r')
            else:
                break

            # Non-blocking read for input
            import select
            if select.select([ sys.stdin ], [], [], 1)[0]:
                line = sys.stdin.readline()
                if line.strip() == '' and len(line) > 0:
                    user_input_received = True
            time.sleep(1)

        print("\nProceeding to the next track.", flush=True)
        return

    def signal_handler(self, sig, frame):
        print("\nExiting gracefully...")
        if self.progress_bar:
            self.progress_bar.close()
        pygame.mixer.quit()
        sys.exit(0)
            
def main(args):
    player = AudioPlayer(timeout=args.wait_timeout)

    signal(SIGINT, player.signal_handler)
    signal(SIGTERM, player.signal_handler)
    
    # Handle single file mode
    if args.file:
        try:
            if not path.exists(args.file):
                logger.error(f'File "{args.file}" does not exist.')
                exit(1)

            player.get_audio_metadata(args.file)
            print(f"\nPlaying: {player.metadata['artist']} - {player.metadata['title']}")
            print(f"Bitrate: {player.metadata['bitrate']} kbps")
            
            player.play_audio(args.file)

        except Exception as e:
            print(f"Error playing file: {e}")
        
    # Handle directory mode
    elif args.dir:
        if not path.isdir(args.dir):
            logger.error(f'Directory "{args.dir}" does not exist.')
            exit(1)
            
        audio_list = player.get_audio_files(args.dir)
        
        if audio_list:
            player.play_sequence(audio_list)  # Start playing the list
            
        else:
            print("No supported audio files found in the directory.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command-line media/audio player')
    parser.add_argument('--wait-timeout', '-wt', required=False, type=int, default=10, help='Wait time before playing next audio file.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--file', '-f', required=False, type=str, help='Single audio file.')
    group.add_argument('--dir', '-d', required=False, type=str, help='Directory of audio files.')
    args = parser.parse_args()

    # Validate args
    if not (args.file or args.dir):
        parser.print_help(sys.stderr)
        exit(0)

    main(args)