import sys
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QLabel, QPushButton, QSizePolicy, QWidget, QSlider, QLineEdit, QListView
from PyQt5.QtGui import QIntValidator, QStandardItemModel, QStandardItem
from dicomimages import DicomImages
from plotdicom import PlotDicom
from plotsignal import PlotSignal



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

        self.plotSignal = PlotSignal(self, width=1.3, height=1.3)

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