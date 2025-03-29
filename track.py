import os
import logging
from mutagen import File as MutagenFile
from mutagen.flac import FLAC, FLACNoHeaderError
from mutagen.mp3 import MP3, HeaderNotFoundError
from mutagen.mp4 import MP4, MP4StreamInfoError
import librosa
import numpy as np

# Get logger for this module
logger = logging.getLogger(__name__)

class Track:
    def __init__(self, file_path):
        logger.debug(f"Initializing Track for file: {file_path}")
        self.file_path = file_path
        self.title = ""
        self.artist = ""
        self.album = ""
        self.genre = ""
        self.bpm = 0.0
        self.key = ""
        self.energy = 0
        self.duration = 0
        self.year = ""
        self.comment = ""
        self.id = None
        self.location = file_path  # Adding location property for the table
        self.is_corrupt = False
        self.error_message = ""
        
        # Load metadata
        self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from the audio file"""
        logger.debug(f"Loading metadata for: {self.file_path}")
        try:
            # First make sure the file exists and is readable
            if not os.path.exists(self.file_path):
                logger.warning(f"File does not exist: {self.file_path}")
                self.is_corrupt = True
                self.error_message = "File does not exist"
                self._set_default_metadata()
                return
                
            if not os.access(self.file_path, os.R_OK):
                logger.warning(f"File is not readable: {self.file_path}")
                self.is_corrupt = True
                self.error_message = "File is not readable"
                self._set_default_metadata()
                return
            
            # Check if the file is empty or suspiciously small
            file_size = os.path.getsize(self.file_path)
            if file_size < 1024:  # Less than 1KB
                logger.warning(f"File is too small ({file_size} bytes): {self.file_path}")
                self.is_corrupt = True
                self.error_message = f"File is too small ({file_size} bytes)"
                self._set_default_metadata()
                return
            
            file_ext = os.path.splitext(self.file_path)[1].lower()
            logger.debug(f"File type: {file_ext}")
            
            # Handle different file types
            if file_ext == '.flac':
                self._load_flac_metadata()
            elif file_ext == '.mp3':
                self._load_mp3_metadata()
            elif file_ext in ['.m4a', '.aac']:
                self._load_mp4_metadata()
            else:
                # Default fallback for other formats
                logger.debug(f"Using generic metadata loader for {file_ext}")
                self._load_generic_metadata()
                
            # Only calculate these if we don't have them already and the file isn't corrupt
            if not self.is_corrupt:
                if self.bpm == 0:
                    try:
                        logger.debug(f"Calculating BPM for: {self.file_path}")
                        self._calculate_bpm()
                    except Exception as e:
                        logger.warning(f"Could not calculate BPM for {self.file_path}: {str(e)}")
                        self.bpm = 0.0
                
                if not self.key or self.key == "Unknown":
                    try:
                        logger.debug(f"Calculating key for: {self.file_path}")
                        self._calculate_key()
                    except Exception as e:
                        logger.warning(f"Could not calculate key for {self.file_path}: {str(e)}")
                        self.key = "Unknown"
                
                # Energy calculation is optional - skip if it fails
                try:
                    logger.debug(f"Calculating energy for: {self.file_path}")
                    self._calculate_energy()
                except Exception as e:
                    logger.warning(f"Could not calculate energy for {self.file_path}: {str(e)}")
                    self.energy = 0
                
            logger.debug(f"Completed metadata load for: {self.file_path}")
            
        except Exception as e:
            logger.error(f"Error loading metadata for {self.file_path}: {str(e)}", exc_info=True)
            self.is_corrupt = True
            self.error_message = str(e)
            self._set_default_metadata()
    
    def _load_flac_metadata(self):
        """Load metadata from FLAC file"""
        logger.debug(f"Loading FLAC metadata: {self.file_path}")
        try:
            try:
                audio = FLAC(self.file_path)
            except FLACNoHeaderError as e:
                logger.warning(f"Invalid FLAC file: {self.file_path} - {str(e)}")
                self.is_corrupt = True
                self.error_message = f"Invalid FLAC file: {str(e)}"
                self._set_default_metadata()
                return
                
            self.title = audio.get('title', [self._get_filename()])[0]
            self.artist = audio.get('artist', ['Unknown Artist'])[0]
            self.album = audio.get('album', ['Unknown Album'])[0]
            self.genre = audio.get('genre', ['Unknown Genre'])[0]
            self.year = str(audio.get('date', [''])[0])
            self.comment = str(audio.get('comment', [''])[0])
            self.duration = audio.info.length if hasattr(audio.info, 'length') else 0
            
            # Get BPM from metadata
            if 'bpm' in audio:
                try:
                    self.bpm = float(audio['bpm'][0])
                except ValueError:
                    pass
            
            # Get key from metadata
            if 'key' in audio:
                self.key = audio['key'][0]
                
            logger.debug(f"Successfully loaded FLAC metadata: {self.title} by {self.artist}")
                
        except Exception as e:
            logger.error(f"Error loading FLAC metadata: {self.file_path} - {str(e)}", exc_info=True)
            self.is_corrupt = True
            self.error_message = f"Error loading FLAC metadata: {str(e)}"
            self._set_default_metadata()
    
    def _load_mp3_metadata(self):
        """Load metadata from MP3 file"""
        logger.debug(f"Loading MP3 metadata: {self.file_path}")
        try:
            try:
                audio = MP3(self.file_path)
            except HeaderNotFoundError as e:
                logger.warning(f"Invalid MP3 file: {self.file_path} - {str(e)}")
                self.is_corrupt = True
                self.error_message = f"Invalid MP3 file: {str(e)}"
                self._set_default_metadata()
                return
                
            # Extract metadata from ID3 tags
            if audio.tags:
                self.title = str(audio.tags.get('TIT2', self._get_filename()))
                self.artist = str(audio.tags.get('TPE1', 'Unknown Artist'))
                self.album = str(audio.tags.get('TALB', 'Unknown Album'))
                self.genre = str(audio.tags.get('TCON', 'Unknown Genre'))
                self.year = str(audio.tags.get('TDRC', ''))
                self.comment = str(audio.tags.get('COMM', ''))
                
                # Try to get BPM
                if 'TBPM' in audio.tags:
                    try:
                        self.bpm = float(str(audio.tags['TBPM']))
                    except ValueError:
                        pass
                
                # Try to get key
                if 'TKEY' in audio.tags:
                    self.key = str(audio.tags['TKEY'])
            
            self.duration = audio.info.length if hasattr(audio.info, 'length') else 0
                
        except Exception as e:
            logger.error(f"Error loading MP3 metadata: {self.file_path} - {str(e)}", exc_info=True)
            self.is_corrupt = True
            self.error_message = f"Error loading MP3 metadata: {str(e)}"
            self._set_default_metadata()
    
    def _load_mp4_metadata(self):
        """Load metadata from M4A/AAC file"""
        logger.debug(f"Loading MP4 metadata: {self.file_path}")
        try:
            try:
                audio = MP4(self.file_path)
            except MP4StreamInfoError as e:
                logger.warning(f"Invalid MP4/AAC file: {self.file_path} - {str(e)}")
                self.is_corrupt = True
                self.error_message = f"Invalid MP4/AAC file: {str(e)}"
                self._set_default_metadata()
                return
                
            # Extract metadata
            self.title = audio.get('\xa9nam', [self._get_filename()])[0]
            self.artist = audio.get('\xa9ART', ['Unknown Artist'])[0]
            self.album = audio.get('\xa9alb', ['Unknown Album'])[0]
            self.genre = audio.get('\xa9gen', ['Unknown Genre'])[0]
            self.year = str(audio.get('\xa9day', [''])[0])
            self.comment = str(audio.get('\xa9cmt', [''])[0])
            self.duration = audio.info.length if hasattr(audio.info, 'length') else 0
            
            # Try to get BPM
            if 'tmpo' in audio:
                try:
                    self.bpm = float(audio['tmpo'][0])
                except ValueError:
                    pass
                
        except Exception as e:
            logger.error(f"Error loading MP4 metadata: {self.file_path} - {str(e)}", exc_info=True)
            self.is_corrupt = True
            self.error_message = f"Error loading MP4 metadata: {str(e)}"
            self._set_default_metadata()
    
    def _load_generic_metadata(self):
        """Load metadata using generic mutagen approach"""
        logger.debug(f"Loading generic metadata: {self.file_path}")
        try:
            try:
                audio = MutagenFile(self.file_path)
            except Exception as e:
                logger.warning(f"Unable to read file format: {self.file_path} - {str(e)}")
                self.is_corrupt = True
                self.error_message = f"Unable to read file format: {str(e)}"
                self._set_default_metadata()
                return
                
            if audio is None:
                logger.warning(f"Unable to read file format: {self.file_path}")
                self.is_corrupt = True
                self.error_message = "Unable to read file format"
                self._set_default_metadata()
                return
                
            # Get duration
            self.duration = audio.info.length if hasattr(audio.info, 'length') else 0
            
            # Try to extract metadata from tags
            if hasattr(audio, 'tags') and audio.tags:
                # Different tag formats use different dict-like interfaces
                if isinstance(audio.tags, dict):
                    tag_dict = audio.tags
                else:
                    tag_dict = {k: v for k, v in audio.tags}
                
                # Try to get common metadata
                # Note: tag keys will vary by format
                for title_key in ['title', 'TIT2', 'NAME']:
                    if title_key in tag_dict:
                        self.title = str(tag_dict[title_key][0])
                        break
                else:
                    self.title = self._get_filename()
                    
                for artist_key in ['artist', 'TPE1', 'ARTIST']:
                    if artist_key in tag_dict:
                        self.artist = str(tag_dict[artist_key][0])
                        break
                else:
                    self.artist = "Unknown Artist"
                    
                # Same pattern for other metadata...
                
        except Exception as e:
            logger.error(f"Error loading generic metadata: {self.file_path} - {str(e)}", exc_info=True)
            self.is_corrupt = True
            self.error_message = f"Error loading generic metadata: {str(e)}"
            self._set_default_metadata()
    
    def _get_filename(self):
        """Get filename without extension as title"""
        return os.path.splitext(os.path.basename(self.file_path))[0]
    
    def _set_default_metadata(self):
        """Set default metadata when file can't be read"""
        self.title = self._get_filename()
        self.artist = "Unknown Artist"
        self.album = "Unknown Album"
        self.genre = "Unknown Genre"
        self.bpm = 0.0
        self.key = "Unknown"
        self.energy = 0
        self.duration = 0
        self.year = ""
        self.comment = ""
    
    def _calculate_bpm(self):
        """Calculate BPM using librosa"""
        logger.debug(f"Calculating BPM for: {self.file_path}")
        try:
            # Use a very short segment to speed up calculation and avoid memory issues
            y, sr = librosa.load(self.file_path, duration=30, offset=30, sr=22050)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            self.bpm = round(tempo, 1)
        except Exception as e:
            logger.warning(f"Could not calculate BPM for {self.file_path}: {str(e)}")
            self.bpm = 0.0
    
    def _calculate_key(self):
        """Calculate musical key using librosa"""
        logger.debug(f"Calculating key for: {self.file_path}")
        try:
            # Use a very short segment to speed up calculation and avoid memory issues
            y, sr = librosa.load(self.file_path, duration=20, offset=30, sr=22050)
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            key_raw = librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=sr)
            key_idx = np.argmax(np.mean(key_raw, axis=1))
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            self.key = keys[key_idx % 12]
        except Exception as e:
            logger.warning(f"Could not calculate key for {self.file_path}: {str(e)}")
            self.key = "Unknown"
    
    def _calculate_energy(self):
        """Calculate energy level of the track"""
        logger.debug(f"Calculating energy for: {self.file_path}")
        try:
            # Use a very short segment to speed up calculation and avoid memory issues
            y, sr = librosa.load(self.file_path, duration=15, offset=30, sr=22050)
            rms = librosa.feature.rms(y=y)
            self.energy = int(np.mean(rms) * 100)  # Scale to 0-100
        except Exception as e:
            logger.warning(f"Could not calculate energy for {self.file_path}: {str(e)}")
            self.energy = 0
    
    def to_dict(self):
        """Convert track to dictionary format"""
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'genre': self.genre,
            'bpm': self.bpm,
            'key': self.key,
            'energy': self.energy,
            'duration': self.duration,
            'year': self.year,
            'comment': self.comment,
            'file_path': self.file_path,
            'is_corrupt': self.is_corrupt,
            'error_message': self.error_message
        } 