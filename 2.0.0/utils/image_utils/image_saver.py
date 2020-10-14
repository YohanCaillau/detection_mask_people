import cv2
import os

person_count = [0]

current_path = os.getcwd()

def save_image(source_image):
	cv2.imwrite(current_path + "/detected_objects/object" + str(len(person_count)) + ".png", source_image)
	person_count.insert(0,1)
