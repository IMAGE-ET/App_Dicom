from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QSizePolicy
import numpy as np



class PlotDicom(FigureCanvas):

    def __init__(self, parent=None, width=2.6, height=2.6, dpi=100):

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("#ECECEC")
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.display_position = False
        self.posX = []
        self.posY = []
        self.pointsMode = "one"
        self.rectangleLock = False
        self.alpha = 1
        self.listPlotPoints = []
        hsv = plt.get_cmap('hsv')
        self.colors = hsv(np.linspace(0,1,30))
        self.listNumPointsRectangle = []


    def clear(self):

        self.axes.cla()
        self.axes.set_facecolor("#ECECEC")
        self.draw()
        self.display_position = False
        self.posX = []
        self.posY = []
        self.listPlotPoints = []
        self.listNumPointsRectangle = []


    def plotDicom(self, data, title):

        self.title = title
        self.data = data
        self.axes.cla()
        self.ax = self.axes.imshow(self.data, cmap="gray", extent=[1,self.data.shape[0],1,self.data.shape[1]])
        self.fig.canvas.mpl_connect('button_press_event', self.onPress)
        self.fig.canvas.mpl_connect('motion_notify_event', self.onMotion)
        self.fig.canvas.mpl_connect('button_release_event', self.onRelease)
        self.axes.set_title(self.title)
        if self.posX != []:
            if (self.pointsMode == "one") | (self.pointsMode == "multiple"):
                for i in range(len(self.posX)):
                    drawPos = self.axes.plot(self.posX[i], self.posY[i], color=self.colors[i], marker="+", alpha=self.alpha)
                    self.listPlotPoints.append(drawPos)
            elif self.pointsMode == "rectangle":
                for i in range(len(self.listNumPointsRectangle)):
                    indexEndRectangle = self.listNumPointsRectangle[i]
                    if i == 0:
                        indexStartRectangle = 0
                    else:
                        indexStartRectangle = self.listNumPointsRectangle[i-1]
                    drawPos = self.axes.plot(self.posX[indexStartRectangle:indexEndRectangle], self.posY[indexStartRectangle:indexEndRectangle], color=self.colors[i], marker="+", alpha=self.alpha)
                    self.listPlotPoints.append(drawPos)
        self.draw()
        if self.posX != []:
            if (self.pointsMode == "one") | (self.pointsMode == "multiple"):
                for i in range(len(self.posX)):
                    self.listPlotPoints[i].pop(0).remove()
            elif self.pointsMode == "rectangle":
                for i in range(len(self.listNumPointsRectangle)):
                    self.listPlotPoints[i].pop(0).remove()
            self.listPlotPoints = []


    def onPress(self, event):

        if event.inaxes != self.axes: return
        self.display_position = True
        if self.pointsMode == "one":
            self.posX = [int(event.xdata)]
            self.posY = [int(event.ydata)]
            for i in range(len(self.posX)):
                drawPos = self.axes.plot(self.posX[i], self.posY[i], color=self.colors[i], marker="+", alpha=self.alpha)
                self.listPlotPoints.append(drawPos)
            self.draw()
            for i in range(len(self.posX)):
                self.listPlotPoints[i].pop(0).remove()
            self.listPlotPoints = []
        elif self.pointsMode == "multiple":
            self.posX.append(int(event.xdata))
            self.posY.append(int(event.ydata))
            for i in range(len(self.posX)):
                drawPos = self.axes.plot(self.posX[i], self.posY[i], color=self.colors[i], marker="+", alpha=self.alpha)
                self.listPlotPoints.append(drawPos)
            self.draw()
            for i in range(len(self.posX)):
                self.listPlotPoints[i].pop(0).remove()
            self.listPlotPoints = []
        elif self.pointsMode == "rectangle":
            if self.rectangleLock == False:
                self.x0 = int(event.xdata)
                self.y0 = int(event.ydata)
                self.posX.append(self.x0)
                self.posY.append(self.y0)
                self.rectangleLock = True


    def onMotion(self, event):

        if event.inaxes != self.axes: return
        if (self.pointsMode == "rectangle") & self.rectangleLock:
            dx = int(event.xdata) - self.x0
            dy = int(event.ydata) - self.y0
            if self.listNumPointsRectangle != []:
                self.posX = self.posX[:self.listNumPointsRectangle[-1]]
                self.posY = self.posY[:self.listNumPointsRectangle[-1]]
            else:
                self.posX = []
                self.posY = []
            if dx >= 0:
                xBegin = self.x0
                xEnd = self.x0+dx+1
            else:
                xBegin = self.x0+dx
                xEnd = self.x0+1
            if dy >= 0:
                yBegin = self.y0
                yEnd = self.y0+dy+1
            else:
                yBegin = self.y0+dy
                yEnd = self.y0+1
            for x in range(xBegin, xEnd):
                for y in range(yBegin, yEnd):
                    self.posX.append(x)
                    self.posY.append(y)
            if self.listNumPointsRectangle != []:
                indexStartNewRectangle = self.listNumPointsRectangle[-1]
            else:
                indexStartNewRectangle = 0
            for i in range(len(self.listNumPointsRectangle)):
                indexEndRectangle = self.listNumPointsRectangle[i]
                if i == 0:
                    indexStartRectangle = 0
                else:
                    indexStartRectangle = self.listNumPointsRectangle[i-1]
                drawPos = self.axes.plot(self.posX[indexStartRectangle:indexEndRectangle], self.posY[indexStartRectangle:indexEndRectangle], color=self.colors[i], marker=".", alpha=self.alpha)
                self.listPlotPoints.append(drawPos)
            drawPos = self.axes.plot(self.posX[indexStartNewRectangle:], self.posY[indexStartNewRectangle:], color=self.colors[len(self.listNumPointsRectangle)], marker=".", alpha=self.alpha)
            self.draw()
            for i in range(len(self.listNumPointsRectangle)):
                self.listPlotPoints[i].pop(0).remove()
            self.listPlotPoints = []
            drawPos.pop(0).remove()


    def onRelease(self, event):

        if (self.pointsMode == "rectangle") & self.rectangleLock:
            self.listNumPointsRectangle.append(len(self.posX))
            for i in range(len(self.listNumPointsRectangle)):
                indexEndRectangle = self.listNumPointsRectangle[i]
                if i == 0:
                    indexStartRectangle = 0
                else:
                    indexStartRectangle = self.listNumPointsRectangle[i-1]
                drawPos = self.axes.plot(self.posX[indexStartRectangle:indexEndRectangle], self.posY[indexStartRectangle:indexEndRectangle], color=self.colors[i], marker=".", alpha=self.alpha)
                self.listPlotPoints.append(drawPos)
            self.draw()
            for i in range(len(self.listNumPointsRectangle)):
                self.listPlotPoints[i].pop(0).remove()
            self.listPlotPoints = []
            self.rectangleLock = False


    def clearPositions(self):

        self.posX = []
        self.posY = []
        self.plotDicom(self.data, self.title)
        self.listNumPointsRectangle = []


    def modeSwitch(self, mode):

        if self.pointsMode != mode:
            self.posX = []
            self.posY = []

        if mode == "one":
            self.pointsMode = "one"
            self.alpha = 1
        elif mode == "multiple":
            self.pointsMode = "multiple"
            self.alpha = 1
        elif mode  == "rectangle":
            self.pointsMode = "rectangle"
            self.alpha = 0.1


    def returnPointsMode(self):

        return self.pointsMode


    def position(self):

        return self.display_position, self.posX, self.posY


    def getListNumPointsRectangle(self):

        return self.listNumPointsRectangle