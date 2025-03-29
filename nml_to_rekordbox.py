import xml.etree.ElementTree as ET
import os
import uuid
from datetime import datetime
import re

class NMLToRekordboxConverter:
    def __init__(self, map_hotcues_to_memory=False):
        self.track_id_counter = 1  # Rekordbox uses numeric IDs
        self.track_id_map = {}  # Map Traktor UUIDs to Rekordbox IDs
        self.map_hotcues_to_memory = map_hotcues_to_memory
        self.first_hotcue_processed = False  # Track if we've processed the first hot cue
        
    def convert_nml_to_rekordbox(self, nml_file, output_file):
        """Convert a Traktor NML file to Rekordbox XML format"""
        # Parse NML file
        nml_tree = ET.parse(nml_file)
        nml_root = nml_tree.getroot()
        
        # Create Rekordbox XML structure
        rekordbox_root = ET.Element("DJ_PLAYLISTS")
        rekordbox_root.set("Version", "1.0.0")
        
        # Add product information
        product = ET.SubElement(rekordbox_root, "PRODUCT")
        product.set("Name", "rekordbox")
        product.set("Version", "6.6.3")
        
        # Convert collection
        collection = ET.SubElement(rekordbox_root, "COLLECTION")
        nml_collection = nml_root.find("COLLECTION")
        if nml_collection is not None:
            entries = len(nml_collection.findall("ENTRY"))
            collection.set("Entries", str(entries))
            
            # Convert each track
            for entry in nml_collection.findall("ENTRY"):
                self._convert_track(entry, collection)
        
        # Convert playlists
        playlists = ET.SubElement(rekordbox_root, "PLAYLISTS")
        nml_sets = nml_root.find("SETS")
        if nml_sets is not None:
            root_node = ET.SubElement(playlists, "NODE")
            root_node.set("Type", "0")
            root_node.set("Name", "Root")
            self._convert_playlists(nml_sets, root_node)
        
        # Write to file
        ET.indent(rekordbox_root, space="  ")
        tree = ET.ElementTree(rekordbox_root)
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
    
    def _convert_track(self, nml_entry, collection):
        """Convert a single track from NML to Rekordbox format"""
        # Reset first hotcue flag for each track
        self.first_hotcue_processed = False
        
        # Generate Rekordbox track ID
        traktor_id = nml_entry.get("ID")
        rekordbox_id = str(self.track_id_counter)
        self.track_id_map[traktor_id] = rekordbox_id
        self.track_id_counter += 1
        
        # Create track element
        track = ET.SubElement(collection, "TRACK")
        track.set("TrackID", rekordbox_id)
        
        # Convert basic metadata
        track.set("Name", nml_entry.find("TITLE").text)
        track.set("Artist", nml_entry.find("ARTIST").text)
        track.set("Album", "Unknown")  # NML doesn't store album info
        track.set("Genre", nml_entry.find("INFO").get("GENRE", ""))
        track.set("Kind", "MP3 File")  # Default to MP3
        track.set("Size", "0")  # We don't have file size in NML
        track.set("TotalTime", nml_entry.find("INFO").get("PLAYTIME", "0"))
        track.set("AverageBpm", str(nml_entry.find("TEMPO").get("BPM", "0")))
        track.set("BitRate", nml_entry.find("INFO").get("BITRATE", "320000"))
        track.set("SampleRate", "44100")  # Default sample rate
        track.set("Location", self._convert_file_path(nml_entry.find("LOCATION").get("FILE")))
        track.set("Tonality", nml_entry.find("KEY").get("VALUE", ""))
        track.set("Rating", "0")  # NML doesn't store ratings
        
        # Add tempo information
        tempo = ET.SubElement(track, "TEMPO")
        tempo.set("Inizio", "0.000")
        tempo.set("Bpm", str(nml_entry.find("TEMPO").get("BPM", "0")))
        tempo.set("Metro", "4/4")  # Default time signature
        tempo.set("Battito", "1")  # Default beat position
        
        # Convert cue points
        self._convert_cue_points(nml_entry, track)
    
    def _convert_cue_points(self, nml_entry, track):
        """Convert cue points from NML to Rekordbox format"""
        # Find all CUE_V2 elements
        for cue in nml_entry.findall("CUE_V2"):
            cue_type = int(cue.get("TYPE", "0"))
            start = float(cue.get("START", "0"))
            name = cue.get("NAME", "")
            
            # Create position mark
            mark = ET.SubElement(track, "POSITION_MARK")
            mark.set("Start", f"{start:.3f}")
            
            # Convert cue type
            if cue_type == 0:  # Hot Cue
                if not self.first_hotcue_processed and self.map_hotcues_to_memory:
                    # For the first hot cue, create both memory and hot cue
                    # First create the memory cue
                    mark.set("Type", "2")
                    mark.set("Name", f"Memory {int(name.split()[-1]) + 1}")
                    mark.set("Num", "-1")
                    mark.set("Red", "0")
                    mark.set("Green", "0")
                    mark.set("Blue", "255")
                    
                    # Then create the hot cue
                    hot_cue = ET.SubElement(track, "POSITION_MARK")
                    hot_cue.set("Start", f"{start:.3f}")
                    hot_cue.set("Type", "0")
                    hot_cue.set("Name", f"Hot Cue {int(name.split()[-1]) + 1}")
                    hot_cue.set("Num", "-1")
                    hot_cue.set("Red", "255")
                    hot_cue.set("Green", "0")
                    hot_cue.set("Blue", "0")
                    
                    self.first_hotcue_processed = True
                else:
                    # For other hot cues, keep as hot cue
                    mark.set("Type", "0")
                    mark.set("Name", f"Hot Cue {int(name.split()[-1]) + 1}")
                    mark.set("Num", "-1")
                    mark.set("Red", "255")
                    mark.set("Green", "0")
                    mark.set("Blue", "0")
            elif cue_type == 1:  # Loop
                mark.set("Type", "1")
                mark.set("Name", name)
                mark.set("Num", "-1")
                mark.set("Red", "0")
                mark.set("Green", "255")
                mark.set("Blue", "0")
            elif cue_type == 4:  # Grid
                mark.set("Type", "4")
                mark.set("Name", "Grid")
                mark.set("Num", "-1")
                mark.set("Red", "0")
                mark.set("Green", "0")
                mark.set("Blue", "0")
            elif cue_type == 9:  # Beat
                mark.set("Type", "4")
                mark.set("Name", "Grid")
                mark.set("Num", "-1")
                mark.set("Red", "0")
                mark.set("Green", "0")
                mark.set("Blue", "0")
    
    def _convert_playlists(self, nml_sets, parent_node):
        """Convert playlists from NML to Rekordbox format"""
        for node in nml_sets.findall("NODE"):
            if node.get("TYPE") == "PLAYLIST":
                # Create playlist node
                playlist = ET.SubElement(parent_node, "NODE")
                playlist.set("Type", "1")
                playlist.set("Name", node.get("NAME", ""))
                
                # Add tracks to playlist
                for track_node in node.findall("NODE"):
                    if track_node.get("TYPE") == "TRACK":
                        track_ref = ET.SubElement(playlist, "TRACK")
                        traktor_id = track_node.get("KEY")
                        rekordbox_id = self.track_id_map.get(traktor_id, "0")
                        track_ref.set("TrackID", rekordbox_id)
    
    def _convert_file_path(self, file_path):
        """Convert file path to Rekordbox format"""
        # Convert backslashes to forward slashes
        file_path = file_path.replace("\\", "/")
        # Add file://localhost/ prefix
        return f"file://localhost/{file_path}"

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Traktor NML file to Rekordbox XML format")
    parser.add_argument("input_file", help="Input Traktor NML file")
    parser.add_argument("output_file", help="Output Rekordbox XML file")
    parser.add_argument("--map-hotcues-to-memory", action="store_true", 
                       help="Map first Traktor hot cue to both Rekordbox memory cue and hot cue")
    
    args = parser.parse_args()
    
    converter = NMLToRekordboxConverter(map_hotcues_to_memory=args.map_hotcues_to_memory)
    try:
        converter.convert_nml_to_rekordbox(args.input_file, args.output_file)
        print(f"Successfully converted {args.input_file} to {args.output_file}")
        if args.map_hotcues_to_memory:
            print("First hot cue has been mapped to both memory cue and hot cue")
    except Exception as e:
        print(f"Error converting file: {str(e)}")

if __name__ == "__main__":
    main() 