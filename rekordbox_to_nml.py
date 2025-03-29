import xml.etree.ElementTree as ET
import os
import uuid
from datetime import datetime
import re

class RekordboxToNMLConverter:
    def __init__(self, map_memory_to_hotcue=False):
        self.map_memory_to_hotcue = map_memory_to_hotcue
        self.track_id_map = {}  # Map Rekordbox IDs to Traktor UUIDs
        
    def convert_rekordbox_to_nml(self, rekordbox_file, output_file):
        """Convert a Rekordbox XML file to Traktor NML format"""
        # Parse Rekordbox file
        rekordbox_tree = ET.parse(rekordbox_file)
        rekordbox_root = rekordbox_tree.getroot()
        
        # Create NML XML structure
        nml_root = ET.Element("NML")
        nml_root.set("VERSION", "25")
        
        # Add HEAD section
        head = ET.SubElement(nml_root, "HEAD")
        head.set("COMPANY", "Native Instruments")
        head.set("PROGRAM", "Traktor")
        head.set("VERSION", "3.4.0")
        
        # Add MUSICFOLDERS section
        music_folders = ET.SubElement(nml_root, "MUSICFOLDERS")
        music_folders.set("COUNT", "1")
        folder = ET.SubElement(music_folders, "FOLDER")
        folder.set("PATH", "C:/Users/Public/Music")
        
        # Convert collection
        collection = ET.SubElement(nml_root, "COLLECTION")
        rekordbox_collection = rekordbox_root.find("COLLECTION")
        if rekordbox_collection is not None:
            entries = len(rekordbox_collection.findall("TRACK"))
            collection.set("ENTRIES", str(entries))
            
            # Convert each track
            for track in rekordbox_collection.findall("TRACK"):
                self._convert_track(track, collection)
        
        # Convert playlists
        sets = ET.SubElement(nml_root, "SETS")
        rekordbox_playlists = rekordbox_root.find("PLAYLISTS")
        if rekordbox_playlists is not None:
            root_node = rekordbox_playlists.find("NODE")
            if root_node is not None:
                self._convert_playlists(root_node, sets)
        
        # Write to file
        ET.indent(nml_root, space="  ")
        tree = ET.ElementTree(nml_root)
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
    
    def _convert_track(self, rekordbox_track, collection):
        """Convert a single track from Rekordbox to NML format"""
        # Generate Traktor UUID
        rekordbox_id = rekordbox_track.get("TrackID")
        traktor_id = str(uuid.uuid4())
        self.track_id_map[rekordbox_id] = traktor_id
        
        # Create entry element
        entry = ET.SubElement(collection, "ENTRY")
        entry.set("ID", traktor_id)
        
        # Convert basic metadata
        title = ET.SubElement(entry, "TITLE")
        title.text = rekordbox_track.get("Name", "")
        
        artist = ET.SubElement(entry, "ARTIST")
        artist.text = rekordbox_track.get("Artist", "")
        
        info = ET.SubElement(entry, "INFO")
        info.set("GENRE", rekordbox_track.get("Genre", ""))
        info.set("PLAYTIME", rekordbox_track.get("TotalTime", "0"))
        info.set("BITRATE", rekordbox_track.get("BitRate", "320000"))
        
        location = ET.SubElement(entry, "LOCATION")
        location.set("FILE", self._convert_file_path(rekordbox_track.get("Location", "")))
        
        tempo = ET.SubElement(entry, "TEMPO")
        tempo.set("BPM", rekordbox_track.get("AverageBpm", "0"))
        
        key = ET.SubElement(entry, "KEY")
        key.set("VALUE", rekordbox_track.get("Tonality", ""))
        
        # Convert cue points
        self._convert_cue_points(rekordbox_track, entry)
    
    def _convert_cue_points(self, rekordbox_track, entry):
        """Convert cue points from Rekordbox to NML format"""
        # Find all POSITION_MARK elements
        for mark in rekordbox_track.findall("POSITION_MARK"):
            mark_type = int(mark.get("Type", "0"))
            start = float(mark.get("Start", "0"))
            name = mark.get("Name", "")
            
            # Create CUE_V2 element
            cue = ET.SubElement(entry, "CUE_V2")
            cue.set("START", f"{start:.3f}")
            
            # Convert cue type
            if mark_type == 0:  # Hot Cue
                cue.set("TYPE", "0")
                cue.set("NAME", name)
            elif mark_type == 1:  # Loop
                cue.set("TYPE", "1")
                cue.set("NAME", name)
            elif mark_type == 2:  # Memory Cue
                if self.map_memory_to_hotcue:
                    # Convert memory cue to hot cue
                    cue.set("TYPE", "0")
                    cue.set("NAME", f"Hot Cue {name.split()[-1]}")
                else:
                    # Keep as memory cue (not supported in Traktor)
                    continue
            elif mark_type == 4:  # Grid
                cue.set("TYPE", "4")
                cue.set("NAME", "Grid")
    
    def _convert_playlists(self, rekordbox_node, parent_node):
        """Convert playlists from Rekordbox to NML format"""
        for node in rekordbox_node.findall("NODE"):
            if node.get("Type") == "1":  # Playlist
                # Create playlist node
                playlist = ET.SubElement(parent_node, "NODE")
                playlist.set("TYPE", "PLAYLIST")
                playlist.set("NAME", node.get("Name", ""))
                
                # Add tracks to playlist
                for track_ref in node.findall("TRACK"):
                    rekordbox_id = track_ref.get("TrackID")
                    traktor_id = self.track_id_map.get(rekordbox_id)
                    if traktor_id:
                        track_node = ET.SubElement(playlist, "NODE")
                        track_node.set("TYPE", "TRACK")
                        track_node.set("KEY", traktor_id)
    
    def _convert_file_path(self, file_path):
        """Convert file path from Rekordbox format to local path"""
        # Remove file://localhost/ prefix
        file_path = file_path.replace("file://localhost/", "")
        # Convert forward slashes to backslashes
        return file_path.replace("/", "\\")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Rekordbox XML file to Traktor NML format")
    parser.add_argument("input_file", help="Input Rekordbox XML file")
    parser.add_argument("output_file", help="Output Traktor NML file")
    parser.add_argument("--map-memory-to-hotcue", action="store_true", 
                       help="Map Rekordbox memory cues to Traktor hot cues")
    
    args = parser.parse_args()
    
    converter = RekordboxToNMLConverter(map_memory_to_hotcue=args.map_memory_to_hotcue)
    try:
        converter.convert_rekordbox_to_nml(args.input_file, args.output_file)
        print(f"Successfully converted {args.input_file} to {args.output_file}")
        if args.map_memory_to_hotcue:
            print("Memory cues have been mapped to hot cues")
    except Exception as e:
        print(f"Error converting file: {str(e)}")

if __name__ == "__main__":
    main() 