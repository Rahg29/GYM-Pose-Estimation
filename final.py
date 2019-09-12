import os
import time
import math

import cv2
import numpy as np
import imutils

from server.helpers.estimator import TfPoseEstimator
from server.helpers.networks import get_graph_path, model_wh
from server.helpers.calculate_angle import calculate_angle

from IPython.display import clear_output
import time
import pprint
pp = pprint.PrettyPrinter(indent=14)
def pdictstr(d):
	return "{" + pp.pformat(DATA_PATHS)[14:]
	
def average_or_one(body_parts, idx1, idx2):
	if idx1 in body_parts.keys() and idx2 in body_parts.keys():
		return ((body_parts[idx1].x + body_parts[idx2].x)/2, (body_parts[idx1].y + body_parts[idx2].y)/2) 
	elif idx1 in body_parts.keys():
		return (body_parts[idx1].x, body_parts[idx1].y)
	elif idx2 in body_parts.keys():
		return (body_parts[idx2].x, body_parts[idx2].y)
	else: 
		return False
def angle_one(body_parts, idx):
	return (body_parts[idx].x, body_parts[idx].y)
	
def analyze_workout(body_parts, side, workout_func):
	
	return workout_func(body_parts)
def get_best_human(humans):
	# Get biggest human
	human = None
	largest_torso = 0
	for h in humans:
		try:
			# average shoulders
			shoulder = average_or_one(h.body_parts, 2, 5)
			# average hips
			hip = average_or_one(h.body_parts, 8, 11)
			print("Shoulder : ",shoulder)
			print("Hip :",hip)
			if shoulder and hip:#kya pata
				torso = (hip[0] - shoulder[0])**2 + (hip[1] - shoulder[1])**2
				torso = math.sqrt(torso)
				print("Torso : ",torso, "  Largest Torso : ",largest_torso)
				if torso > largest_torso:
					largest_torso = torso
					human = h
		except KeyError:
			pass
		
	return human

def draw_sizes(image, humans):
	imw, imh = image.shape[0], image.shape[1]
	human = None
	largest_torso = 0
	for h in humans:
		if h==None:
			continue
		else:
			try:
				# average shoulders
				shoulder = average_or_one(h.body_parts, 2, 5)
				# average hips
				hip = average_or_one(h.body_parts, 0, 1)
			
				
				if shoulder and hip:
					torso = (hip[0] - shoulder[0])**2 + (hip[1] - shoulder[1])**2
					torso = math.sqrt(torso)
					
					if torso > largest_torso:
						largest_torso = torso
						human = h
						cv2.putText(image,
									"SIZE: {}".format(torso),
									(int(shoulder[0]*imw-5), int(shoulder[1]*imh)),  cv2.FONT_HERSHEY_SIMPLEX, 0.5,
									(0, 0, 255), 2)
					else:
						cv2.putText(image,
									"SIZE: {}".format(torso),
									(int(shoulder[0*imw]-5), int(shoulder[1]*imh)),  cv2.FONT_HERSHEY_SIMPLEX, 0.5,
									(0, 255, 0), 2)
			except KeyError:
				pass
		
	return image

def squat(body_parts):
	"""
	Problems:
	- Squat depth
		Body Parts:
		   L/R Ankle
		   L/R Knee
		   L/R Hip
		Percent Deviation:
		   (OptimalAngle - AngleDetected)/OptimalAngle * 100
		Params:
			OptimalAngle = pi/2
			Threshold = TBD
	- Forward knee movement
		Body Parts:
			L/R Ankle
			L/R Knee
		Percent Deviation:
		   (X_ANKLE - X_KNEE)/TibiaLength * 100
		Params:
			OptimalDeviation = 0
			Threshold = TBD
	- 'Divebombing'
		Body Parts:
			L/R Shoulder
			L/R Hip
		Percent Deviation:
		   (X_SHOULDER - X_HIP)/TorsoLength * 100
		Params:
			OptimalDeviation = 0
			Threshold = TBD
	"""
	def squat_depth_angle(body_parts, optimal_angle, thresh):
		ankle = average_or_one(body_parts, 10, 13)
		knee = average_or_one(body_parts, 9, 12)
		hip = average_or_one(body_parts, 8, 11)
		try:
			if ankle and knee and hip:
				angle_detected = calculate_angle(ankle, knee, hip)
			else:
				 return -1
		except TypeError as e:
			raise e
		# calculate percent deviation
		deviation = (optimal_angle - angle_detected)/optimal_angle * 100
	
		return deviation
	return squat_depth_angle(body_parts, (math.pi)/2, 0.1)
def pullup(body_parts):
	"""
	Problems:
	->  Deviation in waist:
		Body Parts:
		   L/R Shoulder
		   L/R Hip
		   L/R Ankle
		Percent Deviation:
		   (OptimalAngle - AngleDetected)/OptimalAngle * 100
		Params:
			OptimalAngle = pi
			Threshold = 0.1
	"""
	
	def deviation_in_waist(body_parts, optimal_angle, thresh):
		# average shoulders
		shoulder = average_or_one(body_parts, 2, 5)
		# average hips
		elbow = average_or_one(body_parts, 8, 11)    
		# average ankles
		wrist = average_or_one(body_parts, 10, 13)
			# calculate angle
		angle_detected = calculate_angle(shoulder, elbow, wrist)
		print("angle :",angle_detected)
		deviation = (optimal_angle - angle_detected)/optimal_angle * 100
		return deviation
	
	
	return deviation_in_waist(body_parts, math.pi, 0.1)

def curl(body_parts, side):
	"""
	side - left or right, depending on user
	
	Problems:
	->  Horizontal deviation in humerous to upper body:
		Body parts:
			L//R Shoulder
			L//R Elbow
			L//R Hip
		Percent Deviation:
			(OptimalAngle - AngleDetected)/OptimalAngle * 100
		Params:
			OptimalAngle = 0
			Threshold = 0.1
	"""
	
	def horizontal_deviation_of_elbow(body_parts, side, optimal_angle, thresh):
		try:
			if side == 'L':
				shoulder = angle_one(body_parts, 5)
				elbow = angle_one(body_parts, 6)
				hip = angle_one(body_parts, 11)
			elif side == 'R':
				shoulder = angle_one(body_parts, 2)
				elbow = angle_one(body_parts, 3)
				hip = angle_one(body_parts, 8)
			else:
				return -1
		except KeyError as e:
			return -1
		
		try:
			if shoulder and hip and elbow:
				# calculate angle
				angle_detected = calculate_angle(shoulder, hip, elbow)
				print(angle_detected)
			else:
				return -1
		except TypeError as e:
			raise e
		
		# calculate percent deviation
		deviation = (optimal_angle - angle_detected)/optimal_angle * 100
		return deviation
		
		
		
	return horizontal_deviation_of_elbow(body_parts, side, 0, 0.1)

def pushup(body_parts):
	"""
	Problems:
	->  Deviation in waist:
		Body Parts:
		   L/R Shoulder
		   L/R Hip
		   L/R Ankle
		Percent Deviation:
		   (OptimalAngle - AngleDetected)/OptimalAngle * 100
		Params:
			OptimalAngle = pi
			Threshold = 0.1
	"""
	print("In Pushups")
	def deviation_in_waist(body_parts, optimal_angle, thresh):
		# average shoulders
		shoulder = average_or_one(body_parts, 2, 5)
		# average hips
		elbow = average_or_one(body_parts, 3, 6)    
		# average ankles
		hand = average_or_one(body_parts, 4, 7)
		print("Shoulder :",shoulder)
		print("elbow :",elbow)
		print("hand :",hand)
		try:
			if shoulder and hip and ankle:
				# calculate angle
				angle_detected = calculate_angle(shoulder, elbow, hand)
			else:
				return -1
		except TypeError as e:
			raise e
		# calculate percent deviation'server'
		deviation = (optimal_angle - angle_detected)/optimal_angle * 100
		return deviation


	return deviation_in_waist(body_parts, math.pi, 0.1)



# HARDCODE
def run(CAMERA_NUMBER,CURR_WORKOUT,PROCESSING_DIMS):
    
    if CURR_WORKOUT == 'pullup':
        CURR_WORKOUT = pullup
    # Paths
    BASE_DIR = os.path.abspath('.')
    GRAPH_PATH = os.path.join(BASE_DIR, 'models', 'cmu', 'graph_opt.pb')
    DATA_PATHS = {'base': os.path.join(BASE_DIR, 'data'),'sample': os.path.join(BASE_DIR, 'data', 'sample')}
    print("Base DIR : ",BASE_DIR)
    #print("Base DIR : ",BASE_DIR)
    #print("DATA_PATHS =", DATA_PATHS)
    print("Dimensions : ",PROCESSING_DIMS)
    print(type(PROCESSING_DIMS))
    
    # HARDCODE
    current_workout = CURR_WORKOUT
    repititions = 0

    # Initialize fps counter
    fps_time = 0

    # Load model
    model = TfPoseEstimator(GRAPH_PATH, target_size=PROCESSING_DIMS)

    # Initialize camera capture
    
    cam = cv2.VideoCapture(CAMERA_NUMBER)
    ret_val, image = cam.read()
    print(type(image))
    rows, cols = image.shape[0], image.shape[1]

    frame_width = int(cam.get(3))
    frame_height = int(cam.get(4))

    out = cv2.VideoWriter('outpy.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (frame_width,frame_height))


    # Read loop
    while True:
        # Read from camera
        ret_val, image = cam.read()

        # cv2.imshow('imag',image)
        # Predict poses
        if image is None:
            print("No Image")
            continue
        else:


            humans = model.inference(image)
            # cv2.imshow('im',image)
            time.sleep(5)
            if len(humans) == 0:
                print("No Humans")
                continue
            subject = get_best_human(humans)

            try:
            # Analyze workout
                print(subject)
                if subject==None:
                    continue
                else:
                    dev = analyze_workout(subject.body_parts,'L',current_workout)
                    print(dev)
                    if current_workout == squat:
                        if dev >140 and dev < 180 :
                            repititions = repititions +1

            except IndexError as e:
                image = imutils.rotate(image, -90)
                cv2.imshow('tf-pose-estimation result', image)
                fps_time = time.time()
                if cv2.waitKey(1) == 27:
                    break
                continue


            # Draw pose
            draw = TfPoseEstimator.draw_humans(image, [subject], imgcopy=False)
            # draw = imutils.rotate(draw, -90)

            # Draw angle
            cv2.putText(draw,
                    "Angle_of_ankle_knee_hip: {}".format(dev),
                    (10, 40),  cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)

            # Draw fps
            fps = 1.0 / (time.time() - fps_time)
            cv2.putText(draw,
                    "FPS: {}".format(fps),
                    (10, 10),  cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 0), 2)

            # Show image
            cv2.imshow('tf-pose-estimation result',image )
            out.write(image)

            print(repititions)
            # Restart FPS counter
            fps_time = time.time()
            if cv2.waitKey(1) == 27:
                break

    return repititions
    out.release()
    cam.release()
    cv2.destroyAllWindows()
