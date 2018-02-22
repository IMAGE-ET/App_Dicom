import dicom
import numpy as np
from skimage.filters import threshold_otsu
from skimage.morphology import reconstruction



class DicomImages():

    def __init__(self):

        self.images = []
        self.segmentedImages = []


    def add(self, name_img):

        image = dicom.read_file(name_img).pixel_array
        if self.images == []:
            seed = np.copy(image)
            seed[1:-1, 1:-1] = image.max()
            filledImage = reconstruction(seed, image, method="erosion")
            threshold = threshold_otsu(filledImage)
            self.mask = filledImage<threshold
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
            value = np.mean(self.images[numElement][sizeY-posY2:sizeY-posY1+1,posX1:posX2+1])
        elif mode == "segmented":
            value = np.mean(self.segmentedImages[numElement][sizeY-posY2:sizeY-posY1+1,posX1:posX2+1])
        return value