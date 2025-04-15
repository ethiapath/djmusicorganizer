import vlc
import time

class MusicPlayer:
    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.current_media = None
        self.is_playing = False
    
    def play(self, file_path):
        """Play a music file"""
        try:
            # Create a new media instance
            self.current_media = self.instance.media_new(file_path)
            
            # Set the media to the player
            self.player.set_media(self.current_media)
            
            # Start playback
            self.player.play()
            self.is_playing = True
            
        except Exception as e:
            print(f"Error playing {file_path}: {str(e)}")
            self.is_playing = False
    
    def pause(self):
        """Pause the current playback"""
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
    
    def resume(self):
        """Resume playback"""
        if not self.is_playing:
            self.player.play()
            self.is_playing = True
    
    def stop(self):
        """Stop playback"""
        self.player.stop()
        self.is_playing = False
        self.current_media = None
    
    def set_volume(self, volume):
        """Set the volume (0-100)"""
        self.player.audio_set_volume(volume)
    
    def get_position(self):
        """Get the current playback position in seconds"""
        if self.current_media is None:
            return 0
            
        # Get position as a percentage (0-1)
        pos_percentage = self.player.get_position()
        
        # Get total length in milliseconds
        length_ms = self.player.get_length()
        
        # Convert to seconds
        if length_ms > 0 and pos_percentage >= 0:
            return (pos_percentage * length_ms) / 1000
        return 0
    
    def set_position(self, position_seconds):
        """Set the playback position in seconds"""
        if self.current_media is None:
            return
            
        # Get total length in milliseconds
        length_ms = self.player.get_length()
        
        if length_ms > 0:
            # Convert position in seconds to a percentage
            pos_percentage = (position_seconds * 1000) / length_ms
            # Clamp value between 0-1
            pos_percentage = max(0, min(1, pos_percentage))
            # Set position
            self.player.set_position(pos_percentage)
    
    def get_length(self):
        """Get the total length of the current track in milliseconds"""
        return self.player.get_length()
    
    def get_duration(self):
        """Get the total duration of the current track in seconds"""
        length_ms = self.player.get_length()
        if length_ms > 0:
            return length_ms / 1000
        return 0
    
    def is_playing(self):
        """Check if a track is currently playing"""
        return self.is_playing
    
    def get_state(self):
        """Get the current player state"""
        return self.player.get_state() 