Yolo files:
	coco.names
	yolov3-320.cfg
	yolov3-320.weights
	vehicle-count.py used for analyzing slots
	tracker.py used from vehicle-count.py

Important for parking:
	main.py		contains the main (showRealtime and infer on each slot)
	Parking.py 	contains classes for parking and slots
	buildDataset.py	show realtime and save images of slots each time interval


for CNN:
	tryCNN.py	first approach to use a CNN from scratch (tutorial from tensorflow for classification)
	


for VGG:
	tryVGG.py	first approach to use vgg16

for LBP
	tryLBP.py	first approach to use LBP (https://gitlab.com/qualcomm-iot-reference-center/smart-parking-with-local-binary-patterns/-/tree/master)