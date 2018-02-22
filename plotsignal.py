from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QSizePolicy
import numpy as np



class PlotSignal(FigureCanvas):

    def __init__(self, parent=None, width=2.6, height=2.6, dpi=100):

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("#ECECEC")
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.mode = "one"
        hsv = plt.get_cmap('hsv')
        self.colors = hsv(np.linspace(0,1,30))
        self.numPlot = 0


    def clear(self):

        self.axes.cla()
        self.axes.set_facecolor("#ECECEC")
        self.draw()
        self.numPlot = 0


    def plotSig(self, dataX, dataY, title, legend):

        if (self.mode=="one"):
            self.axes.cla()
            self.numPlot = 0
        self.ax = self.axes.plot(dataX, dataY, color=self.colors[self.numPlot])
        self.numPlot += 1
        self.axes.legend(legend)
        self.axes.set_title(title)
        self.draw()


    def modeSwitch(self, mode):

        if self.mode != mode:
            self.numPlot = 0
        if mode == "one":
            self.mode = "one"
        elif mode == "multiple":
            self.mode = "multiple"
        elif mode  == "rectangle":
            self.mode = "rectangle"


    def returnMode(self):

        return self.mode