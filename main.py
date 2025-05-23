import sys
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QFileDialog,
                           QTableWidget, QTableWidgetItem, QComboBox,
                           QSpinBox, QLineEdit, QMessageBox, QInputDialog,
                           QProgressDialog, QHeaderView, QMenu, QToolTip,
                           QDialog, QRadioButton, QGroupBox, QFormLayout, QSlider, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QPoint, QTime, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QColor
import os
import traceback
import time
from music_scanner import MusicScanner
from music_player import MusicPlayer
from waveform_widget import WaveformWidget

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('music_organizer.log')
    ]
)
logger = logging.getLogger(__name__)

# ScannerThread class
class ScannerThread(QThread):
    progress_updated = pyqtSignal(int, str, int, int)
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(Exception)
    
    def __init__(self, scanner):
        super().__init__()
        self.scanner = scanner
        self._is_running = True
        
    def run(self):
        try:
            result = []
            if self._is_running:
                self.scanner.scan(progress_callback=self._progress_wrapper, 
                                result_collector=result)
            self.finished.emit(result[0] if result else [])
        except Exception as e:
            self.error_occurred.emit(e)
    
    def _progress_wrapper(self, value, message, current, total):
        if self._is_running:
            self.progress_updated.emit(value, message, current, total)
            
    def cancel(self):
        self._is_running = False
        self.scanner.cancel_scan()

# Format Migration Dialog
class FormatMigrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Format Migration")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Source format selection
        source_group = QGroupBox("Source Format")
        source_layout = QVBoxLayout()
        
        self.source_nml = QRadioButton("Traktor (NML)")
        self.source_xml = QRadioButton("Rekordbox (XML)")
        self.source_csv = QRadioButton("Serato (CSV)")
        self.source_m3u = QRadioButton("M3U/M3U8 Playlist")
        self.source_nml.setChecked(True)
        
        source_layout.addWidget(self.source_nml)
        source_layout.addWidget(self.source_xml)
        source_layout.addWidget(self.source_csv)
        source_layout.addWidget(self.source_m3u)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Target format selection
        target_group = QGroupBox("Target Format")
        target_layout = QVBoxLayout()
        
        self.target_nml = QRadioButton("Traktor (NML)")
        self.target_xml = QRadioButton("Rekordbox (XML)")
        self.target_csv = QRadioButton("Serato (CSV)")
        self.target_m3u = QRadioButton("M3U Playlist")
        self.target_m3u8 = QRadioButton("M3U8 Playlist (UTF-8)")
        self.target_xml.setChecked(True)
        
        target_layout.addWidget(self.target_nml)
        target_layout.addWidget(self.target_xml)
        target_layout.addWidget(self.target_csv)
        target_layout.addWidget(self.target_m3u)
        target_layout.addWidget(self.target_m3u8)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # Options
        options_group = QGroupBox("Migration Options")
        options_layout = QFormLayout()
        
        self.preserve_cues = QComboBox()
        self.preserve_cues.addItems(["Preserve all cue points", "Preserve only first 8 cues", "Skip cue points"])
        
        self.handle_missing = QComboBox()
        self.handle_missing.addItems(["Skip missing files", "Include with warnings", "Attempt to locate"])
        
        options_layout.addRow("Cue Points:", self.preserve_cues)
        options_layout.addRow("Missing Files:", self.handle_missing)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.migrate_btn = QPushButton("Start Migration")
        self.cancel_btn = QPushButton("Cancel")
        
        self.migrate_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.migrate_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
    
    def get_source_format(self):
        if self.source_nml.isChecked():
            return "nml"
        elif self.source_xml.isChecked():
            return "xml"
        elif self.source_csv.isChecked():
            return "csv"
        elif self.source_m3u.isChecked():
            return "m3u"
        return "nml"  # Default
    
    def get_target_format(self):
        if self.target_nml.isChecked():
            return "nml"
        elif self.target_xml.isChecked():
            return "xml"
        elif self.target_csv.isChecked():
            return "csv"
        elif self.target_m3u.isChecked():
            return "m3u"
        elif self.target_m3u8.isChecked():
            return "m3u8"
        return "xml"  # Default
    
    def get_options(self):
        return {
            "preserve_cues": self.preserve_cues.currentText(),
            "handle_missing": self.handle_missing.currentText()
        }

class DJMusicOrganizer(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.debug("Initializing DJMusicOrganizer")
        self.setWindowTitle("DJ Music Organizer")
        self.setMinimumSize(1200, 800)
        
        # Initialize components
        self.music_scanner = MusicScanner()
        self.music_player = MusicPlayer()
        logger.debug("MusicScanner and MusicPlayer initialized")
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create toolbar
        toolbar = QHBoxLayout()
        
        # Add folder button
        add_folder_btn = QPushButton("Add Music Folder")
        add_folder_btn.clicked.connect(self.add_music_folder)
        toolbar.addWidget(add_folder_btn)
        
        # Scan button
        scan_btn = QPushButton("Scan Music")
        scan_btn.clicked.connect(self.scan_music)
        toolbar.addWidget(scan_btn)
        
        # NML import/export buttons
        import_nml_btn = QPushButton("Import NML")
        import_nml_btn.clicked.connect(self.import_nml)
        toolbar.addWidget(import_nml_btn)
        
        export_nml_btn = QPushButton("Export NML")
        export_nml_btn.clicked.connect(self.export_nml)
        toolbar.addWidget(export_nml_btn)
        
        # M3U import/export buttons
        import_m3u_btn = QPushButton("Import M3U")
        import_m3u_btn.clicked.connect(self.import_m3u)
        toolbar.addWidget(import_m3u_btn)
        
        export_m3u_btn = QPushButton("Export M3U")
        export_m3u_btn.clicked.connect(self.export_m3u)
        toolbar.addWidget(export_m3u_btn)
        
        # Create playlist button
        create_playlist_btn = QPushButton("Create Playlist")
        create_playlist_btn.clicked.connect(self.create_playlist)
        toolbar.addWidget(create_playlist_btn)
        
        # Remove corrupted button
        remove_corrupted_btn = QPushButton("Remove Corrupted Files")
        remove_corrupted_btn.clicked.connect(self.remove_corrupted_files)
        toolbar.addWidget(remove_corrupted_btn)
        
        # Format migration button
        migrate_btn = QPushButton("Format Migration")
        migrate_btn.clicked.connect(self.migrate_formats)
        toolbar.addWidget(migrate_btn)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Genre filter
        self.genre_filter = QComboBox()
        self.genre_filter.addItem("All Genres")
        self.genre_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Genre:"))
        filter_layout.addWidget(self.genre_filter)
        
        # BPM range
        self.bpm_min = QSpinBox()
        self.bpm_min.setRange(0, 200)
        self.bpm_min.valueChanged.connect(self.apply_filters)
        self.bpm_max = QSpinBox()
        self.bpm_max.setRange(0, 200)
        self.bpm_max.setValue(200)
        self.bpm_max.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("BPM:"))
        filter_layout.addWidget(self.bpm_min)
        filter_layout.addWidget(QLabel("-"))
        filter_layout.addWidget(self.bpm_max)
        
        # Key filter
        self.key_filter = QComboBox()
        self.key_filter.addItems(["All Keys", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
        self.key_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Key:"))
        filter_layout.addWidget(self.key_filter)
        
        # Show corrupted files checkbox
        self.show_corrupted = QComboBox()
        self.show_corrupted.addItems(["All Files", "Valid Files Only", "Corrupted Files Only"])
        self.show_corrupted.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Show:"))
        filter_layout.addWidget(self.show_corrupted)
        
        # Apply filter button
        apply_filter_btn = QPushButton("Apply Filters")
        apply_filter_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(apply_filter_btn)
        
        toolbar.addLayout(filter_layout)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Create music table
        self.music_table = QTableWidget()
        self.music_table.setColumnCount(8)  # Added Status column
        self.music_table.setHorizontalHeaderLabels([
            "Title", "Artist", "BPM", "Key", "Genre", "Energy", "Status", "Location"
        ])
        # Set column widths
        self.music_table.setColumnWidth(0, 250)  # Title
        self.music_table.setColumnWidth(1, 200)  # Artist
        self.music_table.setColumnWidth(2, 80)   # BPM
        self.music_table.setColumnWidth(3, 80)   # Key
        self.music_table.setColumnWidth(4, 150)  # Genre
        self.music_table.setColumnWidth(5, 80)   # Energy
        self.music_table.setColumnWidth(6, 100)  # Status
        self.music_table.setColumnWidth(7, 300)  # Location
        
        # Make the horizontal header resize to contents
        header = self.music_table.horizontalHeader()
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        
        self.music_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.music_table.doubleClicked.connect(self.play_selected_track)
        self.music_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.music_table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.music_table)
        
        # Create player controls
        player_controls = QHBoxLayout()
        
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.toggle_play)
        player_controls.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_playback)
        player_controls.addWidget(self.stop_btn)
        
        # Now playing label
        self.now_playing_label = QLabel("Not Playing")
        player_controls.addWidget(self.now_playing_label)
        
        # Add waveform widget
        self.waveform_widget = WaveformWidget()
        self.waveform_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.waveform_widget.setFixedHeight(100)
        self.waveform_widget.position_changed.connect(self.set_position_from_waveform)
        player_controls.addWidget(self.waveform_widget)
        
        # Add playback progress slider
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(0, 100)
        self.time_slider.setValue(0)
        self.time_slider.setEnabled(False)
        self.time_slider.sliderPressed.connect(self.slider_pressed)
        self.time_slider.sliderReleased.connect(self.slider_released)
        self.time_slider.valueChanged.connect(self.slider_value_changed)
        player_controls.addWidget(self.time_slider)
        
        # Add time labels
        self.current_time_label = QLabel("0:00")
        player_controls.addWidget(self.current_time_label)
        player_controls.addWidget(QLabel("/"))
        self.total_time_label = QLabel("0:00")
        player_controls.addWidget(self.total_time_label)
        
        player_controls.addStretch()
        
        # Volume control
        self.volume_slider = QSpinBox()
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        player_controls.addWidget(QLabel("Volume:"))
        player_controls.addWidget(self.volume_slider)
        
        # Create a dedicated container for the player controls
        player_control_widget = QWidget()
        player_control_widget.setLayout(player_controls)
        layout.addWidget(player_control_widget)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Initialize state
        self.current_track = None
        self.is_playing = False
        self.all_tracks = []
        self.progress_dialog = None
        self.scan_start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_progress_time)
        
        # Add playback timer for updating slider
        self.playback_timer = QTimer()
        self.playback_timer.setInterval(50)  # Update more frequently (50ms) for smoother playhead movement
        self.playback_timer.timeout.connect(self.update_playback_position)
        self.slider_being_dragged = False
        
    def add_music_folder(self):
        logger.debug("add_music_folder method called")
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        logger.debug(f"Selected folder: {folder}")
        if folder:
            try:
                logger.debug(f"Adding folder to music scanner: {folder}")
                self.music_scanner.add_folder(folder)
                logger.debug(f"Successfully added folder: {folder}")
                self.statusBar().showMessage(f"Added folder: {folder}")
            except Exception as e:
                logger.error(f"Error adding folder: {str(e)}", exc_info=True)
                self.show_error("Error adding folder", str(e))
    
    def _update_progress_time(self):
        """Update the elapsed time on the progress dialog"""
        if self.progress_dialog and self.scan_start_time:
            elapsed = time.time() - self.scan_start_time
            elapsed_str = time.strftime("%M:%S", time.gmtime(elapsed))
            current_text = self.progress_dialog.labelText()
            
            # Extract the first line of the label text (the operation description)
            lines = current_text.split('\n')
            if len(lines) > 0:
                operation_text = lines[0]
                # Check if we already have a time display and replace it, otherwise add it
                if "Elapsed time:" in current_text:
                    time_text = f"\nElapsed time: {elapsed_str}"
                    self.progress_dialog.setLabelText(f"{operation_text}{time_text}")
                else:
                    self.progress_dialog.setLabelText(f"{operation_text}\nElapsed time: {elapsed_str}")
    
    def scan_music(self):
        # Replace existing scan logic with:
        if not self.music_scanner.folders:
            QMessageBox.warning(self, "Warning", "Add a folder first.")
            return
        
        try:
            self.progress_dialog = QProgressDialog("Preparing...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowTitle("Scanning Music")
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setValue(0)
            self.progress_dialog.show()
            
            # Connect to canceled signal
            self.progress_dialog.canceled.connect(self._cancel_scan)
            
            # Set progress callback
            self.music_scanner.set_progress_callback(self._update_progress)
            
            # Start timer for elapsed time display
            self.scan_start_time = time.time()
            self.timer.start(1000)  # Update every second
            
            # Allow UI updates before starting the scan
            QApplication.processEvents()
            
            # Start scanning
            logger.debug(f"Starting scan of {len(self.music_scanner.folders)} folders")
            self.music_scanner.scan()
            
            # Stop timer
            self.timer.stop()
            
            # Ensure progress dialog is closed
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            
            self.all_tracks = self.music_scanner.get_tracks()
            logger.debug(f"Scan complete. Found {len(self.all_tracks)} tracks")
            self.update_music_table(self.all_tracks)
            self.update_genre_filter()
            
            # Count corrupted files
            corrupted_count = sum(1 for track in self.all_tracks if track.is_corrupt)
            logger.debug(f"Found {corrupted_count} corrupted files")
            
            # Show counts
            self.statusBar().showMessage(
                f"Scanned {len(self.all_tracks)} tracks ({corrupted_count} corrupted)"
            )
        except Exception as e:
            logger.error(f"Error during music scan: {str(e)}", exc_info=True)
            self.timer.stop()
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            self.show_error("Error scanning music", str(e))
    
    def _cancel_scan(self):
        """Cancel the current scanning operation"""
        logger.debug("Scan canceled by user")
        self.statusBar().showMessage("Scan canceled by user")
        self.music_scanner.cancel_scan()
        
        # Disable cancel button to prevent multiple clicks
        if self.progress_dialog:
            self.progress_dialog.setCancelButtonText("Canceling...")
            self.progress_dialog.setCancelButton(None)  # Disable cancel button
            self.progress_dialog.setLabelText("Canceling scan... This may take a moment.\nPlease wait.")
    
    def update_music_table(self, tracks):
        """Update the table with the provided tracks"""
        try:
            self.music_table.setRowCount(len(tracks))
            
            # Disable sorting while updating
            self.music_table.setSortingEnabled(False)
            
            for i, track in enumerate(tracks):
                try:
                    # Use empty strings for None values to prevent issues
                    title_item = QTableWidgetItem(track.title or "")
                    artist_item = QTableWidgetItem(track.artist or "")
                    bpm_item = QTableWidgetItem(str(track.bpm or 0))
                    key_item = QTableWidgetItem(track.key or "")
                    genre_item = QTableWidgetItem(track.genre or "")
                    energy_item = QTableWidgetItem(str(track.energy or 0))
                    
                    # Add status column
                    if track.is_corrupt:
                        status_item = QTableWidgetItem("Corrupted")
                        status_item.setForeground(QColor("red"))
                        status_item.setToolTip(f"Corrupted: {track.error_message}")  # Show full error
                        
                        # Add corruption indicator to location column
                        location_item = QTableWidgetItem(f"[CORRUPT] {track.file_path}")
                        location_item.setForeground(QColor("red"))
                    else:
                        status_item = QTableWidgetItem("OK")
                        location_item = QTableWidgetItem(track.file_path or "")
                    
                    self.music_table.setItem(i, 0, title_item)
                    self.music_table.setItem(i, 1, artist_item)
                    self.music_table.setItem(i, 2, bpm_item)
                    self.music_table.setItem(i, 3, key_item)
                    self.music_table.setItem(i, 4, genre_item)
                    self.music_table.setItem(i, 5, energy_item)
                    self.music_table.setItem(i, 6, status_item)
                    self.music_table.setItem(i, 7, location_item)
                    
                except Exception as e:
                    print(f"Error adding track row: {str(e)}")
            
            # Re-enable sorting after update
            self.music_table.setSortingEnabled(True)
        except Exception as e:
            self.show_error("Error updating music table", str(e))
    
    def update_genre_filter(self):
        """Update the genre filter with unique genres from tracks"""
        try:
            current_genres = set()
            for track in self.all_tracks:
                if track.genre and track.genre.strip():
                    current_genres.add(track.genre.strip())
            
            current_text = self.genre_filter.currentText()
            self.genre_filter.clear()
            self.genre_filter.addItem("All Genres")
            self.genre_filter.addItems(sorted(current_genres))
            
            # Try to restore previous selection
            index = self.genre_filter.findText(current_text)
            if index >= 0:
                self.genre_filter.setCurrentIndex(index)
        except Exception as e:
            self.show_error("Error updating genre filter", str(e))
    
    def apply_filters(self):
        """Apply filters to the track list"""
        try:
            # Filter by metadata
            genre = None if self.genre_filter.currentText() == "All Genres" else self.genre_filter.currentText()
            bpm_min = self.bpm_min.value() if self.bpm_min.value() > 0 else None
            bpm_max = self.bpm_max.value() if self.bpm_max.value() < 200 else None
            key = None if self.key_filter.currentText() == "All Keys" else self.key_filter.currentText()
            
            filtered_tracks = self.music_scanner.filter_tracks(
                genre=genre, bpm_min=bpm_min, bpm_max=bpm_max, key=key
            )
            
            # Filter by corruption status
            corruption_filter = self.show_corrupted.currentText()
            if corruption_filter == "Valid Files Only":
                filtered_tracks = [t for t in filtered_tracks if not t.is_corrupt]
            elif corruption_filter == "Corrupted Files Only":
                filtered_tracks = [t for t in filtered_tracks if t.is_corrupt]
            
            self.update_music_table(filtered_tracks)
            
            # Count corrupted files in the filtered list
            corrupted_count = sum(1 for track in filtered_tracks if track.is_corrupt)
            
            self.statusBar().showMessage(
                f"Showing {len(filtered_tracks)} of {len(self.all_tracks)} tracks ({corrupted_count} corrupted)"
            )
        except Exception as e:
            self.show_error("Error applying filters", str(e))
    
    def remove_corrupted_files(self):
        """Remove corrupted files from the track list"""
        corrupted_tracks = [t for t in self.all_tracks if t.is_corrupt]
        if not corrupted_tracks:
            QMessageBox.information(self, "No Corrupted Files", "No corrupted files found in the library.")
            return
            
        reply = QMessageBox.question(
            self, 
            "Remove Corrupted Files",
            f"Are you sure you want to remove {len(corrupted_tracks)} corrupted files from the library?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.all_tracks = [t for t in self.all_tracks if not t.is_corrupt]
            self.update_music_table(self.all_tracks)
            self.statusBar().showMessage(f"Removed {len(corrupted_tracks)} corrupted files")
    
    def show_context_menu(self, position):
        """Show context menu for track items"""
        menu = QMenu()
        
        # Get row under cursor
        row = self.music_table.rowAt(position.y())
        if row < 0:
            return
            
        # Get the track at this row
        file_path = self.music_table.item(row, 7).text()
        selected_track = None
        for track in self.all_tracks:
            if track.file_path == file_path:
                selected_track = track
                break
                
        if not selected_track:
            return
        
        # Create actions    
        play_action = menu.addAction("Play")
        reveal_action = menu.addAction("Reveal in File Explorer")
        
        if selected_track.is_corrupt:
            error_action = menu.addAction("Show Error Details")
            remove_action = menu.addAction("Remove from Library")
        
        # Show the menu and get selected action
        action = menu.exec(self.music_table.viewport().mapToGlobal(position))
        
        # Handle the action
        if action == play_action:
            self.play_track(selected_track)
        elif action == reveal_action:
            self.reveal_file(selected_track.file_path)
        elif selected_track.is_corrupt and action == error_action:
            QMessageBox.critical(self, "File Error", f"Error in {selected_track.file_path}:\n{selected_track.error_message}")
        elif selected_track.is_corrupt and action == remove_action:
            self.all_tracks.remove(selected_track)
            self.update_music_table(self.all_tracks)
            self.statusBar().showMessage(f"Removed file from library: {os.path.basename(selected_track.file_path)}")
    
    def reveal_file(self, file_path):
        """Open file explorer to the file location"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Path not found: {file_path}")
            # Get directory containing the file
            directory = os.path.dirname(file_path)
            
            # Open file explorer to that directory
            if sys.platform == 'win32':
                os.startfile(directory)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{directory}"')
            else:  # Linux
                os.system(f'xdg-open "{directory}"')
        except Exception as e:
            self.show_error("Error revealing file", str(e))
            self.current_track.is_corrupt = True
            self.current_track.error_message = f"File location invalid: {str(e)}"
            self.update_music_table(self.all_tracks)
    
    def play_track(self, track):
        """Play a track"""
        if track.is_corrupt:
            QMessageBox.warning(self, "Cannot Play", f"Cannot play corrupted file: {os.path.basename(track.file_path)}")
            return
            
        try:
            self.current_track = track
            self.music_player.play(track.file_path)
            self.is_playing = True
            self.play_btn.setText("Pause")
            
            # Update now playing label
            self.now_playing_label.setText(f"Now Playing: {track.title} - {track.artist}")
            
            # Load the audio file in the waveform widget
            self.waveform_widget.load_audio(track.file_path)
            
            # Enable and setup the slider
            self.time_slider.setEnabled(True)
            self.time_slider.setValue(0)
            
            # Get track duration from the music player and update the total time label
            duration = self.music_player.get_duration()
            if duration > 0:
                self.time_slider.setRange(0, int(duration) * 1000)  # Convert to milliseconds
                minutes, seconds = divmod(duration, 60)
                self.total_time_label.setText(f"{int(minutes)}:{int(seconds):02d}")
            else:
                self.time_slider.setRange(0, 100)
                self.total_time_label.setText("0:00")
                
            # Start the timer for updating playback position
            self.playback_timer.start()
            
        except Exception as e:
            self.show_error("Error playing track", str(e))
            
    def update_playback_position(self):
        """Update the playback position slider"""
        if not self.is_playing or self.slider_being_dragged:
            return
            
        try:
            position = self.music_player.get_position()
            position_ms = int(position * 1000)  # Convert to milliseconds
            
            if position >= 0:
                self.time_slider.setValue(position_ms)
                
                # Update waveform position
                self.waveform_widget.set_position(position_ms)
                
                # Update current time label
                minutes, seconds = divmod(position, 60)
                self.current_time_label.setText(f"{int(minutes)}:{int(seconds):02d}")
                
                # Check if the track has ended
                if position >= self.music_player.get_duration():
                    self.stop_playback()
                    
        except Exception as e:
            logger.error(f"Error updating playback position: {str(e)}")
            
    def slider_pressed(self):
        """Called when the user starts dragging the slider"""
        self.slider_being_dragged = True
        
    def slider_released(self):
        """Called when the user stops dragging the slider"""
        try:
            position_ms = self.time_slider.value()
            position_seconds = position_ms / 1000.0
            
            # Update waveform position
            self.waveform_widget.set_position(position_ms)
            
            # Set player position
            self.music_player.set_position(position_seconds)
            
            # Update current time label
            minutes, seconds = divmod(position_seconds, 60)
            self.current_time_label.setText(f"{int(minutes)}:{int(seconds):02d}")
            
        except Exception as e:
            self.show_error("Error setting playback position", str(e))
        finally:
            self.slider_being_dragged = False
    
    def slider_value_changed(self, value):
        """Update time display while slider is being dragged"""
        if self.slider_being_dragged:
            minutes, seconds = divmod(value, 60)
            self.current_time_label.setText(f"{int(minutes)}:{int(seconds):02d}")
    
    def import_nml(self):
        """Import tracks from NML file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import NML File", "", "NML Files (*.nml)"
        )
        if file_path:
            try:
                # Create progress dialog
                self.progress_dialog = QProgressDialog("Importing NML file...", "Cancel", 0, 100, self)
                self.progress_dialog.setWindowTitle("Importing")
                self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                self.progress_dialog.setValue(0)
                self.progress_dialog.show()
                
                # Set progress callback
                self.music_scanner.set_progress_callback(self._update_progress)
                
                # Import the file
                self.music_scanner.import_from_nml(file_path)
                
                # Cleanup
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                
                self.all_tracks = self.music_scanner.get_tracks()
                self.update_music_table(self.all_tracks)
                self.update_genre_filter()
                
                # Count corrupted files
                corrupted_count = sum(1 for track in self.all_tracks if track.is_corrupt)
                
                self.statusBar().showMessage(
                    f"Imported {len(self.all_tracks)} tracks from NML file ({corrupted_count} corrupted)"
                )
            except Exception as e:
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                self.show_error("Error importing NML file", str(e))
    
    def export_nml(self):
        """Export tracks to NML file"""
        if not self.all_tracks:
            QMessageBox.warning(self, "Warning", "No tracks to export. Scan music files first.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export NML File", "", "NML Files (*.nml)"
        )
        if file_path:
            try:
                # Create progress dialog
                self.progress_dialog = QProgressDialog("Exporting to NML file...", "Cancel", 0, 100, self)
                self.progress_dialog.setWindowTitle("Exporting")
                self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                self.progress_dialog.setValue(0)
                self.progress_dialog.show()
                
                # Export the file
                self.music_scanner.export_to_nml(file_path)
                
                # Cleanup
                self.progress_dialog.setValue(100)
                self.progress_dialog.close()
                self.progress_dialog = None
                
                self.statusBar().showMessage(f"Exported {len(self.all_tracks)} tracks to NML file")
            except Exception as e:
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                self.show_error("Error exporting NML file", str(e))
    
    def create_playlist(self):
        """Create a new playlist from selected tracks"""
        selected_items = self.music_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select tracks for the playlist")
            return
        
        try:
            # Get unique rows from selected items
            rows = set(item.row() for item in selected_items)
            
            # Get the tracks that are currently displayed in the table
            filtered_tracks = []
            corrupted_count = 0
            
            for row in rows:
                file_path = self.music_table.item(row, 7).text()
                for track in self.all_tracks:
                    if track.file_path == file_path:
                        filtered_tracks.append(track)
                        if track.is_corrupt:
                            corrupted_count += 1
                        break
            
            if corrupted_count > 0:
                reply = QMessageBox.question(
                    self,
                    "Include Corrupted Files",
                    f"{corrupted_count} corrupted tracks selected.\n"
                    "These will be unplayable in the playlist.\n"
                    "Include them anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    filtered_tracks = [t for t in filtered_tracks if not t.is_corrupt]
            
            if not filtered_tracks:
                QMessageBox.warning(self, "Warning", "No valid tracks selected for playlist")
                return
            
            # Get playlist name
            name, ok = QInputDialog.getText(self, "Create Playlist", "Enter playlist name:")
            if ok and name:
                self.music_scanner.create_playlist(name, filtered_tracks)
                self.statusBar().showMessage(f"Created playlist '{name}' with {len(filtered_tracks)} tracks")
        except Exception as e:
            self.show_error("Error creating playlist", str(e))
    
    def play_selected_track(self, index):
        """Play the track that was double-clicked"""
        try:
            row = index.row()
            file_path = self.music_table.item(row, 7).text()
            
            # Find the track object
            for track in self.all_tracks:
                if track.file_path == file_path:
                    if track.is_corrupt:
                        QMessageBox.warning(
                            self, 
                            "Cannot Play", 
                            f"Cannot play corrupted file: {os.path.basename(track.file_path)}"
                        )
                        return
                    self.play_track(track)
                    break
        except Exception as e:
            self.show_error("Error playing track", str(e))
    
    def toggle_play(self):
        if not self.current_track:
            selected_items = self.music_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Warning", "Please select a track to play")
                return
            
            try:
                row = selected_items[0].row()
                file_path = self.music_table.item(row, 7).text()
                
                # Find the track object
                for track in self.all_tracks:
                    if track.file_path == file_path:
                        if track.is_corrupt:
                            QMessageBox.warning(
                                self, 
                                "Cannot Play", 
                                f"Cannot play corrupted file: {os.path.basename(track.file_path)}"
                            )
                            return
                        self.play_track(track)
                        return  # We've already started playing, so exit the method
                        
            except Exception as e:
                self.show_error("Error selecting track", str(e))
                return
        
        try:
            if self.is_playing:
                self.music_player.pause()
                self.play_btn.setText("Play")
                self.playback_timer.stop()  # Stop updating the slider
            else:
                self.music_player.play(self.current_track.file_path)
                self.play_btn.setText("Pause")
                
                # Update now playing label
                self.now_playing_label.setText(
                    f"Now Playing: {self.current_track.title} - {self.current_track.artist}"
                )
                
                # Start the timer for updating playback position
                self.playback_timer.start()
            
            self.is_playing = not self.is_playing
        except Exception as e:
            self.show_error("Error during playback", str(e))
    
    def stop_playback(self):
        try:
            self.music_player.stop()
            self.is_playing = False
            self.play_btn.setText("Play")
            self.current_track = None
            self.now_playing_label.setText("Not Playing")
            
            # Reset waveform
            self.waveform_widget.set_position(0)
            
            # Reset and disable the slider
            self.time_slider.setValue(0)
            self.time_slider.setEnabled(False)
            self.current_time_label.setText("0:00")
            self.total_time_label.setText("0:00")
            
            # Stop the playback timer
            self.playback_timer.stop()
            
        except Exception as e:
            self.show_error("Error stopping playback", str(e))
    
    def set_volume(self, value):
        try:
            self.music_player.set_volume(value)
        except Exception as e:
            self.show_error("Error setting volume", str(e))
    
    def show_error(self, title, message):
        """Show error dialog with details"""
        logger.error(f"{title}: {message}")
        logger.error(traceback.format_exc())
        
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle(title)
        error_dialog.setText(message)
        error_dialog.setDetailedText(traceback.format_exc())
        error_dialog.exec()
        
        # Also log to console
        print(f"ERROR: {title} - {message}")
        print(traceback.format_exc())

    def _update_progress(self, value, message, current=None, total=None):
        """Update progress dialog with current status"""
        logger.debug(f"Progress update: {value}% - {message}")
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            
            # Set the label text based on available information
            if current is not None and total is not None:
                # If we have current and total counts, show them in the dialog
                elapsed_time = ""
                if self.scan_start_time:
                    elapsed = time.time() - self.scan_start_time
                    elapsed_time = f"\nElapsed time: {time.strftime('%M:%S', time.gmtime(elapsed))}"
                
                self.progress_dialog.setLabelText(
                    f"Processing: {os.path.basename(message)}\n"
                    f"File {current} of {total} ({value}%){elapsed_time}"
                )
            else:
                # Simple status message
                self.progress_dialog.setLabelText(f"{message}")
            
            # This is critical to keep the UI responsive
            QApplication.processEvents()  # Ensure UI updates

    def migrate_formats(self):
        """Migrate between different DJ software formats"""
        dialog = FormatMigrationDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        source_format = dialog.get_source_format()
        target_format = dialog.get_target_format()
        options = dialog.get_options()
        
        if source_format == target_format:
            QMessageBox.warning(self, "Invalid Selection", "Source and target formats must be different")
            return
        
        # Get source file
        source_extensions = {
            "nml": "Traktor Files (*.nml)", 
            "xml": "Rekordbox Files (*.xml)",
            "csv": "Serato Files (*.csv)",
            "m3u": "M3U Playlist Files (*.m3u *.m3u8)"
        }
        
        source_file, _ = QFileDialog.getOpenFileName(
            self, f"Select {source_format.upper()} Source File", "", 
            source_extensions.get(source_format, "All Files (*)")
        )
        
        if not source_file:
            return
        
        # Get target file
        target_extensions = {
            "nml": "nml", 
            "xml": "xml", 
            "csv": "csv",
            "m3u": "m3u",
            "m3u8": "m3u8"
        }
        target_file, _ = QFileDialog.getSaveFileName(
        self, f"Save {target_format.upper()} Target File", "",
            f"{target_format.upper()} Files (*.{target_extensions.get(target_format)})"
        )
        
        if not target_file:
            return
        
        try:
            # Create progress dialog
            self.progress_dialog = QProgressDialog(f"Migrating from {source_format} to {target_format}...", 
            "Cancel", 0, 100, self)
            self.progress_dialog.setWindowTitle("Format Migration")
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.show()
            
            # Start timer for elapsed time display
            self.scan_start_time = time.time()
            self.timer.start(1000)
            
            # Perform the migration
            self.music_scanner.migrate_format(
            source_file, target_file, 
            source_format, target_format,
            options,
            progress_callback=self._update_progress
            )
            
            # Cleanup
            self.timer.stop()
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
                
                QMessageBox.information(
                self, "Migration Complete", 
                f"Successfully migrated from {source_format.upper()} to {target_format.upper()}"
                )
        
        except Exception as e:
            self.timer.stop()
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
                self.show_error("Migration Error", str(e))

    def import_m3u(self):
        """Import tracks from M3U/M3U8 playlist file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import M3U/M3U8 Playlist File", "", "M3U/M3U8 Playlist Files (*.m3u *.m3u8)"
        )
        if file_path:
            try:
                # Create progress dialog
                self.progress_dialog = QProgressDialog("Importing M3U/M3U8 playlist...", "Cancel", 0, 100, self)
                self.progress_dialog.setWindowTitle("Importing")
                self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                self.progress_dialog.setValue(0)
                self.progress_dialog.show()
                
                # Set progress callback
                self.music_scanner.set_progress_callback(self._update_progress)
                
                # Import the file
                self.music_scanner.import_from_m3u(file_path)
                
                # Cleanup
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                
                self.all_tracks = self.music_scanner.get_tracks()
                self.update_music_table(self.all_tracks)
                self.update_genre_filter()
                
                # Count corrupted files
                corrupted_count = sum(1 for track in self.all_tracks if track.is_corrupt)
                
                self.statusBar().showMessage(
                    f"Imported {len(self.all_tracks)} tracks from M3U/M3U8 playlist ({corrupted_count} corrupted)"
                )
            except Exception as e:
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                self.show_error("Error importing M3U/M3U8 playlist", str(e))

    def export_m3u(self):
        """Export tracks to M3U/M3U8 playlist file"""
        if not self.all_tracks:
            QMessageBox.warning(self, "Warning", "No tracks to export. Scan music files first.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export M3U/M3U8 Playlist File", "", "M3U/M3U8 Playlist Files (*.m3u *.m3u8)"
        )
        if file_path:
            try:
                # Create progress dialog
                self.progress_dialog = QProgressDialog("Exporting to M3U/M3U8 playlist...", "Cancel", 0, 100, self)
                self.progress_dialog.setWindowTitle("Exporting")
                self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                self.progress_dialog.setValue(0)
                self.progress_dialog.show()
                
                # Export the file
                self.music_scanner.export_to_m3u(file_path)
                
                # Cleanup
                self.progress_dialog.setValue(100)
                self.progress_dialog.close()
                self.progress_dialog = None
                
                self.statusBar().showMessage(f"Exported {len(self.all_tracks)} tracks to M3U/M3U8 playlist")
            except Exception as e:
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                self.show_error("Error exporting M3U/M3U8 playlist", str(e))

    def set_position_from_waveform(self, position_ms):
        """Set the playback position from waveform click"""
        if self.current_track:
            position_seconds = position_ms / 1000.0
            self.music_player.set_position(position_seconds)
            
            # Update time slider
            self.time_slider.setValue(position_ms)
            
            # Update time label
            minutes, seconds = divmod(position_seconds, 60)
            self.current_time_label.setText(f"{int(minutes)}:{int(seconds):02d}")

# Add this code to run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DJMusicOrganizer()
    window.show()
    sys.exit(app.exec())