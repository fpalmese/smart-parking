import cv2,os,time,json
from djitellopy import Tello

slotColors = [
        [255, 255, 255],      #normal slot (white)
        [0, 230, 255],        #reserved slot (yellow)
        [255, 15, 0],          #paid slot (blue)
        [0, 0, 255]          #special slot (red)
]
imagesPath = "C:/Users/Admin/PycharmProjects/testCamera/personalParkings/raspCaptures"


def parkingFromJson(jPark):
    park = Parking(jPark["streamSource"], jPark["latitude"], jPark["longitude"], jPark["sizeX"], jPark["sizeY"])
    park.cameraResolution = (jPark["cameraResolution"][0], jPark["cameraResolution"][1])
    park.name = jPark["name"]
    for jSlot in jPark["slots"]:
        park.addSlot(ParkingSlot(jSlot["x"], jSlot["y"], jSlot["w"], jSlot["h"], jSlot["type"]))
    return park


def parkingFromFile(filename):
    config_file = open(filename, 'r')
    json_data = config_file.read()
    jPark = json.loads(json_data)
    return parkingFromJson(jPark)



def adaptSlotSizes(slots, inputResolution, outputResolution):
    for s in slots:
        x = int((s.coords[0][0] * outputResolution[0]) / inputResolution[0])
        y = int((s.coords[0][1] * outputResolution[1]) / inputResolution[1])
        s.coords[0] = (x, y)
        x = int((s.coords[1][0] * outputResolution[0]) / inputResolution[0])
        y = int((s.coords[1][1] * outputResolution[1]) / inputResolution[1])
        s.coords[1] = (x, y)
    return slots

class Parking:
    class_counter = 0
    def __init__(self,streamSource,latitude,longitude,sizeX,sizeY):
        Parking.class_counter += 1
        self.id = Parking.class_counter
        self.name = "Parking"
        self.streamSource = streamSource
        self.slots = []
        self.geoCoords = [latitude,longitude]
        self.sizes = [sizeX, sizeY]  # size of the parking (useful to generate the image for the user)
        self.cameraResolution = (1920,1080)
        self.path = imagesPath

    def addSlot(self,slot):
        slot.setId(len(self.slots)+1)
        self.slots.append(slot)

    def getEmptySlots(self):
        emptySlots = {}
        for slot in self.slots:
            if str(slot.type) not in emptySlots:
                emptySlots[str(slot.type)] = 0

            if slot.status == 0:
                emptySlots[str(slot.type)] += 1
        return emptySlots

    def getCameraImage(self, times=1):
        cap = cv2.VideoCapture(self.streamSource,cv2.CAP_FFMPEG)
        imgs = []
        tsucc = 0
        while (tsucc < times):
            success, img = cap.read()
            if not success or img is None:
                print("not success")
                continue
            img = cv2.resize(img, self.cameraResolution, None, 0.5, 0.5)
            tsucc += 1
            imgs.append(img)
        cap.release()
        return imgs

    def drawSlots(self,image=None):
        if image is None:
            image = self.getCameraImage()[0]
        #for slot in self.slots:
        #    crop = image[slot.coords[1]:slot.coords[3], slot.coords[0]:slot.coords[2]]
        #    cv2.imshow('Slot '+str(slot.id), crop)
        for slot in self.slots:
            cv2.rectangle(image, slot.coords[0], slot.coords[1], slotColors[slot.type], 2)
            midpointX = int(slot.coords[0][0] + 0.33 * (slot.coords[1][0] - slot.coords[0][0]))
            midpointY = int(slot.coords[1][1] - 0.1 * (slot.coords[1][1] - slot.coords[0][1]))
            cv2.putText(image,str(slot.id), (midpointX, midpointY), cv2.FONT_HERSHEY_SIMPLEX, 1, slotColors[slot.type],2)
            if slot.isEmpty():
                cv2.putText(image, "V", (midpointX, int(slot.coords[1][1] - 0.4 * (slot.coords[1][1] - slot.coords[0][1]))), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            else:
                cv2.putText(image, "X", (midpointX, int(slot.coords[1][1] - 0.4 * (slot.coords[1][1] - slot.coords[0][1]))), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        return image



    def exportImage(self):
        imgs = self.getCameraImage()
        img = imgs[0]
        if img is not None:
            cv2.imwrite(os.path.join(self.path , 'all'+str(self.id)+'.jpg'), img)
        return img

    def getSavedImage(self):
        return cv2.imread(os.path.join(self.path, str(self.id)+'.jpg'))

    def showRealtime(self, showSlots=True):
        cap = cv2.VideoCapture(self.streamSource, cv2.CAP_FFMPEG)
        while (True):
            success, img = cap.read()
            if (not success or img is None):
                print("not success")
                continue
            img = cv2.resize(img, self.cameraResolution, None, 0.5, 0.5)
            if(showSlots):
                img = self.drawSlots(img)
            cv2.imshow("Parking #" + str(self.id), img)
            #cv2.imshow('Output', img)
            if cv2.waitKey(1) == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def objectify(self):
        jPark = {}
        jPark["streamSource"] = self.streamSource
        jPark["latitude"] = self.geoCoords[0]
        jPark["longitude"] = self.geoCoords[1]
        jPark["sizeX"] = self.sizes[0]
        jPark["sizeY"] = self.sizes[1]
        jPark["name"] = self.name
        jPark["cameraResolution"] = [self.cameraResolution[0], self.cameraResolution[1]]
        jPark["slots"] = []
        for slot in self.slots:
            jSlot = {}
            jSlot["x"] = slot.coords[0][0]
            jSlot["y"] = slot.coords[0][1]
            jSlot["w"] = slot.coords[1][0] - slot.coords[0][0]
            jSlot["h"] = slot.coords[1][1] - slot.coords[0][1]
            jSlot["type"] = slot.type
            jSlot["state"] = slot.state
            jPark["slots"].append(jSlot)
        return jPark

    def jsonify(self):
        jPark = self.objectify()
        return json.dumps(jPark,indent=4)


class ParkingSlot:
    def __init__(self, x, y, w, h, type):
        self.id = 0
        self.coords = [(x, y), (x+w, y+h)]
        self.type = type    # car,bike,yellow etc...
        self.state = 0
        self.price = 0

    def setEmpty(self):
        self.state = 0

    def setOccupied(self):
        self.state = 1

    def isEmpty(self):
        return self.state == 0

    def setId(self, id):
        self.id = id
