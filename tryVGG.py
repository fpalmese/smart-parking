from keras.layers import Input, Lambda, Dense, Flatten
from keras.models import Model
from keras.applications.vgg16 import VGG16
from keras.applications.vgg16 import preprocess_input
from keras.preprocessing import image
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
import numpy as np
from glob import glob
import matplotlib.pyplot as plt
from keras.preprocessing.image import ImageDataGenerator
from keras.models import load_model
import cv2
from imutils import paths
from sklearn.metrics import accuracy_score

def train():
    # re-size all the images to this
    IMAGE_SIZE = [224, 224]

    # use A for training, B for testing
    train_path = 'C:/Users/Admin/PycharmProjects/testCamera/personalParkings/raspCaptures/slotted/square'
    valid_path = 'C:/Users/Admin/PycharmProjects/testCamera/personalParkings/raspCaptures/slotted/square'

    # add preprocessing layer to the front of VGG
    vgg = VGG16(input_shape=IMAGE_SIZE + [3], weights='imagenet', include_top=False)

    # don't train existing weights
    for layer in vgg.layers:
        layer.trainable = False

    # useful for getting number of classes
    folders = glob('C:/Users/Admin/PycharmProjects/testCamera/personalParkings/raspCaptures/slotted/square/*')

    # our layers - you can add more if you want
    x = Flatten()(vgg.output)
    # x = Dense(1000, activation='relu')(x)
    prediction = Dense(len(folders), activation='softmax')(x)

    # create a model object
    model = Model(inputs=vgg.input, outputs=prediction)


    # tell the model what cost and optimization method to use
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    train_datagen = ImageDataGenerator(rescale=1. / 255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True)

    test_datagen = ImageDataGenerator(rescale=1. / 255)

    training_set = train_datagen.flow_from_directory(train_path, target_size=(224, 224), batch_size=32,
                                                     class_mode='categorical')

    test_set = test_datagen.flow_from_directory(valid_path, target_size=(224, 224), batch_size=32,
                                                class_mode='categorical')

    '''r=model.fit_generator(training_set,
                             samples_per_epoch = 8000,
                             nb_epoch = 5,
                             validation_data = test_set,
                             nb_val_samples = 2000)'''



    # fit the model
    r = model.fit_generator(training_set, validation_data=test_set, epochs=5, steps_per_epoch=len(training_set),
                            validation_steps=len(test_set))

    model.save('trainedVGG.h5')

def test():
    model = load_model('trainedVGG.h5')
    labels = []
    predictions = []
    for imagePath in paths.list_images('C:/Users/Admin/PycharmProjects/testCamera/personalParkings/raspCaptures/slotted/square'):
        img = cv2.imread(imagePath)
        img = cv2.resize(img, (224, 224), None, 0.5, 0.5)
        img = img[np.newaxis, :, :]
        prediction = model.predict(img)
        labels.append(imagePath.split('\\')[1])
        if np.argmax(prediction) == 0:
            predictions.append("busy")
        else:
            predictions.append("free")
    for i in range(len(labels)):
        print(str(i)+": " + str(predictions[i] == labels[i]))
    print("N. of images: ", len(labels), " Accuracy: ", accuracy_score(labels, predictions))


def predictVGG16(model,img):
    img = cv2.resize(img, (224, 224), None, 0.5, 0.5)
    img = img[np.newaxis, :, :]
    if np.argmax(model.predict(img)) == 0:
        return "busy"
    return "free"


if __name__ == '__main__':
    train()
    test()
