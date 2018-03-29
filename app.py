import sys
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QLabel, QPushButton, QSizePolicy, QWidget, QSlider, QLineEdit, QListView, QComboBox
from PyQt5.QtGui import QIntValidator, QStandardItemModel, QStandardItem
import dicom
import numpy as np
from numpy.linalg import inv, norm
from math import exp, sqrt
from skimage.filters import threshold_otsu
from skimage.morphology import reconstruction
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class DicomImages():

    def __init__(self):

        self.images = []
        self.segmentedImages = []
        self.acquisitionTimes = []
        self.defaultTime = -1


    def add(self, name_img):

        image = dicom.read_file(name_img).pixel_array
        acquisitionTime = cleanAcquisitionTimes(dicom.read_file(name_img).AcquisitionTime)
        if self.images == []:
            self.defaultTime = acquisitionTime
            threshold = threshold_otsu(image)
            self.mask = image<threshold
            self.utile = image>=threshold
            self.shapeImageX = image.shape[0]
            self.shapeImageY = image.shape[1]
        self.images.append(image)
        self.acquisitionTimes.append(round(acquisitionTime-self.defaultTime,6))
        image = dicom.read_file(name_img).pixel_array
        image[self.mask] = 0
        self.segmentedImages.append(image)


    def clear(self):

        self.images = []
        self.segmentedImages = []
        self.acquisitionTimes = []


    def length(self):

        return len(self.images)


    def shapeImages(self):

        return [self.shapeImageX, self.shapeImageY]


    def element(self, numElement, mode):

        if mode == "normal":
            return self.images[numElement]
        elif mode == "segmented":
            return self.segmentedImages[numElement]


    def valuePixel(self, numElement, posX, posY, mode):

        sizeY, sizeX = self.images[numElement].shape
        if mode == "normal":
            value = self.images[numElement][sizeY-posY, posX]
        elif mode == "segmented":
            value = self.segmentedImages[numElement][sizeY-posY, posX]
        return value


    def meanValue(self, numElement, posX1, posY1, posX2, posY2, mode):

        sizeY, sizeX = self.images[numElement].shape
        if mode == "normal":
            value = np.mean(self.images[numElement][sizeY-posY2:sizeY-posY1+1,posX1:posX2+1])
        elif mode == "segmented":
            value = np.mean(self.segmentedImages[numElement][sizeY-posY2:sizeY-posY1+1,posX1:posX2+1])
        return value


    def pixelUtiles(self):

        self.IUtile = np.zeros((len(self.images),np.sum(self.utile)))
        for i in range(len(self.images)):
            self.IUtile[i,:] = self.segmentedImages[i][self.utile]
            for j in range(np.sum(self.utile)):
                if self.IUtile[i,j] == 0:
                    self.IUtile[i,j] = 1
        return self.IUtile


    def indicesPixelUtiles(self):

        return self.utile


    def getAcquisitionTimes(self):

        return self.acquisitionTimes



class PlotDicom(FigureCanvas):

    def __init__(self, parent=None, width=2.6, height=2.6, dpi=100):

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("#ECECEC")
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.axes.tick_params(axis="both", which="both", bottom="off", top="off", left="off", right="off", labelleft="off",labelbottom="off")

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
        self.axes.tick_params(axis="both", which="both", bottom="off", top="off", left="off", right="off", labelleft="off",labelbottom="off")
        self.axes.set_facecolor("#ECECEC")
        self.draw()
        self.display_position = False
        self.posX = []
        self.posY = []
        self.listPlotPoints = []
        self.listNumPointsRectangle = []


    def plotDicom(self, data, title):

        self.axes.tick_params(reset=True)
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



class PlotI0T2(FigureCanvas):

    def __init__(self, parent=None, width=2.6, height=2.6, dpi=100):

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("#ECECEC")
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.axes.tick_params(axis="both", which="both", bottom="off", top="off", left="off", right="off", labelleft="off",labelbottom="off")



    def clear(self):

        self.axes.cla()
        self.axes.tick_params(axis="both", which="both", bottom="off", top="off", left="off", right="off", labelleft="off",labelbottom="off")
        self.axes.set_facecolor("#ECECEC")
        self.draw()


    def plotI0T2Error(self, data, title, colorlabel):

        self.axes.tick_params(reset=True)
        self.title = title
        self.data = data
        self.axes.cla()
        self.ax = self.axes.imshow(self.data, cmap="gnuplot", extent=[1,self.data.shape[0],1,self.data.shape[1]])
        self.colorbar = self.fig.colorbar(self.ax, shrink=0.8)
        self.colorbar.ax.set_yticklabels(self.colorbar.ax.get_yticklabels(), fontsize=6)
        self.colorbar.set_label(colorlabel, fontsize=6)
        self.axes.set_title(self.title, fontsize=8)
        for tick in self.axes.xaxis.get_major_ticks():
            tick.label.set_fontsize(6)
        for tick in self.axes.yaxis.get_major_ticks():
            tick.label.set_fontsize(6)
            tick.label.set_rotation('horizontal')
        self.draw()
        self.colorbar.remove()
        self.axes.cla()
        self.axes.clear()


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

        self.axes.tick_params(axis="both", which="both", bottom="off", top="off", left="off", right="off", labelleft="off",labelbottom="off")


    def clear(self):

        self.axes.cla()
        self.axes.tick_params(axis="both", which="both", bottom="off", top="off", left="off", right="off", labelleft="off",labelbottom="off")
        self.axes.set_facecolor("#ECECEC")
        self.draw()
        self.numPlot = 0


    def plotSig(self, dataX, dataY, title, legend):

        self.axes.tick_params(reset=True)
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



class Window(QWidget):

    def __init__(self):

        super().__init__()
        self.dicomImages = DicomImages()
        self.currentImage = 0
        self.segmentationMode = "normal"
        self.hasData = False
        self.nExp = 1
        self.figuresI0 = {}
        self.figuresT2 = {}
        self.figuresError = {}
        self.mapsI0 = {}
        self.mapsT2 = {}
        self.initUI()


    def initUI(self):

        importButton = QPushButton('Import files', self)
        importButton.clicked.connect(self.showDialog)

        clearButton = QPushButton('Clear', self)
        clearButton.clicked.connect(self.clearData)

        positionButton = QPushButton('Show position', self)
        positionButton.clicked.connect(self.showSignal)

        self.holdButton = QPushButton('Hold on', self)
        self.holdButton.clicked.connect(self.modeSwitchPositions)

        self.rectangleButton = QPushButton('Rectangle', self)
        self.rectangleButton.clicked.connect(self.modeSwitchPositions)

        self.clearPositionsButton = QPushButton('Clear positions', self)
        self.clearPositionsButton.clicked.connect(self.clearPositionsTicks)

        self.segmentedModeButton = QPushButton('Segmented', self)
        self.segmentedModeButton.clicked.connect(self.segmentedModeSwitch)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMaximum(0)
        self.slider.valueChanged.connect(self.valueSliderChanged)

        self.minSliderDisplay = QLabel("Min : {0}".format(0))
        self.maxSliderDisplay = QLabel("Max : {0}".format(self.slider.maximum()))

        self.changeValueText = QLabel("Choose image :")

        self.defineValue = QLineEdit(self)
        self.defineValue.setValidator(QIntValidator(0, self.slider.maximum()))
        self.defineValue.returnPressed.connect(self.valueTypedByHand)

        self.currentValueDisplay = QLabel("Current image : {0}".format(self.currentImage))

        self.plotImage = PlotDicom(self, width=0.2, height=0.2)

        self.plotSignal = PlotSignal(self, width=0.5, height=0.5)

        self.expText = QLabel("Number of exponentials : ")
        self.comboBoxExp = QComboBox()
        self.comboBoxExp.addItem("1")
        self.comboBoxExp.addItem("2")
        self.comboBoxExp.addItem("3")
        self.comboBoxExp.addItem("4")
        self.comboBoxExp.currentIndexChanged.connect(self.selectionExp)
        self.expGenerateButton = QPushButton('Generate', self)
        self.expGenerateButton.clicked.connect(self.expGenerate)


        self.figuresI0[0] = PlotI0T2(self, width=0.5, height=2)
        self.figuresI0[0].setFixedWidth(200)
        self.figuresI0[0].setFixedHeight(200)
        self.figuresT2[0] = PlotI0T2(self, width=0.5, height=2)
        self.figuresT2[0].setFixedWidth(200)
        self.figuresT2[0].setFixedHeight(200)
        self.figuresI0[1] = PlotI0T2(self, width=0.5, height=2)
        self.figuresI0[1].setFixedWidth(200)
        self.figuresI0[1].setFixedHeight(200)
        self.figuresT2[1] = PlotI0T2(self, width=0.5, height=2)
        self.figuresT2[1].setFixedWidth(200)
        self.figuresT2[1].setFixedHeight(200)
        self.figuresI0[2] = PlotI0T2(self, width=0.5, height=2)
        self.figuresI0[2].setFixedWidth(200)
        self.figuresI0[2].setFixedHeight(200)
        self.figuresT2[2] = PlotI0T2(self, width=0.5, height=2)
        self.figuresT2[2].setFixedWidth(200)
        self.figuresT2[2].setFixedHeight(200)
        self.figuresI0[3] = PlotI0T2(self, width=0.5, height=2)
        self.figuresI0[3].setFixedWidth(200)
        self.figuresI0[3].setFixedHeight(200)
        self.figuresT2[3] = PlotI0T2(self, width=0.5, height=2)
        self.figuresT2[3].setFixedWidth(200)
        self.figuresT2[3].setFixedHeight(200)

        for k in range(1,4):
            self.figuresI0[k].hide()
            self.figuresT2[k].hide()

        self.vbox1 = QVBoxLayout()
        self.vbox1.addWidget(importButton)
        self.vbox1.addWidget(clearButton)
        self.vbox1.addWidget(positionButton)
        self.vbox1.addWidget(self.holdButton)
        self.vbox1.addWidget(self.rectangleButton)
        self.vbox1.addWidget(self.clearPositionsButton)
        self.vbox1.addWidget(self.segmentedModeButton)

        self.hbox1 = QHBoxLayout()
        self.hbox1.addWidget(self.minSliderDisplay)
        self.hbox1.addWidget(self.slider)
        self.hbox1.addWidget(self.maxSliderDisplay)

        self.hbox2 = QHBoxLayout()
        self.hbox2.addWidget(self.changeValueText)
        self.hbox2.addWidget(self.defineValue)
        self.hbox2.addStretch(1)

        self.vbox2 = QVBoxLayout()
        self.vbox2.addLayout(self.hbox1)
        self.vbox2.addLayout(self.hbox2)
        self.vbox2.addWidget(self.currentValueDisplay)
        self.vbox2.addWidget(self.plotImage)
        self.vbox2.addWidget(self.plotSignal)

        self.vbox3 = QVBoxLayout()
        self.hbox7 = QHBoxLayout()
        self.hbox7.addWidget(self.expText)
        self.hbox7.addWidget(self.comboBoxExp)
        self.hbox7.addWidget(self.expGenerateButton)
        self.vbox3.addLayout(self.hbox7)
        self.hbox3 = QHBoxLayout()
        self.hbox3.addWidget(self.figuresI0[0])
        self.hbox3.addStretch()
        self.hbox3.addWidget(self.figuresT2[0])
        self.vbox3.addLayout(self.hbox3)
        self.hbox4 = QHBoxLayout()
        self.hbox4.addWidget(self.figuresI0[1])
        self.hbox4.addWidget(self.figuresT2[1])
        self.vbox3.addLayout(self.hbox4)
        self.hbox5 = QHBoxLayout()
        self.hbox5.addWidget(self.figuresI0[2])
        self.hbox5.addWidget(self.figuresT2[2])
        self.vbox3.addLayout(self.hbox5)
        self.hbox6 = QHBoxLayout()
        self.hbox6.addWidget(self.figuresI0[3])
        self.hbox6.addWidget(self.figuresT2[3])
        self.vbox3.addLayout(self.hbox6)
        self.vbox3.addStretch(1)

        self.vbox2widget = QWidget()
        self.vbox2widget.setLayout(self.vbox2)
        self.vbox2widget.setFixedWidth(400)

        self.hboxMain = QHBoxLayout()
        self.hboxMain.addLayout(self.vbox1)
        self.hboxMain.addStretch()
        self.hboxMain.addWidget(self.vbox2widget)
        self.hboxMain.addStretch()
        self.hboxMain.addLayout(self.vbox3)
        self.hboxMain.addStretch()

        self.setLayout(self.hboxMain)

        self.setGeometry(300,300,950,700)
        self.setWindowTitle('Application')
        self.show()


    def showDialog(self):

        fname = QFileDialog.getOpenFileNames(self, 'Open file', '/', 'DICOM images (*IMA)')
        if fname[0]:
            self.hasData = True
            for name_img in fname[0]:
                self.dicomImages.add(name_img)
            self.refreshImage()
            self.slider.setMinimum(0)
            self.slider.setMaximum(self.dicomImages.length()-1)
            self.maxSliderDisplay.setText("Max : {0}".format(self.slider.maximum()))
            self.defineValue.setValidator(QIntValidator(0, self.slider.maximum()))
            self.slider.setTickInterval(1)


    def clearData(self):

        self.hasData = False
        self.plotImage.clear()
        self.plotSignal.clear()
        self.dicomImages.clear()
        self.currentImageChanged(0)
        self.maxSliderDisplay.setText("Max : {0}".format(0))
        self.defineValue.setValidator(QIntValidator(0, 0))


    def showSignal(self):

        self.plotSignal.clear()
        display_position, posX, posY = self.plotImage.position()
        legend = []
        if display_position:
            dataX = range(self.dicomImages.length())
            if (self.plotImage.returnPointsMode() == "one") | (self.plotImage.returnPointsMode() == "multiple"):
                for i in range(len(posX)):
                    dataY = []
                    for element in dataX:
                        value = self.dicomImages.valuePixel(element, posX[i], posY[i], self.segmentationMode)
                        dataY.append(value)
                    legend.append("Pixel ({0},{1})".format(posX[i],posY[i]))
                    self.plotSignal.plotSig(dataX, dataY, "Evolution of pixel value", legend)
            elif self.plotImage.returnPointsMode() == "rectangle":
                listNumPointsRectangle = self.plotImage.getListNumPointsRectangle()
                for i in range(len(listNumPointsRectangle)):
                    indexEndRectangle = listNumPointsRectangle[i]
                    if i == 0:
                        indexStartRectangle = 0
                    else:
                        indexStartRectangle = listNumPointsRectangle[i-1]
                    minPosX, minPosY, maxPosX, maxPosY = min(posX[indexStartRectangle:indexEndRectangle]), min(posY[indexStartRectangle:indexEndRectangle]), max(posX[indexStartRectangle:indexEndRectangle]), max(posY[indexStartRectangle:indexEndRectangle])
                    dataY = []
                    for element in dataX:
                        value = self.dicomImages.meanValue(element, minPosX, minPosY, maxPosX, maxPosY, self.segmentationMode)
                        dataY.append(value)
                    legend.append("Mean value ({0},{1}),({2},{3})".format(minPosX,minPosY,maxPosX,maxPosY))
                    self.plotSignal.plotSig(dataX, dataY, "Evolution", legend)


    def valueSliderChanged(self):

        self.currentImage = self.slider.value()
        self.currentValueDisplay.setText("Current image : {0}".format(self.currentImage))
        self.defineValue.setText(str(self.currentImage))
        if self.hasData:
            self.refreshImage()

    def currentImageChanged(self, value):

        self.currentImage = value
        self.slider.setValue(self.currentImage)
        self.currentValueDisplay.setText("Current image : {0}".format(self.currentImage))


    def valueTypedByHand(self):

        value = int(self.defineValue.text())
        self.currentImageChanged(value)


    def modeSwitchPositions(self):

        sender = self.sender()
        if sender.text()=="Hold on":
            self.plotImage.modeSwitch("multiple")
            self.plotSignal.modeSwitch("multiple")
            self.holdButton.setText("Hold off")
        elif sender.text()=="Hold off":
            self.plotImage.modeSwitch("one")
            self.plotSignal.modeSwitch("one")
            self.holdButton.setText("Hold on")
        elif sender.text()=="Rectangle":
            self.plotImage.modeSwitch("rectangle")
            self.plotSignal.modeSwitch("rectangle")


    def clearPositionsTicks(self):

        if self.hasData:
            self.plotImage.clearPositions()
            self.plotSignal.clear()


    def segmentedModeSwitch(self):

        sender = self.sender()
        if sender.text()=="Segmented":
            self.segmentationMode = "segmented"
            self.segmentedModeButton.setText("Normal")
        elif sender.text()=="Normal":
            self.segmentationMode = "normal"
            self.segmentedModeButton.setText("Segmented")
        if self.hasData:
            self.refreshImage()


    def refreshImage(self):

        self.plotImage.plotDicom(self.dicomImages.element(self.currentImage, self.segmentationMode), "Image {0}".format(self.currentImage))


    def selectionExp(self,i):

        self.nExp = int(self.comboBoxExp.currentText())


    def expGenerate(self):

        if self.hasData:
            self.expGenerateButton.setText("Computing...")
            self.mapsI0 = {}
            self.mapsT2 = {}
            acquisitionTimes = self.dicomImages.getAcquisitionTimes()
            I = self.dicomImages.pixelUtiles()
            lamb = 0.1
            alpha = 1
            b = 0.05
            c = 10**(-4)
            self.X, self.f = optimLM(acquisitionTimes,I,lamb,alpha,self.nExp,b,c)
            shapeImage = self.dicomImages.shapeImages()
            mask = self.dicomImages.indicesPixelUtiles()
            for k in range(self.nExp):
                self.mapsI0[k] = np.zeros(shapeImage)
                self.mapsT2[k] = np.zeros(shapeImage)
            ind = 0
            for i in range(shapeImage[0]):
                for j in range(shapeImage[1]):
                    if mask[i,j]:
                        for k in range(self.nExp):
                            self.mapsI0[k][i,j] = self.X[ind,k]
                            self.mapsT2[k][i,j] = 1000*self.X[ind,k+self.nExp]
                        ind = ind+1
            for k in range(self.nExp):
                self.figuresI0[k].show()
                self.figuresT2[k].show()
                self.figuresI0[k].plotI0T2Error(data=self.mapsI0[k], title="Carte des I0_{0}".format(k), colorlabel="")
                self.figuresT2[k].plotI0T2Error(data=self.mapsT2[k], title="Carte des T2_{0}".format(k), colorlabel="ms")
            for k in range(self.nExp,4):
                self.figuresI0[k].hide()
                self.figuresT2[k].hide()
            self.expGenerateButton.setText("Generate")




def resource_path(relative_path):
     if hasattr(sys, '_MEIPASS'):
         return os.path.join(sys._MEIPASS, relative_path)
     return os.path.join(os.path.abspath("."), relative_path)



def optimLM(temps,I,lamb,alpha,n_exp,b,c):
    t = 100*np.asarray(temps)
    n_pixels = I.shape[1]
    x = np.ones((10,2))
    for i in range(10):
        x[i,0] = t[i]
    x_transpose = np.transpose(x)
    w = np.matmul(np.matmul(inv(np.matmul(x_transpose,x)),x_transpose),np.log(I[:10,:]))
    solu = np.zeros((n_pixels,2))
    for i in range(n_pixels):
        solu[i,0] = -1/w[0,i]
        solu[i,1] = exp(w[1,i])
    X0 = np.zeros((n_pixels,2*n_exp))
    for i in range(n_pixels):
        for j in range(n_exp):
            X0[i,j] = solu[i,1]/n_exp
            X0[i,j+n_exp] = solu[i,0]/(2**j)
    maxIter = 50
    tolX = 10**(-8)
    tolG = 10**(-8)
    tolF = 10**(-8)
    iteration = 0
    encore = True
    X = X0
    n = len(t)
    r = np.zeros(I.shape)
    temp_r = np.zeros(I.shape)
    g = np.zeros((n_pixels,2*n_exp))
    d = np.zeros((n_pixels,2*n_exp))
    J = np.zeros((n_pixels,n,2*n_exp))
    f = 0
    while encore:
        pas = alpha
        g_d = 0
        for i in range(n_pixels):
            temp = 0
            for j in range(n_exp):
                I0,T2 = X[i,j],X[i,n_exp+j]
                temp = temp + I0*np.exp(-np.divide(t,T2))
                J[i,:,j] = sqrt(2)*np.exp(-np.divide(t,T2))
                J[i,:,n_exp+j] = sqrt(2)*I0/(T2*T2)*np.multiply(t,np.exp(-np.divide(t,T2)))
            r[:,i] = sqrt(2)*(temp-I[:,i])
            J_utile = J[i,:,:]
            r_utile = r[:,i]
            J_transpose = np.transpose(J_utile)
            g[i,:] = np.matmul(J_transpose,r_utile)
            Jt_J = np.matmul(J_transpose,J_utile)
            J_diag = np.diag(np.diag(Jt_J))
            d[i,:] = -np.matmul(inv(Jt_J+lamb*J_diag),g[i,:])
            if np.matmul(np.transpose(d[i,:]),g[i,:])>0:
                d[i,:] = -d[i,:]
            g_d = g_d + np.matmul(np.transpose(d[i,:]),g[i,:])
        pas_invalide = True
        f = np.sum(0.5*np.matmul(r,np.transpose(r)))
        while pas_invalide:
            new_X = X+pas*d
            for i in range(n_pixels):
                temp = 0
                for j in range(n_exp):
                    I0,T2 = new_X[i,j],new_X[i,n_exp+j]
                    temp = temp + I0*np.exp(-np.divide(t,T2))
                temp_r[:,i] = sqrt(2)*(temp-I[:,i])
            new_f = np.sum(0.5*np.matmul(temp_r,np.transpose(temp_r)))
            alpha_g_d = c*pas*g_d
            if new_f>(f+alpha_g_d):
                pas = b*pas
            else:
                pas_invalide = False
        iteration = iteration+1
        if norm(g)<tolG:
            encore = False
        if norm(new_X-X)/norm(X)<tolX:
            encore = False
        if norm(new_f-f)/norm(f)<tolF:
            encore = False
        if iteration>=maxIter:
            encore = False
        X = new_X
        f = new_f
    X[:,n_exp:] = np.divide(X[:,n_exp:],100)
    return X, f


def cleanAcquisitionTimes(acquisitionTime):
    hour = float(acquisitionTime[0:2])
    minutes = float(acquisitionTime[2:4])
    seconds = float(acquisitionTime[4:6])
    decim = float(acquisitionTime[7:])*10**(-6)
    time = hour*3600+minutes*60+seconds+decim
    return time



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sshFile=resource_path("darkorange.stylesheet")
    with open(sshFile,"r") as fh:
        app.setStyleSheet(fh.read())
    sys.exit(app.exec_())