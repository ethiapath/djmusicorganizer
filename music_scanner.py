import os
import mimetypes
import logging
import traceback
from track import Track
from nml_handler import NMLHandler

# Get logger for this module
logger = logging.getLogger(__name__)

class MusicScanner:
    def __init__(self):
        logger.debug("Initializing MusicScanner")
        self.tracks = []
        self.folders = []
        self.nml_handler = NMLHandler()
        self.supported_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac'}
        self.progress_callback = None
        self.cancel_scan_requested = False
        
        # Initialize mimetypes
        mimetypes.init()
        # Register additional MIME types that might be missing
        mimetypes.add_type('audio/flac', '.flac')
        mimetypes.add_type('audio/aac', '.aac')
        mimetypes.add_type('audio/m4a', '.m4a')
        logger.debug(f"Supported extensions: {self.supported_extensions}")
    
    def set_progress_callback(self, callback):
        """Set a callback function to report progress"""
        logger.debug("Setting progress callback")
        self.progress_callback = callback
    
    def cancel_scan(self):
        """Request to cancel the current scanning operation"""
        logger.info("Scan cancellation requested")
        self.cancel_scan_requested = True
    
    def is_scan_canceled(self):
        """Check if scan cancellation was requested"""
        return self.cancel_scan_requested
    
    def reset_cancel_flag(self):
        """Reset the cancellation flag"""
        self.cancel_scan_requested = False
    
    def add_folder(self, folder_path):
        """Add a folder to scan for music files"""
        logger.debug(f"Adding folder: {folder_path}")
        logger.debug(f"Current folders: {self.folders}")
        
        if not os.path.exists(folder_path):
            logger.error(f"Folder does not exist: {folder_path}")
            raise ValueError(f"Folder does not exist: {folder_path}")
            
        if folder_path in self.folders:
            logger.info(f"Folder already added: {folder_path}")
            return
            
        logger.info(f"Adding new folder to scan list: {folder_path}")
        self.folders.append(folder_path)
        logger.debug(f"Updated folders list: {self.folders}")
    
    def is_music_file(self, file_path):
        """Check if a file is actually a valid music file"""
        logger.debug(f"Checking if file is valid music file: {file_path}")
        try:
            # Check file size (skip if too small to be a valid music file)
            file_size = os.path.getsize(file_path)
            if file_size < 1024:  # Smaller than 1KB is probably not a music file
                logger.debug(f"Skipping file (too small): {file_path}")
                return False
                
            # Check if the file extension is supported
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.supported_extensions:
                logger.debug(f"Skipping file (unsupported extension): {file_path} - {ext}")
                return False
                
            # Check mime type
            mime_type = mimetypes.guess_type(file_path)[0]
            if mime_type and not mime_type.startswith('audio/'):
                logger.debug(f"Skipping file (not audio mimetype): {file_path} - {mime_type}")
                return False
            
            logger.debug(f"File is valid music file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error checking if file is music: {file_path} - {str(e)}")
            return False
    def scan(self):
        """Scan all added folders for music files"""
        logger.info("Starting music scan...")
        self.tracks = []
        self.cancel_scan_requested = False
        
        # First, count total files to scan for progress reporting
        total_files = 0
        music_files = []
        
        # Update progress with initial status
        if self.progress_callback:
            self.progress_callback(0, "Starting file discovery...")
        
        logger.info(f"Scanning {len(self.folders)} folders for music files...")
        for folder in self.folders:
            if self.cancel_scan_requested:
                logger.info("Scan canceled during file discovery phase")
                return
                
            logger.info(f"Scanning folder: {folder}")
            
            # Update progress with folder scanning status
            if self.progress_callback:
                self.progress_callback(0, f"Scanning folder: {folder}")
                
            try:
                for root, _, files in os.walk(folder):
                    if self.cancel_scan_requested:
                        logger.info("Scan canceled during file discovery phase")
                        return
                        
                    logger.debug(f"Checking directory: {root}")
                    
                    # Update progress with directory status
                    if self.progress_callback:
                        self.progress_callback(0, f"Scanning: {root}")
                        
                    for file in files:
                        if self.cancel_scan_requested:
                            logger.info("Scan canceled during file discovery phase")
                            return
                            
                        file_path = os.path.join(root, file)
                        file_ext = os.path.splitext(file)[1].lower()
                        if file_ext in self.supported_extensions:
                            logger.debug(f"Found potential music file: {file_path}")
                            # Do a preliminary check on the extension
                            if self.is_music_file(file_path):
                                total_files += 1
                                music_files.append(file_path)
                                logger.debug(f"Confirmed valid music file: {file_path}")
                            else:
                                logger.debug(f"Skipping invalid music file: {file_path}")
            except Exception as e:
                logger.error(f"Error scanning folder {folder}: {str(e)}", exc_info=True)
        
        if self.cancel_scan_requested:
            logger.info("Scan canceled after file discovery phase")
            return
            
        logger.info(f"Found {total_files} valid music files to process")
        
        # Update progress with file count
        if self.progress_callback:
            self.progress_callback(0, f"Found {total_files} music files to process")
            
        # Now process the files with progress updates
        processed_files = 0
        for file_path in music_files:
            if self.cancel_scan_requested:
                logger.info(f"Scan canceled after processing {processed_files} of {total_files} files")
                return
                
            try:
                logger.debug(f"Processing file {processed_files + 1} of {total_files}: {file_path}")
                
                # Update progress before processing the file
                if self.progress_callback and total_files > 0:
                    progress_percent = int((processed_files / total_files) * 100)
                    logger.debug(f"Progress: {progress_percent}%")
                    # Pass additional info about current file and total files
                    self.progress_callback(progress_percent, file_path, processed_files + 1, total_files)
                
                track = Track(file_path)
                self.tracks.append(track)
                logger.debug(f"Successfully processed: {file_path}")
                logger.debug(f"Track details: Title='{track.title}', Artist='{track.artist}', BPM={track.bpm}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}", exc_info=True)
            
            processed_files += 1
        
        if self.cancel_scan_requested:
            logger.info(f"Scan canceled after processing all files")
            return
            
        # Final progress update
        if self.progress_callback:
            self.progress_callback(100, "Completed processing files", processed_files, total_files)
            
        logger.info(f"Scan complete. Processed {processed_files} files.")
        logger.info(f"Successfully imported {len(self.tracks)} tracks.")
    
    def _scan_folder(self, folder_path):
        """Scan a single folder for music files"""
        print(f"\nScanning individual folder: {folder_path}")
        try:
            for root, _, files in os.walk(folder_path):
                print(f"Checking directory: {root}")
                for file in files:
                    file_path = os.path.join(root, file)
                    print(f"Checking file: {file_path}")
                    if self.is_music_file(file_path):
                        try:
                            print(f"Processing valid music file: {file_path}")
                            track = Track(file_path)
                            self.tracks.append(track)
                            print(f"Successfully added track: {track.title}")
                        except Exception as e:
                            print(f"Error processing {file_path}: {str(e)}")
                            print(f"Stack trace: {traceback.format_exc()}")
        except Exception as e:
            print(f"Error scanning folder {folder_path}: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
    
    def get_tracks(self):
        """Get all scanned tracks"""
        return self.tracks
    
    def filter_tracks(self, genre=None, bpm_min=None, bpm_max=None, key=None):
        """Filter tracks based on criteria"""
        filtered_tracks = self.tracks
        
        if genre:
            filtered_tracks = [t for t in filtered_tracks if t.genre and t.genre.lower() == genre.lower()]
        
        if bpm_min is not None:
            filtered_tracks = [t for t in filtered_tracks if t.bpm >= bpm_min]
        
        if bpm_max is not None:
            filtered_tracks = [t for t in filtered_tracks if t.bpm <= bpm_max]
        
        if key:
            filtered_tracks = [t for t in filtered_tracks if t.key == key]
        
        return filtered_tracks
    
    def export_to_nml(self, filepath):
        """Export tracks to Traktor NML format"""
        try:
            self.nml_handler.create_new_nml()
            
            # Add all tracks to collection
            for track in self.tracks:
                track.id = self.nml_handler.add_track_to_collection(track)
            
            # Save the NML file
            self.nml_handler.save_nml(filepath)
        except Exception as e:
            print(f"Error exporting to NML: {str(e)}")
            raise
    
    def import_from_nml(self, filepath):
        """Import tracks from Traktor NML format"""
        try:
            self.nml_handler.load_nml(filepath)
            
            # Get tracks from collection
            nml_tracks = self.nml_handler.get_collection_tracks()
            
            # Process each track, skipping any that fail
            successful_tracks = 0
            total_tracks = len(nml_tracks)
            
            for i, nml_track in enumerate(nml_tracks):
                try:
                    file_path = nml_track['file_path']
                    if os.path.exists(file_path) and self.is_music_file(file_path):
                        track = Track(file_path)
                        track.id = nml_track['id']
                        self.tracks.append(track)
                        successful_tracks += 1
                    else:
                        print(f"Skipping non-existent or non-music file: {file_path}")
                except Exception as e:
                    print(f"Error importing track {nml_track['file_path']}: {str(e)}")
                
                if self.progress_callback:
                    progress_percent = int((i + 1) / total_tracks * 100)
                    self.progress_callback(progress_percent, f"Imported {successful_tracks} of {total_tracks}")
            
            print(f"Successfully imported {successful_tracks} of {total_tracks} tracks")
        except Exception as e:
            print(f"Error importing from NML: {str(e)}")
            raise
    
    def create_playlist(self, name, tracks):
        """Create a playlist with the given tracks"""
        try:
            self.nml_handler.create_playlist(name, tracks)
        except Exception as e:
            print(f"Error creating playlist: {str(e)}")
            raise
    
    def get_playlists(self):
        """Get all playlists from the NML file"""
        try:
            return self.nml_handler.get_playlists()
        except Exception as e:
            print(f"Error getting playlists: {str(e)}")
            return [] 