#----------------------------------------------
#--- Author         : Ahmet Ozlu
#--- Mail           : ahmetozlu93@gmail.com
#--- Date           : 27th January 2018
#----------------------------------------------

import tensorflow as tf
import cv2
import numpy as np
import json
from time import gmtime, strftime
from utils import visualization_utils as vis_util
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import load_model

# Variables
total_passed_person = 0  # using it to count people

def cumulative_object_counting_x_axis(input_video, detection_graph, category_index, is_color_recognition_enabled, roi, deviation):      
        total_passed_person = 0              

        # initialize .json
        with open("pedestrian_measurement.json", mode='w', encoding='utf-8') as file:
            json.dump([], file)

        # input video
        cap = cv2.VideoCapture(0)

        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        output_movie = cv2.VideoWriter('the_output.avi', fourcc, fps, (width, height))

        total_passed_person = 0
        direction = "waiting..."
        counting_mode = "..."
        width_heigh_taken = True
        with detection_graph.as_default():
          with tf.compat.v1.Session(graph=detection_graph) as sess:
            # Definite input and output Tensors for detection_graph
            image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

            # Each box represents a part of the image where a particular object was detected.
            detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

            # Each score represent how level of confidence for each of the objects.
            # Score is shown on the result image, together with the class label.
            detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
            detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')

            mask_model = load_model("C:/Users/utilisateur/Desktop/people_counting_tensorflow/api/mask_recog_ver2.h5")

            # for all the frames that are extracted from input video
            while(cap.isOpened()):
                ret, frame = cap.read()                

                if not  ret:
                    print("end of the video file...")
                    break
                
                input_frame = frame

                # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                image_np_expanded = np.expand_dims(input_frame, axis=0)

                # Actual detection.
                (boxes, scores, classes, num) = sess.run(
                    [detection_boxes, detection_scores, detection_classes, num_detections],
                    feed_dict={image_tensor: image_np_expanded})

                # insert information text to video frame
                font = cv2.FONT_HERSHEY_SIMPLEX

                # Visualization of the results of a detection.        
                counter, json_line, counting_mode = vis_util.visualize_boxes_and_labels_on_image_array_x_axis(cap.get(1),
                                                                                                             input_frame,
                                                                                                             1,
                                                                                                             is_color_recognition_enabled,
                                                                                                             np.squeeze(boxes),
                                                                                                             np.squeeze(classes).astype(np.int32),
                                                                                                             np.squeeze(scores),
                                                                                                             category_index,
                                                                                                             x_reference = roi,
                                                                                                             deviation = deviation,
                                                                                                             use_normalized_coordinates=True,
                                                                                                             line_thickness=4)
                               
                # when the person passed over line and counted, make the color of ROI line green
                if counter == 1:
                  cv2.line(input_frame, (roi, 0), (roi, height), (0, 0xFF, 0), 5)
                else:
                  cv2.line(input_frame, (roi, 0), (roi, height), (0, 0, 0xFF), 5)

                total_passed_person = total_passed_person + counter

                cascPath = "C:/Users/utilisateur/Desktop/people_counting_tensorflow/api/haarcascade_frontalface_alt2.xml"
                #cascPath = "./haarcascade_frontalface_default.xml"
                faceCascade = cv2.CascadeClassifier(cascPath)


                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(gray,
                                                    scaleFactor=1.1,
                                                    minNeighbors=5,
                                                    minSize=(60, 60),
                                                    flags=cv2.CASCADE_SCALE_IMAGE)
                
                faces_list=[]
                preds=[]
                for (x, y, w, h) in faces:
                    face_frame = input_frame[y:y+h,x:x+w]
                    face_frame = cv2.cvtColor(face_frame, cv2.COLOR_BGR2RGB)
                    face_frame = cv2.resize(face_frame, (224, 224))
                    face_frame = img_to_array(face_frame)
                    face_frame = np.expand_dims(face_frame, axis=0)
                    face_frame =  preprocess_input(face_frame)
                    faces_list.append(face_frame)
                    if len(faces_list)>0:
                        preds = mask_model.predict(faces_list)
                    for pred in preds:
                        (mask, withoutMask) = pred
                    label = "Mask" if mask > withoutMask else "No Mask"
                    color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
                    label = "{}: {:.2f}%".format(label, max(mask, withoutMask) * 100)
                    cv2.putText(frame, label, (x, y- 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)

                    cv2.rectangle(frame, (x, y), (x + w, y + h),color, 2)

                # insert information text to video frame
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(
                    input_frame,
                    'Detected Pedestrians: ' + str(total_passed_person),
                    (10, 35),
                    font,
                    0.8,
                    (0, 0xFF, 0xFF),
                    2,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    )

                cv2.putText(
                    input_frame,
                    'ROI Line',
                    (545, roi-10),
                    font,
                    0.6,
                    (0, 0, 0xFF),
                    2,
                    cv2.LINE_AA,
                    )

                cv2.putText(
                    input_frame,
                    'LAST PASSED PERSON INFO',
                    (11, 290),
                    font,
                    0.5,
                    (0xFF, 0xFF, 0xFF),
                    1,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    )

                cv2.putText(
                    input_frame,
                    '-Movement Direction: ' + str(direction),
                    (14, 302),
                    font,
                    0.4,
                    (0xFF, 0xFF, 0xFF),
                    1,
                    cv2.FONT_HERSHEY_COMPLEX_SMALL,
                    )
                
                cv2.putText(
                    input_frame,
                    '-Timestamp: ' + strftime('%Y-%m-%d %H:%M:%S'),
                    (14, 322),
                    font,
                    0.4,
                    (0xFF, 0xFF, 0xFF),
                    1,
                    cv2.FONT_HERSHEY_COMPLEX_SMALL,
                    )

                output_movie.write(input_frame)
                print ("writing frame")
                cv2.imshow('object counting',input_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                with open("pedestrian_measurement.json", mode='r', encoding='utf-8') as feedsjson:
                    feeds = json.load(feedsjson)

                if json_line != 'not_available':
                    with open("pedestrian_measurement.json", mode='w', encoding='utf-8') as feedsjson:
                        Timestamp = strftime('%Y-%m-%d %H:%M:%S')
                        entry = {'Timestamp': Timestamp, 'Movement Direction': direction, 'Masked': label}
                        feeds.append(entry)
                        json.dump(feeds, feedsjson)

            cap.release()
            cv2.destroyAllWindows()

def targeted_object_counting(input_video, detection_graph, category_index, is_color_recognition_enabled, targeted_object):

        # input video
        cap = cv2.VideoCapture(input_video)

        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        output_movie = cv2.VideoWriter('the_output.avi', fourcc, fps, (width, height))

        total_passed_person = 0
        speed = "waiting..."
        direction = "waiting..."
        size = "waiting..."
        color = "waiting..."
        the_result = "..."
        width_heigh_taken = True
        height = 0
        width = 0
        with detection_graph.as_default():
          with tf.compat.v1.Session(graph=detection_graph) as sess:
            # Definite input and output Tensors for detection_graph
            image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

            # Each box represents a part of the image where a particular object was detected.
            detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

            # Each score represent how level of confidence for each of the objects.
            # Score is shown on the result image, together with the class label.
            detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
            detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')

            # for all the frames that are extracted from input video
            while(cap.isOpened()):
                ret, frame = cap.read()                

                if not  ret:
                    print("end of the video file...")
                    break
                
                input_frame = frame

                # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                image_np_expanded = np.expand_dims(input_frame, axis=0)

                # Actual detection.
                (boxes, scores, classes, num) = sess.run(
                    [detection_boxes, detection_scores, detection_classes, num_detections],
                    feed_dict={image_tensor: image_np_expanded})

                # insert information text to video frame
                font = cv2.FONT_HERSHEY_SIMPLEX

                # Visualization of the results of a detection.        
                counter, json_line, the_result = vis_util.visualize_boxes_and_labels_on_image_array(cap.get(1),
                                                                                                      input_frame,
                                                                                                      1,
                                                                                                      is_color_recognition_enabled,
                                                                                                      np.squeeze(boxes),
                                                                                                      np.squeeze(classes).astype(np.int32),
                                                                                                      np.squeeze(scores),
                                                                                                      category_index,
                                                                                                      targeted_objects=targeted_object,
                                                                                                      use_normalized_coordinates=True,
                                                                                                      line_thickness=4)
                if(len(the_result) == 0):
                    cv2.putText(input_frame, "...", (10, 35), font, 0.8, (0,255,255),2,cv2.FONT_HERSHEY_SIMPLEX)                       
                else:
                    cv2.putText(input_frame, the_result, (10, 35), font, 0.8, (0,255,255),2,cv2.FONT_HERSHEY_SIMPLEX)
                
                #cv2.imshow('object counting',input_frame)

                output_movie.write(input_frame)
                print ("writing frame")

                if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

            cap.release()
            cv2.destroyAllWindows()