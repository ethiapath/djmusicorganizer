# Pioneer Rekordbox XML Format Documentation

## Overview
Pioneer Rekordbox uses an XML-based format to store music collections, playlists, and DJ-specific metadata. This format is used for exporting collections to USB drives for use with Pioneer CDJs and DJM mixers.

## Basic Structure
```xml
<?xml version="1.0" encoding="UTF-8"?>
<DJ_PLAYLISTS Version="1.0.0">
    <PRODUCT Name="rekordbox" Version="6.6.3"/>
    <COLLECTION Entries="0">
        <!-- Track entries -->
    </COLLECTION>
    <PLAYLISTS>
        <!-- Playlists and folders -->
    </PLAYLISTS>
</DJ_PLAYLISTS>
```

## Root Element
- `<DJ_PLAYLISTS>`: The root element
  - `Version`: The XML format version (e.g., "1.0.0")

## Product Information
- `<PRODUCT>`: Contains Rekordbox version information
  - `Name`: Always "rekordbox"
  - `Version`: Rekordbox software version

## COLLECTION Section
Contains all track entries in the collection.
- `Entries`: Number of tracks in the collection

### Track Entry Structure
```xml
<TRACK TrackID="1234" Name="Track Name" Artist="Artist Name" Composer="" Album="Album Name" Grouping="" Genre="" Kind="MP3 File" Size="1234567" TotalTime="180000" DiscNumber="1" TrackNumber="1" Year="2023" AverageBpm="128.00" DateAdded="2023-01-01" BitRate="320000" SampleRate="44100" Comments="" PlayCount="0" LastPlayed="" Rating="0" Location="file://localhost/M:/Music/example.mp3" Remixer="" Tonality="C" Label="" Mix="">
    <TEMPO Inizio="0.000" Bpm="128.000" Metro="4/4" Battito="1"/>
    <POSITION_MARK Name="Hot Cue 1" Type="0" Start="32.000" Num="-1" Red="255" Green="0" Blue="0"/>
    <POSITION_MARK Name="Loop 1" Type="1" Start="64.000" Num="-1" Red="0" Green="255" Blue="0"/>
    <POSITION_MARK Name="Memory 1" Type="2" Start="96.000" Num="-1" Red="0" Green="0" Blue="255"/>
    <POSITION_MARK Name="Grid" Type="4" Start="0.000" Num="-1" Red="0" Green="0" Blue="0"/>
</TRACK>
```

#### Track Entry Elements
- `<TRACK>`: Container for track information
  - `TrackID`: Unique identifier for the track
  - `Name`: Track title
  - `Artist`: Artist name
  - `Album`: Album name
  - `Genre`: Track genre
  - `Kind`: File type (e.g., "MP3 File", "WAV File")
  - `Size`: File size in bytes
  - `TotalTime`: Duration in milliseconds
  - `AverageBpm`: Beats per minute
  - `BitRate`: Audio bitrate
  - `SampleRate`: Audio sample rate
  - `Location`: File path (URL format)
  - `Tonality`: Musical key
  - `Rating`: Track rating (0-100)

### Cue Points and Beat Grid
Rekordbox uses the `<POSITION_MARK>` element for all types of markers. Each marker has the following attributes:

- `Name`: Display name of the marker
- `Type`: Type of marker
  - `0`: Hot Cue
  - `1`: Loop
  - `2`: Memory Cue
  - `4`: Grid
- `Start`: Start position in seconds
- `Num`: Marker number (-1 for non-hot cues)
- `Red`, `Green`, `Blue`: RGB color values (0-255)

#### Hot Cues
Hot cues are stored as type 0 position marks. Each hot cue has:
- A unique number in the Name field
- Type="0"
- Color values for visual identification

#### Loops
Loops are stored as type 1 position marks with:
- Start: Loop start position
- Length is determined by the next marker's Start position

#### Memory Cues
Memory cues are stored as type 2 position marks. They are similar to hot cues but:
- Are not assigned to specific hardware buttons
- Can be used for additional reference points

#### Beat Grid
Beat grid markers are stored as type 4 position marks with:
- Start: Beat position
- Name: "Grid"
- Black color (RGB: 0,0,0)

## PLAYLISTS Section
Contains playlists and folders.

### Playlist Structure
```xml
<PLAYLISTS>
    <NODE Type="0" Name="Root">
        <NODE Type="1" Name="My Playlist">
            <TRACK TrackID="1234"/>
            <TRACK TrackID="5678"/>
        </NODE>
    </NODE>
</PLAYLISTS>
```

#### Playlist Elements
- `<NODE>`: Container for playlist or folder
  - `Type`: Node type
    - `0`: Folder
    - `1`: Playlist
  - `Name`: Playlist/folder name
  - `<TRACK>`: Reference to track by TrackID

## Example
```xml
<?xml version="1.0" encoding="UTF-8"?>
<DJ_PLAYLISTS Version="1.0.0">
    <PRODUCT Name="rekordbox" Version="6.6.3"/>
    <COLLECTION Entries="1">
        <TRACK TrackID="1234" Name="Example Track" Artist="Example Artist" Album="Example Album" Genre="House" Kind="MP3 File" Size="1234567" TotalTime="180000" AverageBpm="128.00" BitRate="320000" SampleRate="44100" Location="file://localhost/M:/Music/example.mp3" Tonality="C">
            <TEMPO Inizio="0.000" Bpm="128.000" Metro="4/4" Battito="1"/>
            <POSITION_MARK Name="Hot Cue 1" Type="0" Start="32.000" Num="-1" Red="255" Green="0" Blue="0"/>
            <POSITION_MARK Name="Loop 1" Type="1" Start="64.000" Num="-1" Red="0" Green="255" Blue="0"/>
            <POSITION_MARK Name="Grid" Type="4" Start="0.000" Num="-1" Red="0" Green="0" Blue="0"/>
        </TRACK>
    </COLLECTION>
    <PLAYLISTS>
        <NODE Type="0" Name="Root">
            <NODE Type="1" Name="My Playlist">
                <TRACK TrackID="1234"/>
            </NODE>
        </NODE>
    </PLAYLISTS>
</DJ_PLAYLISTS>
```

## Notes
1. The format is case-sensitive
2. Track IDs are numeric (unlike Traktor's UUIDs)
3. File paths are stored as file://localhost/ URLs
4. BPM values are stored with 2 decimal places
5. Hot cues are numbered 1-8 (unlike Traktor's 0-7)
6. Memory cues are unique to Rekordbox
7. Beat grid markers are always black
8. Playlists can be nested in folders
9. The format supports both MP3 and WAV files
10. Track ratings are on a scale of 0-100 