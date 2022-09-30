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



# Create the haar cascade
iconRow = 0
neutralRow= 0
singleRow = 0
multiRow = 0
bookIcon = xlsxwriter.Workbook('./Icons.xlsx')
sheet1 = bookIcon.add_worksheet()
bookNeutral = xlsxwriter.Workbook('./NeutralImages.xlsx')
sheet2 = bookNeutral.add_worksheet()
bookSingle = xlsxwriter.Workbook('./Single.xlsx')
sheet3 = bookSingle.add_worksheet()
bookMultiple = xlsxwriter.Workbook('./Multiple.xlsx')
sheet4 = bookMultiple.add_worksheet()
destination_top ="./TestUsers"
destination_path_for_single_person_image = "./TestUsers/single"
destination_path_for_multi_person_image = "./TestUsers/multiple"
destination_path_for_no_face_image = "./TestUsers/none"
destination_path_for_icons = "./TestUsers/icons"

path_to_images = '/home/amiangshu/HDD2/Works/SaymaWork/Avatars/male'


#to find path of xml file containing haarCascade file
cfp =  "haarcascade_frontalface_alt2.xml"
#print(cfp)
# load the harcaascade in the cascade classifier
fc = cv2.CascadeClassifier(cfp)
# load the known faces and embeddings saved in last file
data = pickle.loads(open('face_enc', "rb").read())


def create_directory(dir_name):
    global error
    try:
        os.mkdir(dir_name)
        print("Directory '%s' created successfully" % dir_name)
    except OSError as error:
        print("Directory '%s' can not be created" % dir_name)


create_directory(destination_top)
create_directory(destination_path_for_single_person_image)
create_directory(destination_path_for_multi_person_image)
create_directory(destination_path_for_no_face_image)
create_directory(destination_path_for_icons)

for filename in os.listdir(path_to_images):
    print(filename)
    iPath = os.path.join(path_to_images, filename)
    img_ = PIL.Image.open(iPath)
    width, height = img_.size

    print("width: " + str(width) + " height: " + str(height) + " size:" + str(os.path.getsize(iPath)))
    if width <= 420 and height <= 420 and os.path.getsize(iPath) < 2000:
        shutil.copyfile(iPath, os.path.join(destination_path_for_icons, filename))
        sheet1.write(iconRow, 0, filename)
        iconRow = iconRow + 1
    else:
         cascPath = cfp
         image = cv2.imread(iPath)
         rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

         # #convert image to Greyscale for HaarCascade
         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
         faceCascade = cv2.CascadeClassifier(cascPath)
         faces = fc.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=6,minSize=(60, 60),flags=cv2.CASCADE_SCALE_IMAGE)

         # the facial embeddings for face in input
         encodings = face_recognition.face_encodings(rgb)
         print("number of people: " + str(len(encodings)))

         if(len(encodings) == 0):
             sheet2.write(neutralRow, 0, filename)
             neutralRow = neutralRow + 1
             shutil.copyfile(iPath, os.path.join(destination_path_for_no_face_image, filename))
         elif (len(encodings) == 1):
             sheet3.write(singleRow,0,filename)
             singleRow = singleRow + 1
             shutil.copyfile(iPath, os.path.join(destination_path_for_single_person_image, filename))
         elif(len(encodings) > 1):
             sheet4.write(multiRow, 0, filename)
             multiRow = multiRow + 1
             shutil.copyfile(iPath, os.path.join(destination_path_for_multi_person_image, filename))

bookIcon.close()
bookNeutral.close()
bookSingle.close()
bookMultiple.close()