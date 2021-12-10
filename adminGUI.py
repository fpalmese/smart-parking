import cv2
import tkinter as tk
from threading import Thread
from Parking import *
import glob

"""
filename = "C:/Users/Admin/PycharmProjects/testCamera/personalParkings/raspCaptures/full/2021_12_01_11_18_pm.jpg"
img = cv2.imread(filename)
img = cv2.resize(img, (1280, 720), None, 0.5, 0.5)
baseImg = img.copy()
"""

#Constants
adminGUIResolution = (1280, 720)
parkingResolution = (1920, 1080)
possibleActions = ["Add slot", "Edit slot", "Delete slot"]
possibleSlotTypes = ["Free slot (white)", "Reserved slot (yellow)", "Paid slot (blue)", "Special slot (red)"]


# variables
appRunning = False
currentParking = None
currentSlots = []
currentParkId = -1
selectedSlot = None

parkImage = None
showingImage = None
imageWithSlots = None

#editing slot var
LMouseDown = False
RMouseDown = False
action = 1
slotType = 0
ix = -1
iy = -1

def setSelectedSlot(index):
    global selectedSlot, currentSlots, showingImage, imageWithSlots
    selectedSlot = currentSlots.pop(index)
    showingImage = drawCurrentSlots(parkImage)
    imageWithSlots = showingImage.copy()
    drawSlot(showingImage, selectedSlot)


def mouse_handle(event, x, y, flags, param):
    global ix, iy, LMouseDown, RMouseDown, showingImage, parkImage, imageWithSlots,currentSlots, selectedSlot
    if event == cv2.EVENT_LBUTTONDOWN:
        LMouseDown = True
        if action == 0:
            ix = x
            iy = y
        if action == 1:
            index = findSlot(x,y)
            if index >= 0:
                ix = x
                iy = y
                setSelectedSlot(index)

    if event == cv2.EVENT_RBUTTONDOWN:
        RMouseDown = True
        if action == 1:
            index = findSlot(x,y)
            if index >= 0:
                ix = x
                iy = y
                setSelectedSlot(index)

    elif event == cv2.EVENT_MOUSEMOVE:
        if LMouseDown == True:
            if action == 0:
                img2 = imageWithSlots.copy()
                minV = min(x-ix, y-iy, key=abs)
                cv2.putText(img2,str(minV)+"x"+str(minV), (int(ix + 0.4*minV), int(iy+minV+15)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color=slotColors[slotType])
                cv2.rectangle(img2, pt1=(ix,iy), pt2=(ix + minV, iy + minV), color=slotColors[slotType], thickness=6)
                showingImage = img2.copy()

            if action == 1:
                if selectedSlot is not None:
                    newX = selectedSlot.coords[0][0] + (x-ix)
                    newY = selectedSlot.coords[0][1] + (y-iy)
                    selectedSlot.coords[0] = (newX, newY)
                    newX = selectedSlot.coords[1][0] + (x-ix)
                    newY = selectedSlot.coords[1][1] + (y-iy)
                    ix = x
                    iy = y
                    selectedSlot.coords[1] = (newX, newY)
                    img2 = imageWithSlots.copy()
                    drawSlot(img2, selectedSlot)
                    showingImage = img2.copy()

        if RMouseDown == True:
            if action == 1:
                if selectedSlot is not None:
                    minV = min((x-ix),(y-iy),key=abs)
                    p0 = selectedSlot.coords[0]
                    p1 = selectedSlot.coords[1]
                    newX = p1[0] + minV
                    newY = p1[1] + minV
                    size = newX-p0[0]
                    if size < 45:
                        newX = p0[0] + 45
                        newY = p0[1] + 45
                        size = 45
                    else:
                        ix = x
                        iy = y
                    selectedSlot.coords[1] = (newX, newY)
                    img2 = imageWithSlots.copy()
                    drawSlot(img2, selectedSlot)
                    cv2.putText(img2, str(size) + "x" + str(size), (int(p0[0] + 0.4 * size), int(p0[1] + size + 15)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color=slotColors[selectedSlot.type])
                    showingImage = img2.copy()


        if action == 2:
            img2 = imageWithSlots.copy()
            cv2.line(img2, (x - 10, y - 10), (x + 10, y + 10), (0, 0, 255), thickness=3)
            cv2.line(img2, (x - 10, y + 10), (x + 10, y - 10), (0, 0, 255), thickness=2)
            showingImage = img2.copy()


    elif event == cv2.EVENT_LBUTTONUP:
        LMouseDown = False
        if action == 0:
            minV = min(x - ix, y - iy, key=abs)
            if abs(minV) < 45:   #skip if slot is too short
                showingImage = drawCurrentSlots(parkImage)
                return
            #cv2.rectangle(showingImage, pt1=(ix,iy), pt2=(ix + minV, iy + minV), color=(0, 255, 255), thickness=4)
            #if we go into negative, swap coords
            if (minV < 0):
                minV = -minV
                ix = ix - minV
                iy = iy - minV
            slot = ParkingSlot(ix, iy, minV, minV, slotType)
            slot.id = len(currentSlots)+1
            currentSlots.append(slot)
            showingImage = drawCurrentSlots(parkImage)
            imageWithSlots = showingImage.copy()

        if action == 1:
            if selectedSlot is not None:
                currentSlots.insert(selectedSlot.id - 1,selectedSlot)
                showingImage = drawCurrentSlots(parkImage)
                imageWithSlots = showingImage.copy()
                selectedSlot = None

        if action == 2:
            index = findSlot(x, y)
            if index >= 0:
                deleteSlot(index)
                showingImage = drawCurrentSlots(parkImage)
                imageWithSlots = showingImage.copy()

    elif event == cv2.EVENT_RBUTTONUP:
        RMouseDown = False
        if action == 1:
            if selectedSlot is not None:
                currentSlots.insert(selectedSlot.id - 1,selectedSlot)
                showingImage = drawCurrentSlots(parkImage)
                imageWithSlots = showingImage.copy()
                selectedSlot = None

def findSlot(x,y):
    global currentSlots
    for i in range(0, len(currentSlots)):
        if currentSlots[i].coords[0][0] <= x <= currentSlots[i].coords[1][0] and currentSlots[i].coords[0][1] <= y <= currentSlots[i].coords[1][1]:
            return i
    return -1


def deleteSlot(index):
    global currentSlots
    currentSlots.pop(index)
    for j in range(index, len(currentSlots)):
        currentSlots[j].id = j + 1

def drawCurrentSlots(image):
    global currentSlots
    im2 = image.copy()
    for slot in currentSlots:
        drawSlot(im2,slot)
    return im2

def drawSlot(image,slot):
    cv2.rectangle(image, slot.coords[0], slot.coords[1], slotColors[slot.type], 2)
    midpointX = int(slot.coords[0][0] + 0.33 * (slot.coords[1][0] - slot.coords[0][0]))
    midpointY = int(slot.coords[1][1] - 0.1 * (slot.coords[1][1] - slot.coords[0][1]))
    cv2.putText(image, str(slot.id), (midpointX, midpointY), cv2.FONT_HERSHEY_SIMPLEX, 1, slotColors[slot.type], 2)

def parkingImageThread():
    global parkImage, showingImage, imageWithSlots, currentSlots
    cvWindow = False
    window_name = "Edit parking slots"
    while appRunning:
        if currentParking is not None:
            if not cvWindow:
                cv2.namedWindow(winname=window_name)
                cv2.setMouseCallback(window_name, mouse_handle)
                cvWindow = True
                parkImage = currentParking.getCameraImage()[0]
                imageWithSlots = drawCurrentSlots(parkImage)
                showingImage = imageWithSlots.copy()
        else:
            if cvWindow:
                cv2.destroyWindow(window_name)
                cvWindow = False

        while currentParking is not None:
            try:
                cv2.imshow(window_name, showingImage)
                if cv2.waitKey(10) == 27:
                    break
            except:
                print("error")
                continue

def resetParkInfo():
    global currentParking, currentSlots, currentParkId, parkImage, showingImage, imageWithSlots
    currentParking = None
    currentSlots = []
    currentParkId = -1
    parkImage = None
    showingImage = None
    imageWithSlots = None

def listAvailableParkings():
    parkings = []
    for p in glob.glob("C:/Users/Admin/PycharmProjects/testCamera/config/parkings/*.json"):
        parkings.append(p.replace("C:/Users/Admin/PycharmProjects/testCamera/config/parkings\\", ""))
    Parking.class_counter = len(parkings)
    return parkings

def is_float(value):
    try:
        float(value)
        return True
    except:
        return False

def controlWindow():
    root = tk.Tk()
    root.title("Smart Parking")
    root.geometry("300x350")
    pages = []
    parkingsInFolder = listAvailableParkings()

    def getTextInput(textElement):
        result = textElement.get(1.0, tk.END + "-1c")
        return str(result)

    def show(page):
        #hide other pages
        for p in pages:
            hide(p)
        #show current page elements
        page.pack()

    def hide(page):
        page.pack_forget()

    def showError(msg):
        errorLabel.pack()
        errorLabel.configure(text=msg)

    def hideError():
        errorLabel.pack_forget()

    def addInputText(labelText,page):
        label = tk.Label(page, text=labelText)
        inputText = tk.Text(page, height=1, width=20)
        label.pack()
        inputText.pack()
        return inputText

    def checkParkingParameters(name, stream):
        if name is None or name == "":
            showError("Name cannot be empty")
            return False
        if stream is None or stream == "":
            showError("Stream is not valid")
            return False
        return True

    def confirmParkingSettings():
        global currentParking
        hideError()
        name = getTextInput(parkNameInput).strip()
        stream = getTextInput(parkStreamSourceInput).strip()
        lat = getTextInput(parkLatitudeInput).strip()
        long = getTextInput(parkLongitudeInput).strip()
        sizeX = getTextInput(parkSizeXInput).strip()
        sizeY = getTextInput(parkSizeYInput).strip()
        if not is_float(lat):
            lat = 0
        if not is_float(long):
            long = 0
        if not is_float(sizeX):
            sizeX = 0
        if not is_float(sizeY):
            sizeY = 0
        if not checkParkingParameters(name, stream):
            return

        park = Parking(stream, lat, long, sizeX, sizeY)
        park.name = name
        park.cameraResolution = adminGUIResolution
        if currentParkId > -1:
            park.id = currentParkId
        currentParking = park
        editSlotsLabel.configure(text="Edit slots for: "+name)
        show(editSlotsPage)

    def updateExistingParkingList():
        parkingsInFolder = listAvailableParkings()
        menu = existingFilenameMenu["menu"]
        menu.delete(0, "end")
        for string in parkingsInFolder:
            menu.add_command(label=string,
                             command=lambda value=string: existingFilename.set(value))

    def goToExistingParkingPage():
        updateExistingParkingList()
        existingFilename.set(parkingsInFolder[0])
        show(selectExistingParkingPage)

    def openExistingParking():
        global currentSlots, currentParkId
        parkName = existingFilename.get()
        openedPark = parkingFromFile("C:/Users/Admin/PycharmProjects/testCamera/config/parkings/"+parkName)
        parkNameInput.insert(1.0, openedPark.name)
        parkStreamSourceInput.insert(1.0, openedPark.streamSource)
        parkLatitudeInput.insert(1.0, openedPark.geoCoords[0])
        parkLongitudeInput.insert(1.0, openedPark.geoCoords[1])
        parkSizeXInput.insert(1.0, openedPark.sizes[0])
        parkSizeYInput.insert(1.0, openedPark.sizes[1])
        currentSlots = adaptSlotSizes(openedPark.slots, parkingResolution, adminGUIResolution)
        currentParkId = int(parkName.replace(".json", ""))
        show(parkingInfoPage)

    def on_closing():
        global appRunning, currentParking
        currentParking = None
        appRunning = False
        root.quit()

    def saveSlotsParkingJson():
        global currentParking
        currentParking.slots = adaptSlotSizes(currentSlots, adminGUIResolution, parkingResolution)
        currentParking.cameraResolution = parkingResolution
        file = open("C:/Users/Admin/PycharmProjects/testCamera/config/parkings/"+str(currentParking.id)+".json","w")
        file.write(currentParking.jsonify())
        file.close()
        resetParkInfo()
        resetAll()
        show(homePage)

    def resetInputForm(inputText):
        inputText.delete('1.0', tk.END)

    def resetAll():
        resetInputForm(parkNameInput)
        resetInputForm(parkStreamSourceInput)
        resetInputForm(parkLatitudeInput)
        resetInputForm(parkLongitudeInput)
        resetInputForm(parkSizeXInput)
        resetInputForm(parkSizeYInput)

    def changeAction(sv):
        global action
        action = possibleActions.index(sv.get())

    def changeSlotType(sv):
        global slotType
        slotType = possibleSlotTypes.index(sv.get())

    def backToHomePage():
        resetParkInfo()
        resetAll()
        show(homePage)


    """--------------------------------
        HOME PAGE
    -------------------------------"""
    homePage = tk.Frame(root)
    pages.append(homePage)
    titleLabel = tk.Label(homePage, text="BASE5G: Smart Parking",pady=15)
    titleLabel.pack()
    photo = tk.PhotoImage(file=r"C:/Users/Admin/PycharmProjects/testCamera/logo.png")
    photo = photo.zoom(40)  # with 250, I ended up running out of memory
    photo = photo.subsample(300)  # mechanically, here it is adjusted to 32 instead of 32
    image = tk.Label(homePage, image=photo, width=40, height=40)
    image.pack()
    #Home button to open existing parking
    goToOpenParkingBtn = tk.Button(homePage, height=1, text="Open Existing parking",
                            command=goToExistingParkingPage)
    goToOpenParkingBtn.pack()
    # Home button to create new parking
    goToNewParkingBtn = tk.Button(homePage, height=1, text="Create new parking",
                           command=lambda: show(parkingInfoPage))
    goToNewParkingBtn.pack()

    """--------------------------------
        ParkingInfoPage
    --------------------------------
    """
    parkingInfoPage = tk.Frame(root)
    pages.append(parkingInfoPage)
    parkNameInput = addInputText("Name: ", parkingInfoPage)
    parkStreamSourceInput = addInputText("Stream source: ", parkingInfoPage)
    parkLatitudeInput = addInputText("Latitude: ", parkingInfoPage)
    parkLongitudeInput = addInputText("Longitude: ", parkingInfoPage)
    parkSizeXInput = addInputText("Size X: ", parkingInfoPage)
    parkSizeYInput = addInputText("Size Y: ", parkingInfoPage)
    confirmNewParkBtn = tk.Button(parkingInfoPage, height=1, text="Confirm Settings",
                           command=confirmParkingSettings)
    confirmNewParkBtn.pack()
    errorLabel = tk.Label(parkingInfoPage, text="Error", fg='#f00')

    backToParkInfoBtn = tk.Button(parkingInfoPage, height=1, text="Back to Home",
                                  command=backToHomePage)
    backToParkInfoBtn.pack()
    """--------------------------------
            selectExistingParkingPage
            this page contains the list of existing parkings to open
    --------------------------------
    """
    selectExistingParkingPage = tk.Frame(root)
    pages.append(selectExistingParkingPage)
    existingFilename = tk.StringVar(selectExistingParkingPage)

    selectExistingLabel = tk.Label(selectExistingParkingPage, text="Select one parking to open:")
    selectExistingLabel.pack()
    existingFilenameMenu = tk.OptionMenu(selectExistingParkingPage, existingFilename, *parkingsInFolder)
    existingFilenameMenu.pack()
    confirmOpenParkBtn = tk.Button(selectExistingParkingPage, height=1, text="Open",
                                  command=openExistingParking)
    confirmOpenParkBtn.pack()
    backToParkInfoBtn = tk.Button(selectExistingParkingPage, height=1, text="Back to Home",
                                  command=backToHomePage)
    backToParkInfoBtn.pack()

    """-----------------------------
                editSlotsPage
                this page contains all the tools to edit/add slots to the parking
    --------------------------------
    """
    editSlotsPage = tk.Frame(root)
    pages.append(editSlotsPage)
    editSlotsLabel = tk.Label(editSlotsPage, text="Edit slots for: ", pady=15)
    editSlotsLabel.pack()

    #action menu
    selectAcionLabel = tk.Label(editSlotsPage, text="Action to perform:")
    selectAcionLabel.pack()
    selectedAction = tk.StringVar(editSlotsPage)
    selectedAction.set(possibleActions[action])
    actionMenu = tk.OptionMenu(editSlotsPage, selectedAction, *possibleActions)
    actionMenu.pack()
    selectedAction.trace("w", lambda name, index, mode, sv=selectedAction: changeAction(sv))

    #slot type menu
    selectSlotTypeLabel = tk.Label(editSlotsPage, text="Slot type:",pady=15)
    selectSlotTypeLabel.pack()
    selectedSlotType = tk.StringVar(editSlotsPage)
    selectedSlotType.set(possibleSlotTypes[slotType])
    slotTypeMenu = tk.OptionMenu(editSlotsPage, selectedSlotType, *possibleSlotTypes)
    slotTypeMenu.pack()
    selectedSlotType.trace("w", lambda name, index, mode, sv=selectedSlotType: changeSlotType(sv))

    saveSlotsParkingBtn = tk.Button(editSlotsPage, height=1, text="Save Parking",
                                   command=saveSlotsParkingJson)
    saveSlotsParkingBtn.pack()
    backToParkInfoBtn = tk.Button(editSlotsPage, height=1, text="Back to Home",
                                    command=backToHomePage)
    backToParkInfoBtn.pack()

    # -----------------------------
    # -----------------------------
    show(homePage)  #show homepage at start
    root.protocol("WM_DELETE_WINDOW", on_closing) #define closing behaviour
    root.mainloop() #run root loop


def app():
    global appRunning
    appRunning = True
    th1 = Thread(target=controlWindow)
    th2 = Thread(target=parkingImageThread)
    th1.start()
    th2.start()


if __name__ == '__main__':
    app()

