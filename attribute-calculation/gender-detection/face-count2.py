import pickle
import cv2
import face_recognition
import xlsxwriter
import PIL

imagePaths = []

######## male/female classification code ######

import os
import shutil
import cv2
from mtcnn import MTCNN



destination_top ="./TestUsers"
destination_path_for_single_person_image = "./TestUsers/single"
destination_path_for_multi_person_image = "./TestUsers/multiple"
destination_path_for_no_face_image = "./TestUsers/none"
destination_path_for_icons = "./TestUsers/icons"

path_to_images = '/home/amiangshu/Works/scratch/GenderClassification/TestUsers/'

detector = MTCNN()


def create_directory(dir_name):
    global error
    try:
        os.mkdir(dir_name)
        print("Directory '%s' created successfully" % dir_name)
    except OSError as error:
        print("Directory '%s' can not be created" % dir_name)



for filename in os.listdir(destination_path_for_no_face_image):
    print(filename)
    iPath = os.path.join(destination_path_for_no_face_image, filename)
    image = cv2.imread(iPath)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    detections = detector.detect_faces(image)
    print("number of people: " + str(len(detections)))
    if(len(detections) > 0):
        shutil.move(iPath, os.path.join(destination_path_for_single_person_image, filename))
