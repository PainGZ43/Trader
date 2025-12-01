import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPen, QBrush
import pandas as pd
from datetime import datetime
import numpy as np

# Premium Colors
COLOR_UP = "#FF4560"   # Red (Korean Market Up)
COLOR_DOWN = "#0081F2" # Blue (Korean Market Down)
COLOR_BG = "#1e1e1e"
COLOR_GRID = "#333333"
COLOR_TEXT = "#e0e0e0"
COLOR_CROSSHAIR = "#ffffff"

class DateAxisItem(pg.AxisItem):
    """
    Custom Axis Item to display dates/times correctly on X-axis.
    Maps integer index to timestamp string from data.
    """
    def __init__(self, timestamps, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timestamps = timestamps

    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            idx = int(v)
            if 0 <= idx < len(self.timestamps):
                ts = self.timestamps[idx]
                if isinstance(ts, str):
                    try:
                        # Try parsing ISO format
                        dt = datetime.fromisoformat(ts)
                        strings.append(dt.strftime('%H:%M'))
                    except:
                        strings.append(ts)
                elif isinstance(ts, (int, float)):
                    strings.append(datetime.fromtimestamp(ts).strftime('%H:%M'))
                else:
                    strings.append(str(ts))
            else:
                strings.append('')
        return strings

class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data  # data: list of (time_idx, open, close, min, max)
        self.generatePicture()

    def generatePicture(self):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        
        w = 0.4 # Candle width
        
        for (t, open, close, low, high) in self.data:
            if close >= open:
                color = QColor(COLOR_UP)
                p.setPen(pg.mkPen(color))
                p.setBrush(pg.mkBrush(color))
                # Draw High/Low line
                p.drawLine(pg.QtCore.QPointF(t, low), pg.QtCore.QPointF(t, high))
                # Draw Body
                p.drawRect(pg.QtCore.QRectF(t - w, open, w * 2, close - open))
            else:
                color = QColor(COLOR_DOWN)
                p.setPen(pg.mkPen(color))
                p.setBrush(pg.mkBrush(color))
                # Draw High/Low line
                p.drawLine(pg.QtCore.QPointF(t, low), pg.QtCore.QPointF(t, high))
                # Draw Body
                p.drawRect(pg.QtCore.QRectF(t - w, open, w * 2, close - open))
                
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())

class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Configure PyQtGraph Global Options
        pg.setConfigOption('background', COLOR_BG)
        pg.setConfigOption('foreground', COLOR_TEXT)
        pg.setConfigOptions(antialias=False) # False for sharper lines
        
        self.graphics_layout = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.graphics_layout)
        
        # 1. Price Plot (Top)
        self.price_plot = self.graphics_layout.addPlot(row=0, col=0)
        self.price_plot.showGrid(x=True, y=True, alpha=0.3)
        self.price_plot.setLabel('right', 'Price')
        self.price_plot.getAxis('left').hide() # Hide left axis
        self.price_plot.getAxis('right').show() # Show right axis
        self.price_plot.getAxis('bottom').hide() # Hide bottom axis (shared with volume)
        
        # 2. Volume Plot (Bottom)
        self.volume_plot = self.graphics_layout.addPlot(row=1, col=0)
        self.volume_plot.setMaximumHeight(100)
        self.volume_plot.setXLink(self.price_plot) # Link X-axis
        self.volume_plot.showGrid(x=True, y=True, alpha=0.3)
        self.volume_plot.setLabel('right', 'Vol')
        self.volume_plot.getAxis('left').hide()
        self.volume_plot.getAxis('right').show()
        
        # Crosshair Lines
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(COLOR_CROSSHAIR, width=1, style=Qt.PenStyle.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(COLOR_CROSSHAIR, width=1, style=Qt.PenStyle.DashLine))
        self.price_plot.addItem(self.v_line, ignoreBounds=True)
        self.price_plot.addItem(self.h_line, ignoreBounds=True)
        
        self.proxy = pg.SignalProxy(self.price_plot.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved)
        
        self.timestamps = []

    def update_chart(self, df: pd.DataFrame):
        """
        Update chart with new DataFrame.
        df columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        if df.empty:
            return

        self.price_plot.clear()
        self.volume_plot.clear()
        
        # Re-add crosshairs
        self.price_plot.addItem(self.v_line, ignoreBounds=True)
        self.price_plot.addItem(self.h_line, ignoreBounds=True)
        
        # Prepare Data
        self.timestamps = df['timestamp'].tolist()
        
        # Set Custom Axis
        axis = DateAxisItem(self.timestamps, orientation='bottom')
        self.volume_plot.setAxisItems({'bottom': axis})
        
        candle_data = []
        volume_items = []
        
        for i, row in enumerate(df.itertuples()):
            # Candle Data: (index, open, close, low, high)
            candle_data.append((i, row.open, row.close, row.low, row.high))
            
            # Volume Data
            color = COLOR_UP if row.close >= row.open else COLOR_DOWN
            bg = pg.BarGraphItem(x=i, height=row.volume, width=0.6, brush=pg.mkBrush(color), pen=pg.mkPen(None))
            self.volume_plot.addItem(bg)
            
        # Add Candle Item
        self.candle_item = CandlestickItem(candle_data)
        self.price_plot.addItem(self.candle_item)
        
        # Auto Range
        # self.price_plot.autoRange() # Optional, sometimes better to let user control

    def mouse_moved(self, evt):
        pos = evt[0]
        if self.price_plot.sceneBoundingRect().contains(pos):
            mouse_point = self.price_plot.vb.mapSceneToView(pos)
            index = int(mouse_point.x())
            
            # Snap to x index
            if 0 <= index < len(self.timestamps):
                self.v_line.setPos(index)
                self.h_line.setPos(mouse_point.y())
                
                # Update Label (Optional: could emit signal to update status bar)
                # ts = self.timestamps[index]
                # price = mouse_point.y()

