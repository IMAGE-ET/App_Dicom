import sys
import os
import dicom
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QLabel, QPushButton, QSizePolicy, QWidget, QSlider, QLineEdit, QListView
from PyQt5.QtGui import QIntValidator, QStandardItemModel, QStandardItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from skimage.filters import threshold_otsu



class DicomImages():

    def __init__(self):

        self.images = []
        self.segmentedImages = []


    def add(self, name_img):

        image = dicom.read_file(name_img).pixel_array
        if self.images == []:
            threshold = threshold_otsu(image)
            self.mask = image<threshold
        self.images.append(image)
        image = dicom.read_file(name_img).pixel_array
        image[self.mask] = 0
        self.segmentedImages.append(image)


    def clear(self):

        self.images = []
        self.segmentedImages = []


    def length(self):

        return len(self.images)


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
            value = np.mean(self.images[numElement][sizeY-posY1:sizeY-posY2+1,posX1:posX2+1])
        elif mode == "segmented":
            value = np.mean(self.segmentedImages[numElement][sizeY-posY1:sizeY-posY2+1,posX1:posX2+1])
        return value



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



class Window(QWidget):

    def __init__(self):

        super().__init__()
        self.dicomImages = DicomImages()
        self.currentImage = 0
        self.segmentationMode = "normal"
        self.hasData = False
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

        self.plotImage = PlotDicom(self, width=1.3, height=1.3)
        self.plotImage.hide()

        self.plotSignal = PlotSignal(self, width=1.3, height=1.3)
        self.plotSignal.hide()

        vbox1 = QVBoxLayout()
        vbox1.addWidget(importButton)
        vbox1.addWidget(clearButton)
        vbox1.addWidget(positionButton)
        vbox1.addWidget(self.holdButton)
        vbox1.addWidget(self.rectangleButton)
        vbox1.addWidget(self.clearPositionsButton)
        vbox1.addWidget(self.segmentedModeButton)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.minSliderDisplay)
        hbox1.addWidget(self.slider)
        hbox1.addWidget(self.maxSliderDisplay)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.changeValueText)
        hbox2.addWidget(self.defineValue)
        hbox2.addStretch(1)

        vbox2 = QVBoxLayout()
        vbox2.addLayout(hbox1)
        vbox2.addLayout(hbox2)
        vbox2.addWidget(self.currentValueDisplay)
        vbox2.addWidget(self.plotImage)
        vbox2.addWidget(self.plotSignal)

        hboxMain = QHBoxLayout()
        hboxMain.addLayout(vbox1)
        hboxMain.addLayout(vbox2)
        hboxMain.addStretch()

        self.setLayout(hboxMain)

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
            self.plotImage.show()


    def clearData(self):

        self.hasData = False
        self.plotImage.clear()
        self.plotSignal.clear()
        self.dicomImages.clear()
        self.currentImageChanged(0)
        self.maxSliderDisplay.setText("Max : {0}".format(0))
        self.defineValue.setValidator(QIntValidator(0, 0))
        self.plotImage.hide()
        self.plotSignal.hide()


    def showSignal(self):

        self.plotSignal.clear()
        display_position, posX, posY = self.plotImage.position()
        legend = []
        if display_position:
            self.plotSignal.show()
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



def resource_path(relative_path):
     if hasattr(sys, '_MEIPASS'):
         return os.path.join(sys._MEIPASS, relative_path)
     return os.path.join(os.path.abspath("."), relative_path)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sshFile=resource_path("darkorange.stylesheet")
    with open(sshFile,"r") as fh:
        app.setStyleSheet(fh.read())
    sys.exit(app.exec_())