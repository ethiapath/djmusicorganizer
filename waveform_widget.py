import os
import numpy as np
import librosa
import logging
from PyQt6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt6.QtGui import QPainter, QPen, QColor, QLinearGradient, QPainterPath
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal

logger = logging.getLogger(__name__)

class WaveformWidget(QGraphicsView):
    position_changed = pyqtSignal(int)  # Signal to emit when user clicks on waveform (milliseconds)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup the scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Initialize variables
        self.waveform_data = None
        self.duration = 0
        self.current_position = 0
        self.waveform_color = QColor(0, 122, 255)  # Blue color
        self.playhead_color = QColor(255, 0, 0)    # Red color
        
        # Create waveform and playhead items
        self.waveform_item = WaveformItem()
        self.playhead_item = PlayheadItem()
        
        # Add items to scene
        self.scene.addItem(self.waveform_item)
        self.scene.addItem(self.playhead_item)
        
        # Set scene and view properties
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setMouseTracking(True)
        
    def load_audio(self, filepath):
        """Load audio file and generate waveform data"""
        try:
            # Load audio file with librosa
            y, sr = librosa.load(filepath, sr=None, mono=True)
            self.duration = librosa.get_duration(y=y, sr=sr) * 1000  # Duration in milliseconds
            
            # Generate waveform data (simplified for performance)
            # Downsample to reduce data points for faster rendering
            hop_length = max(1, len(y) // 1000)
            self.waveform_data = librosa.feature.rms(y=y, frame_length=hop_length*2, hop_length=hop_length)[0]
            
            # Normalize data between -1 and 1
            if len(self.waveform_data) > 0:
                max_val = max(self.waveform_data.max(), abs(self.waveform_data.min()))
                if max_val > 0:
                    self.waveform_data = self.waveform_data / max_val
                    
            # Update the waveform display
            self.update_waveform()
            
            # Reset position
            self.set_position(0)
            
            logger.debug(f"Loaded audio file: {os.path.basename(filepath)}")
            
        except Exception as e:
            logger.error(f"Error loading audio for waveform: {str(e)}")
            self.waveform_data = None
            self.duration = 0
            
    def set_position(self, position_ms):
        """Set the current playback position in milliseconds"""
        if self.duration > 0:
            self.current_position = min(position_ms, self.duration)
            # Update playhead position
            self.update_playhead()
            
    def update_playhead(self):
        """Update the playhead position based on current_position"""
        if self.waveform_data is not None and self.duration > 0:
            rect = self.scene.sceneRect()
            x_pos = (self.current_position / self.duration) * rect.width()
            self.playhead_item.set_position(x_pos, rect.height())
            self.scene.update()
            
    def update_waveform(self):
        """Update the waveform display"""
        if self.waveform_data is not None:
            # Update scene rect to match view size
            rect = QRectF(0, 0, self.viewport().width(), self.viewport().height())
            self.scene.setSceneRect(rect)
            
            # Update waveform item
            self.waveform_item.set_waveform_data(self.waveform_data)
            self.waveform_item.update_geometry(rect)
            
            # Update playhead
            self.update_playhead()
            
    def resizeEvent(self, event):
        """Handle resize events to update the waveform display"""
        super().resizeEvent(event)
        self.update_waveform()
        
    def mousePressEvent(self, event):
        """Handle mouse click events to seek in the audio"""
        if self.waveform_data is not None and self.duration > 0:
            # Convert mouse position to scene position
            scene_pos = self.mapToScene(event.pos())
            
            # Calculate position in milliseconds
            position_ratio = scene_pos.x() / self.scene.sceneRect().width()
            position_ms = int(position_ratio * self.duration)
            
            # Update playhead
            self.set_position(position_ms)
            
            # Emit position changed signal
            self.position_changed.emit(position_ms)
            
        super().mousePressEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release event"""
        super().mouseReleaseEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move event for hover effects"""
        super().mouseMoveEvent(event)
        
class WaveformItem(QGraphicsItem):
    """Graphics item for displaying the waveform"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent_widget = parent
        self.waveform_data = None
        self.width = 0
        self.height = 0
        self.path = QPainterPath()
        
    def set_waveform_data(self, data):
        """Set waveform data and update the path"""
        self.waveform_data = data
        self.update_path()
        self.update()
        
    def update_geometry(self, rect):
        """Update the geometry of the waveform"""
        self.width = rect.width()
        self.height = rect.height()
        self.update_path()
        self.update()
        
    def update_path(self):
        """Update the waveform path based on current data and dimensions"""
        if self.waveform_data is None or len(self.waveform_data) == 0:
            return
            
        # Clear existing path
        self.path = QPainterPath()
        
        # Calculate scaling factors
        x_scale = self.width / len(self.waveform_data)
        y_scale = self.height * 0.4  # Use 40% of height for amplitude scaling
        
        # Create path for waveform
        for i, value in enumerate(self.waveform_data):
            x = i * x_scale
            y = (self.height / 2) - (value * y_scale)
            
            if i == 0:
                self.path.moveTo(x, y)
            else:
                self.path.lineTo(x, y)
        
        # Add bottom half (mirror)
        for i in range(len(self.waveform_data) - 1, -1, -1):
            x = i * x_scale
            y = (self.height / 2) + (self.waveform_data[i] * y_scale)
            self.path.lineTo(x, y)
            
        # Close the path
        self.path.closeSubpath()
        
    def boundingRect(self):
        """Return the bounding rectangle of the item"""
        return QRectF(0, 0, self.width, self.height)
        
    def paint(self, painter, option, widget):
        """Paint the waveform"""
        if self.waveform_data is None or len(self.waveform_data) == 0:
            return
            
        # Set up gradient for waveform
        gradient = QLinearGradient(0, 0, 0, self.height)
        gradient.setColorAt(0, QColor(60, 180, 255, 200))  # Top color
        gradient.setColorAt(0.5, QColor(30, 147, 229, 200))  # Middle color
        gradient.setColorAt(1, QColor(60, 180, 255, 200))  # Bottom color
        
        # Draw waveform
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawPath(self.path)
        
        # Draw waveform outline
        painter.setPen(QPen(QColor(100, 200, 255, 150), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path)
        
class PlayheadItem(QGraphicsItem):
    """Graphics item for displaying the playhead"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent_widget = parent
        self.position = 0
        self.height = 0
        self.width = 2  # Width of playhead line
        
    def set_position(self, x, height):
        """Set the position of the playhead"""
        self.position = x
        self.height = height
        self.setPos(x - self.width / 2, 0)  # Center line on position
        self.update()
        
    def update_height(self, height):
        """Update the height of the playhead"""
        self.height = height
        self.update()
        
    def boundingRect(self):
        """Return the bounding rectangle of the item"""
        return QRectF(0, 0, self.width, self.height)
        
    def paint(self, painter, option, widget):
        """Paint the playhead"""
        painter.setPen(QPen(QColor(255, 0, 0), self.width))  # Red playhead
        painter.drawLine(QPointF(self.width / 2, 0), QPointF(self.width / 2, self.height)) 