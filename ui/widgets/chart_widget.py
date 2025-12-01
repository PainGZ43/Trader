import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
import pandas as pd
from datetime import datetime

class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data  # data must have fields: time, open, close, min, max
        self.generatePicture()

    def generatePicture(self):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        w = (self.data[1][0] - self.data[0][0]) / 3.
        for (t, open, close, min, max) in self.data:
            p.drawLine(pg.QtCore.QPointF(t, min), pg.QtCore.QPointF(t, max))
            if open > close:
                p.setBrush(pg.mkBrush('b'))
            else:
                p.setBrush(pg.mkBrush('r'))
            p.drawRect(pg.QtCore.QRectF(t-w, open, w*2, close-open))
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
        
        # Configure PyQtGraph
        pg.setConfigOption('background', '#1e1e1e')
        pg.setConfigOption('foreground', '#dcdcdc')
        pg.setConfigOptions(antialias=True)
        
        self.graphics_layout = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.graphics_layout)
        
        # Create Plot
        self.plot = self.graphics_layout.addPlot()
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setLabel('right', 'Price')
        self.plot.setLabel('bottom', 'Time')
        
        # Custom Axis for Time
        self.axis_x = self.plot.getAxis('bottom')
        
        # Crosshair
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#cccccc', width=1, style=Qt.PenStyle.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('#cccccc', width=1, style=Qt.PenStyle.DashLine))
        self.plot.addItem(self.v_line, ignoreBounds=True)
        self.plot.addItem(self.h_line, ignoreBounds=True)
        
        self.proxy = pg.SignalProxy(self.plot.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved)
        
        # Data Containers
        self.candles = []
        self.item = None

    def update_chart(self, df: pd.DataFrame):
        """
        Update chart with new DataFrame.
        df columns: ['timestamp', 'open', 'high', 'low', 'close']
        """
        if df.empty:
            return

        self.plot.clear()
        self.plot.addItem(self.v_line, ignoreBounds=True)
        self.plot.addItem(self.h_line, ignoreBounds=True)
        
        # Prepare data for CandlestickItem
        # Time needs to be float for plotting. We use index or timestamp.
        # Here we use simple index for X-axis to avoid gaps for non-trading times
        
        data = []
        for i, row in enumerate(df.itertuples()):
            # (time, open, close, min, max)
            data.append((i, row.open, row.close, row.low, row.high))
            
        self.item = CandlestickItem(data)
        self.plot.addItem(self.item)
        
        # Update Axis Labels (Show timestamp instead of index)
        # This is a simplified approach. For production, subclass AxisItem.
        ticks = []
        for i in range(0, len(df), max(1, len(df)//5)):
            ts = df.iloc[i]['timestamp']
            if isinstance(ts, (int, float)):
                ts_str = datetime.fromtimestamp(ts).strftime('%H:%M')
            else:
                ts_str = str(ts)
            ticks.append((i, ts_str))
        self.axis_x.setTicks([ticks])

    def mouse_moved(self, evt):
        pos = evt[0]
        if self.plot.sceneBoundingRect().contains(pos):
            mouse_point = self.plot.vb.mapSceneToView(pos)
            self.v_line.setPos(mouse_point.x())
            self.h_line.setPos(mouse_point.y())
