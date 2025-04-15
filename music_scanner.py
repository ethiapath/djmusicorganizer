import os
import mimetypes
import logging
import traceback
from track import Track
from nml_handler import NMLHandler
from nml_to_rekordbox import NMLToRekordboxConverter

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
        if not os.path.exists(folder_path):
            logger.error(f"Folder does not exist: {folder_path}")
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")
        
        if folder_path not in self.folders:
            self.folders.append(folder_path)
            logger.debug(f"Added folder: {folder_path}")
        else:
            logger.debug(f"Folder already added: {folder_path}")
            
    def is_music_file(self, file_path):
        """Check if a file is a music file"""
        logger.debug(f"Checking if file is music: {file_path}")
        
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
    
    # Add to MusicScanner class
    def migrate_format(self, source_file, target_file, source_format, target_format, options, progress_callback=None):
        """Migrate between different DJ software formats"""
        if progress_callback:
            progress_callback(0, f"Reading {source_format} file...", 0, 100)
        
        # Read source file
        tracks = []
        if source_format == "nml":
            tracks = self._read_nml_file(source_file)
        elif source_format == "xml":
            tracks = self._read_rekordbox_xml(source_file)
        elif source_format == "csv":
            tracks = self._read_serato_csv(source_file)
        elif source_format == "m3u":
            tracks = self.read_m3u_playlist(source_file)
        
        if progress_callback:
            progress_callback(30, f"Processing {len(tracks)} tracks...", 30, 100)
        
        # Process tracks according to options
        preserve_cues = options.get("preserve_cues", "Preserve all cue points")
        handle_missing = options.get("handle_missing", "Skip missing files")
        
        processed_tracks = []
        total = len(tracks) if tracks else 0
        
        for i, track in enumerate(tracks):
            if progress_callback:
                progress_callback(30 + (i / total * 40) if total > 0 else 50, 
                                f"Processing track {i+1}/{total}", i+1, total)
            
            # Handle missing files
            if not os.path.exists(track.file_path):
                if handle_missing == "Skip missing files":
                    continue
                elif handle_missing == "Attempt to locate":
                    # Try to find the file by name in known folders
                    found = False
                    for folder in self.folders:
                        for root, _, files in os.walk(folder):
                            if os.path.basename(track.file_path) in files:
                                new_path = os.path.join(root, os.path.basename(track.file_path))
                                track.file_path = new_path
                                found = True
                                break
                        if found:
                            break
                    if not found and handle_missing == "Skip missing files":
                        continue
            
            # Handle cue points
            if preserve_cues == "Preserve only first 8 cues" and hasattr(track, 'cue_points'):
                track.cue_points = track.cue_points[:8]
            elif preserve_cues == "Skip cue points" and hasattr(track, 'cue_points'):
                track.cue_points = []
            
            processed_tracks.append(track)
        
        if progress_callback:
            progress_callback(70, f"Writing {target_format} file...", 70, 100)
        
        # Write target file
        if target_format == "nml":
            self._write_nml_file(target_file, processed_tracks)
        elif target_format == "xml":
            self._write_rekordbox_xml(target_file, processed_tracks)
        elif target_format == "csv":
            self._write_serato_csv(target_file, processed_tracks)
        elif target_format == "m3u":
            self.write_m3u_playlist(target_file, processed_tracks, use_utf8=False)
        elif target_format == "m3u8":
            self.write_m3u_playlist(target_file, processed_tracks, use_utf8=True)
        
        if progress_callback:
            progress_callback(100, "Migration complete", 100, 100)
        
        return processed_tracks
        
    def _read_nml_file(self, file_path):
        """Read tracks from Traktor NML file"""
        try:
            # Use existing NML handler
            self.nml_handler.load_nml(file_path)
            nml_tracks = self.nml_handler.get_collection_tracks()
            
            # Convert NML tracks to Track objects
            tracks = []
            for nml_track in nml_tracks:
                try:
                    file_path = nml_track['file_path']
                    if os.path.exists(file_path):
                        track = Track(file_path)
                        track.id = nml_track['id']
                        # Copy any additional metadata from NML
                        if 'cue_points' in nml_track:
                            track.cue_points = nml_track['cue_points']
                        tracks.append(track)
                except Exception as e:
                    logger.error(f"Error importing track {nml_track.get('file_path', 'unknown')}: {str(e)}")
            
            return tracks
        except Exception as e:
            logger.error(f"Error reading NML file: {str(e)}")
            raise

    def _write_nml_file(self, file_path, tracks):
        """Write tracks to Traktor NML format"""
        try:
            self.nml_handler.create_new_nml()
            
            # Add all tracks to collection
            for track in tracks:
                track.id = self.nml_handler.add_track_to_collection(track)
            
            # Save the NML file
            self.nml_handler.save_nml(file_path)
        except Exception as e:
            logger.error(f"Error writing NML file: {str(e)}")
            raise
            
    def _read_rekordbox_xml(self, file_path):
        """Read tracks from Rekordbox XML file"""
        # Basic implementation - would need to be expanded
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            tracks = []
            collection = root.find("COLLECTION")
            if collection is not None:
                for track_elem in collection.findall("TRACK"):
                    try:
                        location = track_elem.get("Location", "")
                        # Convert from file://localhost/ format
                        if location.startswith("file://localhost/"):
                            file_path = location[16:]
                        else:
                            file_path = location
                        
                        if os.path.exists(file_path) and self.is_music_file(file_path):
                            track = Track(file_path)
                            # Set additional metadata
                            track.id = track_elem.get("TrackID", "")
                            tracks.append(track)
                    except Exception as e:
                        logger.error(f"Error importing Rekordbox track: {str(e)}")
            
            return tracks
        except Exception as e:
            logger.error(f"Error reading Rekordbox XML: {str(e)}")
            raise
            
    def _write_rekordbox_xml(self, file_path, tracks):
        """Write tracks to Rekordbox XML format"""
        try:
            # If we have an NML file to convert directly
            if len(tracks) > 0 and hasattr(tracks[0], 'source_nml'):
                # Use the converter directly
                converter = NMLToRekordboxConverter()
                converter.convert_nml_to_rekordbox(tracks[0].source_nml, file_path)
                return
            
            # Otherwise create a temporary NML and convert it
            temp_nml = os.path.join(os.path.dirname(file_path), "temp_conversion.nml")
            self._write_nml_file(temp_nml, tracks)
            
            # Use the converter
            converter = NMLToRekordboxConverter()
            converter.convert_nml_to_rekordbox(temp_nml, file_path)
            
            # Clean up temp file
            if os.path.exists(temp_nml):
                os.remove(temp_nml)
        except Exception as e:
            logger.error(f"Error writing Rekordbox XML: {str(e)}")
            raise
            
    def _read_serato_csv(self, file_path):
        """Read tracks from Serato CSV file"""
        try:
            import csv
            
            tracks = []
            with open(file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        # Serato CSV typically has a 'path' or 'location' column
                        file_path = row.get('path', row.get('location', ''))
                        if file_path and os.path.exists(file_path) and self.is_music_file(file_path):
                            track = Track(file_path)
                            tracks.append(track)
                    except Exception as e:
                        logger.error(f"Error importing Serato track: {str(e)}")
            
            return tracks
        except Exception as e:
            logger.error(f"Error reading Serato CSV: {str(e)}")
            raise
            
    def _write_serato_csv(self, file_path, tracks):
        """Write tracks to Serato CSV format"""
        try:
            import csv
            
            fieldnames = ['name', 'artist', 'album', 'genre', 'bpm', 'key', 'path']
            
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for track in tracks:
                    writer.writerow({
                        'name': track.title,
                        'artist': track.artist,
                        'album': track.album if hasattr(track, 'album') else '',
                        'genre': track.genre,
                        'bpm': track.bpm,
                        'key': track.key,
                        'path': track.file_path
                    })
        except Exception as e:
            logger.error(f"Error writing Serato CSV: {str(e)}")
            raise
            
    def read_m3u_playlist(self, file_path):
        """Read tracks from M3U or M3U8 playlist file"""
        logger.info(f"Reading M3U playlist: {file_path}")
        try:
            tracks = []
            
            # Determine base directory for resolving relative paths
            base_dir = os.path.dirname(file_path)
            
            with open(file_path, 'r', encoding='utf-8' if file_path.lower().endswith('.m3u8') else 'latin-1') as f:
                lines = f.readlines()
                
                current_title = None
                for line in lines:
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        # Extract title from EXTINF tag if present
                        if line.startswith('#EXTINF:'):
                            # Format: #EXTINF:duration,title
                            parts = line.split(',', 1)
                            if len(parts) > 1:
                                current_title = parts[1].strip()
                        continue
                    
                    # Process file path
                    track_path = line
                    
                    # Handle relative paths
                    if not os.path.isabs(track_path):
                        track_path = os.path.join(base_dir, track_path)
                        
                    # Normalize path (handle ../ etc.)
                    track_path = os.path.normpath(track_path)
                    
                    # Check if the file exists and is a music file
                    if os.path.exists(track_path) and self.is_music_file(track_path):
                        try:
                            track = Track(track_path)
                            # If we found a title in EXTINF, use it
                            if current_title:
                                track.title = current_title
                                current_title = None
                            tracks.append(track)
                            logger.debug(f"Added track from M3U: {track_path}")
                        except Exception as e:
                            logger.error(f"Error loading track {track_path}: {str(e)}")
                    else:
                        logger.warning(f"File not found or not a music file: {track_path}")
            
            logger.info(f"Loaded {len(tracks)} tracks from M3U playlist")
            return tracks
        except Exception as e:
            logger.error(f"Error reading M3U playlist: {str(e)}")
            raise
            
    def write_m3u_playlist(self, file_path, tracks, use_utf8=True):
        """Write tracks to M3U or M3U8 playlist format"""
        logger.info(f"Writing M3U playlist: {file_path}")
        try:
            # Determine if we should use UTF-8 (M3U8) or Latin-1 (M3U) encoding
            if use_utf8 or file_path.lower().endswith('.m3u8'):
                encoding = 'utf-8'
                if not file_path.lower().endswith('.m3u8'):
                    file_path = file_path + '.m3u8'
            else:
                encoding = 'latin-1'
                if not file_path.lower().endswith('.m3u'):
                    file_path = file_path + '.m3u'
            
            # Get base directory for making paths relative
            base_dir = os.path.dirname(file_path)
            
            with open(file_path, 'w', encoding=encoding) as f:
                # Write M3U header
                f.write("#EXTM3U\n")
                
                for track in tracks:
                    # Write extended info
                    duration = 0  # We don't have actual duration info
                    title = f"{track.artist} - {track.title}" if track.artist else track.title
                    f.write(f"#EXTINF:{duration},{title}\n")
                    
                    # Try to make the path relative to the playlist location
                    try:
                        rel_path = os.path.relpath(track.file_path, base_dir)
                        # If the relative path starts going up directories too much,
                        # just use the absolute path
                        if rel_path.startswith('..') and rel_path.count('..') > 2:
                            f.write(f"{track.file_path}\n")
                        else:
                            f.write(f"{rel_path}\n")
                    except:
                        # Fallback to absolute path if there's any issue
                        f.write(f"{track.file_path}\n")
            
            logger.info(f"Successfully wrote {len(tracks)} tracks to M3U playlist")
            return file_path
        except Exception as e:
            logger.error(f"Error writing M3U playlist: {str(e)}")
            raise
    
    def export_to_m3u(self, filepath):
        """Export tracks to M3U/M3U8 playlist format"""
        try:
            # Determine if we should use UTF-8 (M3U8) or Latin-1 (M3U) encoding based on file extension
            use_utf8 = filepath.lower().endswith('.m3u8')
            return self.write_m3u_playlist(filepath, self.tracks, use_utf8)
        except Exception as e:
            logger.error(f"Error exporting to M3U/M3U8: {str(e)}")
            raise
    
    def import_from_m3u(self, filepath):
        """Import tracks from M3U/M3U8 playlist format"""
        try:
            imported_tracks = self.read_m3u_playlist(filepath)
            
            # Process each track, adding to the main tracks list
            successful_tracks = 0
            total_tracks = len(imported_tracks)
            
            for i, track in enumerate(imported_tracks):
                try:
                    self.tracks.append(track)
                    successful_tracks += 1
                except Exception as e:
                    logger.error(f"Error importing track {track.file_path}: {str(e)}")
                
                if self.progress_callback:
                    progress_percent = int((i + 1) / total_tracks * 100)
                    self.progress_callback(progress_percent, f"Imported {successful_tracks} of {total_tracks}")
            
            logger.info(f"Successfully imported {successful_tracks} of {total_tracks} tracks from M3U/M3U8")
        except Exception as e:
            logger.error(f"Error importing from M3U/M3U8: {str(e)}")
            raise