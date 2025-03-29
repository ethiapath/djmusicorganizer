import xml.etree.ElementTree as ET
import os
from datetime import datetime
import uuid

class NMLHandler:
    def __init__(self):
        self.tree = None
        self.root = None
        
    def create_new_nml(self):
        """Create a new NML file structure"""
        self.root = ET.Element("NML")
        self.root.set("VERSION", "25")
        
        # Create HEAD section
        head = ET.SubElement(self.root, "HEAD")
        ET.SubElement(head, "COMPANY").text = "DJ Music Organizer"
        ET.SubElement(head, "PRODUCT").text = "DJ Music Organizer"
        ET.SubElement(head, "VERSION").text = "1.0"
        
        # Create MUSICFOLDERS section
        music_folders = ET.SubElement(self.root, "MUSICFOLDERS")
        
        # Create COLLECTION section
        collection = ET.SubElement(self.root, "COLLECTION")
        collection.set("ENTRIES", "0")
        
        # Create SETS section
        sets = ET.SubElement(self.root, "SETS")
        
        self.tree = ET.ElementTree(self.root)
    
    def add_track_to_collection(self, track):
        """Add a track to the collection section"""
        collection = self.root.find("COLLECTION")
        entry = ET.SubElement(collection, "ENTRY")
        
        # Generate a unique ID for the track
        track_id = str(uuid.uuid4())
        entry.set("ID", track_id)
        
        # Add track information
        ET.SubElement(entry, "PRIMARYKEY").text = track_id
        ET.SubElement(entry, "TITLE").text = track.title
        ET.SubElement(entry, "ARTIST").text = track.artist
        
        # Add BPM information
        bpm = ET.SubElement(entry, "TEMPO")
        bpm.set("BPM", str(track.bpm))
        bpm.set("BPM_QUALITY", "100")
        
        # Add key information
        key = ET.SubElement(entry, "KEY")
        key.set("VALUE", track.key)
        
        # Add file location
        location = ET.SubElement(entry, "LOCATION")
        location.set("FILE", track.file_path)
        location.set("VOLUME", "volume")
        location.set("DIR", os.path.dirname(track.file_path))
        
        # Add metadata
        info = ET.SubElement(entry, "INFO")
        info.set("BITRATE", "320")
        info.set("GENRE", track.genre)
        info.set("PLAYTIME", "0")  # This should be calculated from the actual file
        
        # Update collection entries count
        collection.set("ENTRIES", str(len(collection.findall("ENTRY"))))
        
        return track_id
    
    def create_playlist(self, name, tracks):
        """Create a new playlist with the given tracks"""
        sets = self.root.find("SETS")
        playlist = ET.SubElement(sets, "NODE")
        playlist.set("TYPE", "PLAYLIST")
        playlist.set("NAME", name)
        
        # Add tracks to playlist
        for track in tracks:
            node = ET.SubElement(playlist, "NODE")
            node.set("TYPE", "TRACK")
            node.set("KEY", track.id)  # Reference to collection entry
    
    def save_nml(self, filepath):
        """Save the NML file to disk"""
        if self.tree is None:
            raise ValueError("No NML structure created")
        
        # Create pretty XML
        ET.indent(self.tree, space="  ")
        self.tree.write(filepath, encoding="utf-8", xml_declaration=True)
    
    def load_nml(self, filepath):
        """Load an existing NML file"""
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
    
    def get_collection_tracks(self):
        """Get all tracks from the collection"""
        tracks = []
        collection = self.root.find("COLLECTION")
        if collection is not None:
            for entry in collection.findall("ENTRY"):
                track = {
                    'id': entry.get("ID"),
                    'title': entry.find("TITLE").text,
                    'artist': entry.find("ARTIST").text,
                    'bpm': float(entry.find("TEMPO").get("BPM")),
                    'key': entry.find("KEY").get("VALUE"),
                    'file_path': entry.find("LOCATION").get("FILE"),
                    'genre': entry.find("INFO").get("GENRE")
                }
                tracks.append(track)
        return tracks
    
    def get_playlists(self):
        """Get all playlists from the sets section"""
        playlists = []
        sets = self.root.find("SETS")
        if sets is not None:
            for node in sets.findall("NODE"):
                if node.get("TYPE") == "PLAYLIST":
                    playlist = {
                        'name': node.get("NAME"),
                        'tracks': []
                    }
                    for track_node in node.findall("NODE"):
                        if track_node.get("TYPE") == "TRACK":
                            playlist['tracks'].append(track_node.get("KEY"))
                    playlists.append(playlist)
        return playlists 