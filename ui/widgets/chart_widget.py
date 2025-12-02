import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPen, QBrush
import pandas as pd
from datetime import datetime
import numpy as np

# Premium Colors (Matched with OrderBook)
COLOR_UP = "#ff6b6b"   # Red (Korean Market Up / Bid)
COLOR_DOWN = "#54a0ff" # Blue (Korean Market Down / Ask)
COLOR_BG = "#1e1e1e"
COLOR_GRID = "#2d2d2d" # Lighter grid
COLOR_TEXT = "#cccccc"
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

from ui.widgets.chart_settings_dialog import ChartSettingsDialog
from data.indicator_engine import indicator_engine
from PyQt6.QtWidgets import QPushButton, QHBoxLayout

class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 2, 5, 2)
        
        btn_indicators = QPushButton("Indicators")
        btn_indicators.setStyleSheet("background-color: #3e3e42; color: white; border: none; padding: 4px 8px;")
        btn_indicators.clicked.connect(self.open_settings)
        toolbar.addWidget(btn_indicators)
        toolbar.addStretch()
        
        self.layout.addLayout(toolbar)
        
        # Configure PyQtGraph Global Options
        pg.setConfigOption('background', COLOR_BG)
        pg.setConfigOption('foreground', COLOR_TEXT)
        pg.setConfigOptions(antialias=False)
        
        self.graphics_layout = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.graphics_layout)
        
        self.active_indicators = [] # List of dicts
        self.subplots = {} # name -> PlotItem
        self.timestamps = []
        
        # Initial Setup
        self.setup_layout()

    def setup_layout(self):
        """Rebuild layout based on active indicators."""
        self.graphics_layout.clear()
        self.subplots = {}
        
        # 1. Price Plot (Row 0)
        self.price_plot = self.graphics_layout.addPlot(row=0, col=0)
        self.price_plot.showGrid(x=True, y=True, alpha=0.3)
        self.price_plot.setLabel('right', 'Price')
        self.price_plot.getAxis('left').hide()
        self.price_plot.getAxis('right').show()
        self.price_plot.getAxis('bottom').hide()
        
        # 2. Volume Plot (Row 1)
        self.volume_plot = self.graphics_layout.addPlot(row=1, col=0)
        self.volume_plot.setMaximumHeight(100)
        self.volume_plot.setXLink(self.price_plot)
        self.volume_plot.showGrid(x=True, y=True, alpha=0.3)
        self.volume_plot.setLabel('right', 'Vol')
        self.volume_plot.getAxis('left').hide()
        self.volume_plot.getAxis('right').show()
        
        # 3. Sub-charts (Row 2+)
        row_idx = 2
        for ind in self.active_indicators:
            name = ind["name"]
            # Check if it's a sub-chart indicator
            if name in ["RSI", "MACD", "STOCH", "ATR", "ADX"]:
                plot = self.graphics_layout.addPlot(row=row_idx, col=0)
                plot.setMaximumHeight(100)
                plot.setXLink(self.price_plot)
                plot.showGrid(x=True, y=True, alpha=0.3)
                plot.setLabel('right', name)
                plot.getAxis('left').hide()
                plot.getAxis('right').show()
                self.subplots[name] = plot
                row_idx += 1
                
        # Crosshairs
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(COLOR_CROSSHAIR, width=1, style=Qt.PenStyle.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(COLOR_CROSSHAIR, width=1, style=Qt.PenStyle.DashLine))
        self.price_plot.addItem(self.v_line, ignoreBounds=True)
        self.price_plot.addItem(self.h_line, ignoreBounds=True)
        
        self.proxy = pg.SignalProxy(self.price_plot.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved)

    def open_settings(self):
        dialog = ChartSettingsDialog(self, self.active_indicators)
        if dialog.exec():
            self.active_indicators = dialog.get_indicators()
            self.setup_layout()
            # Trigger update if we have data? 
            # We need to store last df or wait for next update.
            # Ideally, we should request re-render.

    def update_chart(self, df: pd.DataFrame):
        if df.empty: return
        
        self.timestamps = df['timestamp'].tolist()
        x = range(len(self.timestamps))
        
        # Clear Plots
        self.price_plot.clear()
        self.volume_plot.clear()
        for plot in self.subplots.values():
            plot.clear()
            
        # Re-add crosshairs
        self.price_plot.addItem(self.v_line, ignoreBounds=True)
        self.price_plot.addItem(self.h_line, ignoreBounds=True)
        
        # Axis
        axis = DateAxisItem(self.timestamps, orientation='bottom')
        # Set axis for the last plot
        last_plot = self.volume_plot
        if self.subplots:
            last_plot = list(self.subplots.values())[-1]
        last_plot.setAxisItems({'bottom': axis})
        
        # Candle & Volume
        candle_data = []
        for i, row in enumerate(df.itertuples()):
            candle_data.append((i, row.open, row.close, row.low, row.high))
            color = COLOR_UP if row.close >= row.open else COLOR_DOWN
            bg = pg.BarGraphItem(x=i, height=row.volume, width=0.6, brush=pg.mkBrush(color), pen=pg.mkPen(None))
            self.volume_plot.addItem(bg)
            
        self.candle_item = CandlestickItem(candle_data)
        self.price_plot.addItem(self.candle_item)
        
        # Indicators
        for ind in self.active_indicators:
            name = ind["name"]
            params = ind["params"]
            color = params.get("color", "#ffffff")
            
            # Calculate
            result = indicator_engine.get_indicator(df, name, **params)
            
            # Render
            if name in ["SMA", "EMA"]:
                if isinstance(result, pd.Series):
                    self.price_plot.plot(x, result.values, pen=pg.mkPen(color, width=1.5))
            
            elif name == "BBANDS":
                if isinstance(result, dict):
                    upper = result["upper"].values
                    lower = result["lower"].values
                    p1 = self.price_plot.plot(x, upper, pen=pg.mkPen(color, width=1, style=Qt.PenStyle.DotLine))
                    p2 = self.price_plot.plot(x, lower, pen=pg.mkPen(color, width=1, style=Qt.PenStyle.DotLine))
                    fill = pg.FillBetweenItem(p1, p2, brush=pg.mkBrush(QColor(color).red(), QColor(color).green(), QColor(color).blue(), 30))
                    self.price_plot.addItem(fill)
            
            elif name in self.subplots:
                plot = self.subplots[name]
                if name == "MACD" and isinstance(result, dict):
                    plot.plot(x, result["macd"].values, pen=pg.mkPen(color, width=1.5))
                    plot.plot(x, result["signal"].values, pen=pg.mkPen("orange", width=1.5))
                    # Histogram
                    hist = result["hist"].values
                    brushes = [pg.mkBrush(COLOR_UP) if v >= 0 else pg.mkBrush(COLOR_DOWN) for v in hist]
                    bg = pg.BarGraphItem(x=x, height=hist, width=0.6, brushes=brushes, pen=pg.mkPen(None))
                    plot.addItem(bg)
                
                elif name == "STOCH" and isinstance(result, dict):
                    plot.plot(x, result["k"].values, pen=pg.mkPen(color, width=1.5))
                    plot.plot(x, result["d"].values, pen=pg.mkPen("orange", width=1.5))
                    # Overbought/Oversold lines
                    plot.addLine(y=80, pen=pg.mkPen("gray", style=Qt.PenStyle.DashLine))
                    plot.addLine(y=20, pen=pg.mkPen("gray", style=Qt.PenStyle.DashLine))
                
                elif name == "RSI" and isinstance(result, pd.Series):
                    plot.plot(x, result.values, pen=pg.mkPen(color, width=1.5))
                    plot.addLine(y=70, pen=pg.mkPen("gray", style=Qt.PenStyle.DashLine))
                    plot.addLine(y=30, pen=pg.mkPen("gray", style=Qt.PenStyle.DashLine))

    def mouse_moved(self, evt):
        pos = evt[0]
        if self.price_plot.sceneBoundingRect().contains(pos):
            mouse_point = self.price_plot.vb.mapSceneToView(pos)
            index = int(mouse_point.x())
            
            if 0 <= index < len(self.timestamps):
                self.v_line.setPos(index)
                self.h_line.setPos(mouse_point.y())
                
                # Sync Crosshair X to other plots (Optional, XLink handles view, but not line)
                # To sync line, we need to add v_line to all plots and update them.
                # For now, XLink is sufficient for view sync.


