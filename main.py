import sys
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QFileDialog,
                           QTableWidget, QTableWidgetItem, QComboBox,
                           QSpinBox, QLineEdit, QMessageBox, QInputDialog,
                           QProgressDialog, QHeaderView, QMenu, QToolTip)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QIcon, QFont, QColor
import os
import traceback
from music_scanner import MusicScanner
from music_player import MusicPlayer

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
        
        # Create playlist button
        create_playlist_btn = QPushButton("Create Playlist")
        create_playlist_btn.clicked.connect(self.create_playlist)
        toolbar.addWidget(create_playlist_btn)
        
        # Remove corrupted button
        remove_corrupted_btn = QPushButton("Remove Corrupted Files")
        remove_corrupted_btn.clicked.connect(self.remove_corrupted_files)
        toolbar.addWidget(remove_corrupted_btn)
        
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
        player_controls.addStretch()
        
        # Volume control
        self.volume_slider = QSpinBox()
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        player_controls.addWidget(QLabel("Volume:"))
        player_controls.addWidget(self.volume_slider)
        
        layout.addLayout(player_controls)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Initialize state
        self.current_track = None
        self.is_playing = False
        self.all_tracks = []
        self.progress_dialog = None
        
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
    
    def _update_progress(self, value, message):
        """Update progress dialog with current status"""
        logger.debug(f"Progress update: {value}% - {message}")
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            self.progress_dialog.setLabelText(f"Processing: {os.path.basename(message)}")
            QApplication.processEvents()  # Ensure UI updates
    
    def scan_music(self):
        logger.debug("scan_music method called")
        if not self.music_scanner.folders:
            logger.warning("No music folders added before scan attempt")
            QMessageBox.warning(self, "Warning", "No music folders have been added. Add a folder first.")
            return
            
        try:
            # Create a progress dialog
            logger.debug("Creating progress dialog for music scan")
            self.progress_dialog = QProgressDialog("Scanning music files...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowTitle("Scanning Music")
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setValue(0)
            self.progress_dialog.show()
            
            # Set progress callback
            self.music_scanner.set_progress_callback(self._update_progress)
            
            # Start scanning
            logger.debug(f"Starting scan of {len(self.music_scanner.folders)} folders")
            self.music_scanner.scan()
            
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
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            self.show_error("Error scanning music", str(e))
    
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
                        status_item.setToolTip(track.error_message)
                        
                        # Also color the row slightly red
                        title_item.setBackground(QColor(255, 220, 220))
                        artist_item.setBackground(QColor(255, 220, 220))
                        bpm_item.setBackground(QColor(255, 220, 220))
                        key_item.setBackground(QColor(255, 220, 220))
                        genre_item.setBackground(QColor(255, 220, 220))
                        energy_item.setBackground(QColor(255, 220, 220))
                    else:
                        status_item = QTableWidgetItem("OK")
                        status_item.setForeground(QColor("green"))
                    
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
            if os.path.exists(file_path):
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
        except Exception as e:
            self.show_error("Error playing track", str(e))
    
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
                    f"{corrupted_count} of {len(filtered_tracks)} selected tracks are corrupted. Include them anyway?",
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
                        self.current_track = track
                        break
            except Exception as e:
                self.show_error("Error selecting track", str(e))
                return
        
        try:
            if self.is_playing:
                self.music_player.pause()
                self.play_btn.setText("Play")
            else:
                self.music_player.play(self.current_track.file_path)
                self.play_btn.setText("Pause")
                
                # Update now playing label
                self.now_playing_label.setText(
                    f"Now Playing: {self.current_track.title} - {self.current_track.artist}"
                )
            
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

if __name__ == "__main__":
    logger.info("Application starting")
    app = QApplication(sys.argv)
    window = DJMusicOrganizer()
    logger.info("Main window created, showing UI")
    window.show()
    logger.info("Entering main application loop")
    sys.exit(app.exec()) 