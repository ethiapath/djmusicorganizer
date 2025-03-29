# Traktor NML (Native Instruments Traktor) XML Format Documentation

## Overview
The NML (Native Instruments Traktor) format is an XML-based file format used by Native Instruments Traktor DJ software to store music collections and playlists. This document describes the structure and elements of the NML format.

## Basic Structure
```xml
<?xml version="1.0" encoding="UTF-8"?>
<NML VERSION="25">
    <HEAD>
        <COMPANY>Company Name</COMPANY>
        <PRODUCT>Product Name</PRODUCT>
        <VERSION>Version Number</VERSION>
    </HEAD>
    <MUSICFOLDERS>
        <!-- Music folder definitions -->
    </MUSICFOLDERS>
    <COLLECTION ENTRIES="0">
        <!-- Track entries -->
    </COLLECTION>
    <SETS>
        <!-- Playlists and other sets -->
    </SETS>
</NML>
```

## Root Element
- `<NML>`: The root element
  - `VERSION`: The NML format version (e.g., "25")

## HEAD Section
Contains basic information about the collection:
- `<COMPANY>`: Company name
- `<PRODUCT>`: Product name
- `<VERSION>`: Version number

## MUSICFOLDERS Section
Contains definitions of music folders used in the collection.

## COLLECTION Section
Contains all track entries in the collection.
- `ENTRIES`: Number of tracks in the collection

### Track Entry Structure
```xml
<ENTRY ID="unique-id">
    <PRIMARYKEY>unique-id</PRIMARYKEY>
    <TITLE>Track Title</TITLE>
    <ARTIST>Artist Name</ARTIST>
    <TEMPO BPM="120.0" BPM_QUALITY="100"/>
    <KEY VALUE="C"/>
    <LOCATION FILE="path/to/file.mp3" VOLUME="volume" DIR="path/to/directory"/>
    <INFO BITRATE="320" GENRE="Genre Name" PLAYTIME="0"/>
    <CUE_V2 NAME="Hot Cue 1" DISPL_ORDER="0" TYPE="0" START="0.0" LEN="0.0" REPEATS="0" HOTCUE="0"/>
    <CUE_V2 NAME="Loop 1" DISPL_ORDER="1" TYPE="1" START="32.0" LEN="32.0" REPEATS="0" HOTCUE="-1"/>
    <CUE_V2 NAME="Grid" DISPL_ORDER="2" TYPE="4" START="0.0" LEN="0.0" REPEATS="0" HOTCUE="-1"/>
    <CUE_V2 NAME="FadeIn" DISPL_ORDER="3" TYPE="5" START="0.0" LEN="32.0" REPEATS="0" HOTCUE="-1"/>
    <CUE_V2 NAME="FadeOut" DISPL_ORDER="4" TYPE="6" START="128.0" LEN="32.0" REPEATS="0" HOTCUE="-1"/>
    <CUE_V2 NAME="Load" DISPL_ORDER="5" TYPE="7" START="0.0" LEN="0.0" REPEATS="0" HOTCUE="-1"/>
    <CUE_V2 NAME="Grid" DISPL_ORDER="6" TYPE="8" START="0.0" LEN="0.0" REPEATS="0" HOTCUE="-1"/>
    <CUE_V2 NAME="Beat" DISPL_ORDER="7" TYPE="9" START="0.0" LEN="0.0" REPEATS="0" HOTCUE="-1"/>
    <CUE_V2 NAME="Beat" DISPL_ORDER="8" TYPE="9" START="1.0" LEN="0.0" REPEATS="0" HOTCUE="-1"/>
    <CUE_V2 NAME="Beat" DISPL_ORDER="9" TYPE="9" START="2.0" LEN="0.0" REPEATS="0" HOTCUE="-1"/>
</ENTRY>
```

#### Track Entry Elements
- `<ENTRY>`: Container for track information
  - `ID`: Unique identifier for the track
- `<PRIMARYKEY>`: Same as ID
- `<TITLE>`: Track title
- `<ARTIST>`: Artist name
- `<TEMPO>`: BPM information
  - `BPM`: Beats per minute
  - `BPM_QUALITY`: Quality of BPM detection (0-100)
- `<KEY>`: Musical key
  - `VALUE`: Key value (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
- `<LOCATION>`: File location information
  - `FILE`: Full file path
  - `VOLUME`: Volume identifier
  - `DIR`: Directory path
- `<INFO>`: Additional track information
  - `BITRATE`: Audio bitrate
  - `GENRE`: Track genre
  - `PLAYTIME`: Track duration in milliseconds

### Cue Points and Beat Grid
The NML format supports various types of cue points and beat grid markers using the `<CUE_V2>` element. Each cue point has the following attributes:

- `NAME`: Display name of the cue point
- `DISPL_ORDER`: Display order in the interface
- `TYPE`: Type of cue point
  - `0`: Hot Cue
  - `1`: Loop
  - `4`: Grid
  - `5`: Fade In
  - `6`: Fade Out
  - `7`: Load
  - `8`: Grid
  - `9`: Beat
- `START`: Start position in seconds
- `LEN`: Length in seconds (for loops and fades)
- `REPEATS`: Number of repeats (for loops)
- `HOTCUE`: Hot cue number (-1 for non-hot cues, 0-7 for hot cues)

#### Hot Cues
Hot cues are stored as type 0 cue points. Each hot cue has a unique number (0-7) stored in the HOTCUE attribute. The START position indicates where the hot cue is placed in the track.

#### Beat Grid
Beat grid markers are stored as type 9 cue points. Each beat marker has:
- A START position indicating the exact time of the beat
- A NAME of "Beat"
- A HOTCUE value of -1

#### Loops
Loops are stored as type 1 cue points with:
- START: Loop start position
- LEN: Loop length
- REPEATS: Number of times to repeat (0 for infinite)

#### Fade Points
Fade in/out points are stored as type 5/6 cue points with:
- START: Fade start position
- LEN: Fade duration

## SETS Section
Contains playlists and other track sets.

### Playlist Structure
```xml
<NODE TYPE="PLAYLIST" NAME="Playlist Name">
    <NODE TYPE="TRACK" KEY="track-id"/>
    <NODE TYPE="TRACK" KEY="track-id"/>
    <!-- More tracks -->
</NODE>
```

#### Playlist Elements
- `<NODE>`: Container for playlist or track
  - `TYPE`: Node type ("PLAYLIST" or "TRACK")
  - `NAME`: Playlist name (for playlist nodes)
  - `KEY`: Reference to track ID (for track nodes)

## Example
```xml
<?xml version="1.0" encoding="UTF-8"?>
<NML VERSION="25">
    <HEAD>
        <COMPANY>DJ Music Organizer</COMPANY>
        <PRODUCT>DJ Music Organizer</PRODUCT>
        <VERSION>1.0</VERSION>
    </HEAD>
    <MUSICFOLDERS/>
    <COLLECTION ENTRIES="2">
        <ENTRY ID="123e4567-e89b-12d3-a456-426614174000">
            <PRIMARYKEY>123e4567-e89b-12d3-a456-426614174000</PRIMARYKEY>
            <TITLE>Example Track</TITLE>
            <ARTIST>Example Artist</ARTIST>
            <TEMPO BPM="128.0" BPM_QUALITY="100"/>
            <KEY VALUE="C"/>
            <LOCATION FILE="C:/Music/example.mp3" VOLUME="volume" DIR="C:/Music"/>
            <INFO BITRATE="320" GENRE="House" PLAYTIME="180000"/>
            <CUE_V2 NAME="Hot Cue 1" DISPL_ORDER="0" TYPE="0" START="32.0" LEN="0.0" REPEATS="0" HOTCUE="0"/>
            <CUE_V2 NAME="Loop 1" DISPL_ORDER="1" TYPE="1" START="64.0" LEN="32.0" REPEATS="0" HOTCUE="-1"/>
            <CUE_V2 NAME="Beat" DISPL_ORDER="2" TYPE="9" START="0.0" LEN="0.0" REPEATS="0" HOTCUE="-1"/>
            <CUE_V2 NAME="Beat" DISPL_ORDER="3" TYPE="9" START="0.5" LEN="0.0" REPEATS="0" HOTCUE="-1"/>
        </ENTRY>
    </COLLECTION>
    <SETS>
        <NODE TYPE="PLAYLIST" NAME="My Playlist">
            <NODE TYPE="TRACK" KEY="123e4567-e89b-12d3-a456-426614174000"/>
        </NODE>
    </SETS>
</NML>
```

## Notes
1. The NML format is case-sensitive
2. Track IDs should be unique UUIDs
3. File paths should use forward slashes (/) or escaped backslashes (\\)
4. BPM values are typically between 60-200
5. The PLAYTIME value should be in milliseconds
6. The BITRATE value is typically 320 for high-quality files
7. Hot cues are numbered 0-7
8. Beat grid markers should be placed at exact beat positions
9. Loop lengths should be multiples of beats (e.g., 32 beats = 16 seconds at 120 BPM)
10. Fade lengths are typically 8-32 beats 