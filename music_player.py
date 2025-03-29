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
        """Get the current playback position (0-100)"""
        return self.player.get_position() * 100
    
    def set_position(self, position):
        """Set the playback position (0-100)"""
        self.player.set_position(position / 100)
    
    def get_length(self):
        """Get the total length of the current track in milliseconds"""
        return self.player.get_length()
    
    def is_playing(self):
        """Check if a track is currently playing"""
        return self.is_playing
    
    def get_state(self):
        """Get the current player state"""
        return self.player.get_state() 