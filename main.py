from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import cv2, math, numpy as np
from Parking import *
import time
from vehicle_count import *
from tryLBP import *
from tryVGG import *
from tryCNN import *
import json

foundCars = 0
parkings = []


class requestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        self.wfile.write(('<meta http-equiv="refresh" content="2"> found totally '+str(foundCars)+' cars.').encode())
        #self.wfile.write('<iframe width="600" height="380" src="https://rtsp.me/embed/7eGk93Dr/" frameborder="0" allowfullscreen=""></iframe>'.encode())

def updateParkingsMajority():
    nimgs = 3
    while True:
        for park in parkings:
            maj = {}
            imgs = park.getCameraImage(nimgs)
            for i in range(0,len(imgs)):
                img = imgs[i]
                for slot in park.slots:
                    if str(slot.id) not in maj:
                        maj[str(slot.id)] = 0
                    #print("Parsing park #"+str(park.id)+" slot #"+str(slot.id))
                    crop = img[slot.coords[0][1]:slot.coords[1][1], slot.coords[0][0]:slot.coords[1][0]]
                    crop = editCrop(crop)
                    #cv2.imshow('crop', crop)
                    #cv2.waitKey(0)
                    cv2.imwrite(os.path.join(park.path, str(slot.id) + '.jpg'), crop)
                    freq = analize_slot(crop)
                    #print(freq)
                    if (freq["car"] + freq["truck"] + freq["bus"] > 0):
                        maj[str(slot.id)]+=1
                    if(i==len(imgs)-1):
                        print("MAJ is ",maj)
                        if(maj[str(slot.id)]/nimgs > 0.5):
                            slot.setOccupied()
                        else:
                            slot.setEmpty()
        time.sleep(1)


def updateParkingsMultiAlg():
    nalgs = 4
    LBPfile = 'LBPtrained.sav'
    LBPmodel = pickle.load(open(LBPfile, 'rb'))
    VGGmodel = load_model('trainedVGG.h5')
    CNNmodel = tf.keras.models.load_model('C:/Users/Admin/PycharmProjects/testCamera/savedCnn/saved_modelA')
    while True:
        for park in parkings:
            img = park.getCameraImage()[0]
            for slot in park.slots:
                prediction = 0
                crop = img[slot.coords[0][1]:slot.coords[1][1], slot.coords[0][0]:slot.coords[1][0]]
                crop = editCrop(crop)
                """
                #YOLOv4
                algPred = analize_slot(crop)
                #print(freq)
                prediction += (algPred["car"] + algPred["truck"] + algPred["bus"] > 0)
                
                #LBP
                algPred = predictLBP(LBPmodel, crop)
                print(algPred[0])
                if(algPred[0] == 'busy'):
                    print("true")
                    prediction += 1
                """
                #VGG
                algPred = predictVGG16(VGGmodel, crop)
                if (algPred[0] == 'busy'):
                    prediction += 1
                """
                #CNN
                algPred = predictCNN(CNNmodel, crop)
                print(algPred)
                """


                if (algPred == 'busy'):
                    prediction += 1

                if prediction >= 1:
                    slot.setOccupied()
                else:
                    slot.setEmpty()
        time.sleep(1)

def editCrop(img):
    crop = img
    #crop = change_brightness(img,30)
    return crop


def fillCrop(img, size1,size2):
    h, w, c = img.shape
    newimg = np.zeros((size1, size2, 3), np.uint8)
    newimg[:] = (255, 255, 255)
    x = round((size1-w) / 2)
    y = round((size2-h) / 2)
    newimg[y:y+h, x:x+w] = img[0:h,0:w]
    return newimg


def updateParkingsYolo():
    while True:
        for park in parkings:
            imgs = park.getCameraImage()
            img = imgs[0]
            for slot in park.slots:
                print("Parsing park #" + str(park.id) + " slot #" + str(slot.id))
                crop = img[slot.coords[0][1]:slot.coords[1][1], slot.coords[0][0]:slot.coords[1][0]]
                cv2.imwrite(os.path.join(park.path, str(slot.id) + '.jpg'), crop)
                freq = analize_slot(crop)
                print(freq)
                if (freq["car"] + freq["truck"] + freq["bus"] > 0):
                    slot.setOccupied()
                else:
                    slot.setEmpty()
        time.sleep(1)


def loadConfig(config_filename):
    global parkings
    config_file = open(config_filename, 'r')
    json_data = config_file.read()
    configJson = json.loads(json_data)
    for jPark in configJson["parkings"]:
        parkings.append(parkingFromJson(jPark))


def main():
    #server = HTTPServer(('',8000),requestHandler)
    #th = Thread(target=server.serve_forever)
    #th.start()
    loadConfig("config/configSq.json")

    th1 = Thread(target=updateParkingsMultiAlg)
    #th1 = Thread(target=updateParkingsYolo)
    th2 = Thread(target=parkings[0].showRealtime)

    th1.start()
    th2.start()



if __name__ == '__main__':
    main()

