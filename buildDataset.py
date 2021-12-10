from threading import Thread
import cv2
import math
import numpy as np
from Parking import *
import time
from vehicle_count import *
from imutils import paths


parkings = []
parkingPath = "C:/Users/Admin/PycharmProjects/testCamera/personalParkings/raspCaptures"


def saveSlots(imagePath, parking):
    image = cv2.imread(imagePath)
    image = cv2.resize(image, (parking.cameraResolution[0], parking.cameraResolution[1]), None, 0.5, 0.5)
    for slot in parking.slots:
        crop = image[slot.coords[0][1]:slot.coords[1][1], slot.coords[0][0]:slot.coords[1][0]]
        cv2.imwrite(parkingPath + "/slotted/square/" + imagePath.replace(parkingPath, "") + "-" + str(slot.id) + '.jpg', crop)

def loadConfig(config_filename):
    global parkings
    config_file = open(config_filename, 'r')
    json_data = config_file.read()
    configJson = json.loads(json_data)
    for jPark in configJson["parkings"]:
        parkings.append(parkingFromJson(jPark))

def main():
    global parkings
    loadConfig("config/configSq.json")
    parking = parkings[0]

    for imagePath in paths.list_images(parkingPath):
        saveSlots(imagePath,parking)


if __name__ == '__main__':
    main()