#!/usr/bin/env python

import roslib
import sys
import rospy
import cv2
import numpy as np
from std_msgs.msg import String
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray, Float64
from cv_bridge import CvBridge, CvBridgeError


class image_converter:

  # Defines publisher and subscriber
  def __init__(self):
    # initialize the node named image_processing
    rospy.init_node('image_processing', anonymous=True)
    # initialize a publisher to send images from camera2 to a topic named image_topic2
    self.image_pub2 = rospy.Publisher("image_topic2",Image, queue_size = 1)
    # initialize a subscriber to recieve messages rom a topic named /robot/camera1/image_raw and use callback function to recieve data
    self.image_sub2 = rospy.Subscriber("/camera2/robot/image_raw",Image,self.callback2)
    # initialize a publisher to send robot end-effector position
    self.end_effector_pub = rospy.Publisher("end_effector_pos",Float64, queue_size=10)
    # initialize a publisher to send desired trajectory
    self.target_pub = rospy.Publisher("target_pos",Float64, queue_size=10) 
    # initialize the bridge between openCV and ROS
    self.bridge = CvBridge()

  def detect_red(self,image):
      # Isolate the red colour in the image as a binary image
      mask = cv2.inRange(image, (0, 0, 100), (0, 0, 255))
      # This applies a dilate that makes the binary region larger (the more iterations the larger it becomes)
      kernel = np.ones((5, 5), np.uint8)
      mask = cv2.dilate(mask, kernel, iterations=3)
      # Obtain the moments of the binary image
      M = cv2.moments(mask)
      # Calculate pixel coordinates for the centre of the blob
      # Need to detect when there is no red circle using zero moments
      if (M['m00'] == 0):
        cx=0
        cy=0
        print("Red image NOT detected in image 2")
      else:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
      return np.array([cx, cy])

  # Detecting the centre of the green circle
  def detect_green(self,image):
      mask = cv2.inRange(image, (0, 100, 0), (0, 255, 0))
      kernel = np.ones((5, 5), np.uint8)
      mask = cv2.dilate(mask, kernel, iterations=3)
      M = cv2.moments(mask)
      # Need to detect when there is no circle using zero moments
      if (M['m00'] == 0):
        cx=0
        cy=0
        print("Green image NOT detected in image 2")
      else:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
      return np.array([cx, cy])

  # Detecting the centre of the blue circle
  def detect_blue(self,image):
      mask = cv2.inRange(image, (100, 0, 0), (255, 0, 0))
      kernel = np.ones((5, 5), np.uint8)
      mask = cv2.dilate(mask, kernel, iterations=3)
      M = cv2.moments(mask)
      # Need to detect when there is no circle using zero moments
      if (M['m00'] == 0):
        cx=0
        cy=0
        print("Blue image NOT detected in image 2")
      else:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
      return np.array([cx, cy])

  # Detecting the centre of the yellow circle
  def detect_yellow(self,image):
      mask = cv2.inRange(image, (0, 100, 100), (0, 255, 255))
      kernel = np.ones((5, 5), np.uint8)
      mask = cv2.dilate(mask, kernel, iterations=3)
      M = cv2.moments(mask)
      # Need to detect when there is no circle using zero moments
      if (M['m00'] == 10):
        cx=0
        cy=0
        print("Yellow image NOT detected in image 2")
      else:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
      return np.array([cx, cy])

      # Detecting the centre of the yellow circle
  def detect_orange(self,image):
      # Orange = R = 217, G = 118, B = 33
      mask = cv2.inRange(image, (0, 80, 100), (50, 140, 255))
      kernel = np.ones((5, 5), np.uint8)
      mask = cv2.dilate(mask, kernel, iterations=3)
      M = cv2.moments(mask)
      # Need to detect when there is no circle using zero moments
      if (M['m00'] == 0):
        cx=0
        cy=0
        print("Orange image NOT detected in image 1")
      else:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
      return np.array([cx, cy])
    
  # Calculate the conversion from pixel to meter
  def pixel2meter(self,image):
      # Obtain the centre of each coloured blob
      circle1Pos = self.detect_blue(image)
      circle2Pos = self.detect_green(image)
      # find the distance between two circles
      dist = np.sum((circle1Pos - circle2Pos)**2)
      return 3 / np.sqrt(dist)

        # Calculate the relevant joint angles from the image
  def detect_joint_angles(self,image):
    a = self.pixel2meter(image)
    print a
    # Obtain the centre of each coloured blob 
    center = a * self.detect_yellow(image)
    circle1Pos = a * self.detect_blue(image) 
    circle2Pos = a * self.detect_green(image) 
    circle3Pos = a * self.detect_red(image)
    # Solve using trigonometry
    ja1 = np.arctan2(center[0]- circle1Pos[0], center[1] - circle1Pos[1])
    ja2 = np.arctan2(circle1Pos[0]-circle2Pos[0], circle1Pos[1]-circle2Pos[1]) - ja1
    ja3 = np.arctan2(circle2Pos[0]-circle3Pos[0], circle2Pos[1]-circle3Pos[1]) - ja2 - ja1
    return np.array([ja1, ja2, ja3])

    # detect robot end-effector from the image
  def detect_end_effector(self,image):
    a = self.pixel2meter(image)
    endPos = a * (self.detect_yellow(image) - self.detect_red(image))
    return endPos

    # detect the target
  def detect_target(self,image):
    a = self.pixel2meter(image)
    targetPos = a * (self.detect_yellow(image) - self.detect_orange(image))
    return targetPos

  # Recieve data, process it, and publish
  def callback2(self,data):
    # Recieve the image
    try:
      self.cv_image2 = self.bridge.imgmsg_to_cv2(data, "bgr8")
    except CvBridgeError as e:
      print(e)

    # Perform image processing task (your code goes here)
    # in assigment publish target and end_effector pos
    self.end_effector_pos_all= self.detect_end_effector(self.cv_image2)
    self.end_effector_pos = self.end_effector_pos_all[0]
    self.target_pos= self.detect_target(self.cv_image2)
    print self.end_effector_pos


    # Uncomment if you want to save the image
    #cv2.imwrite('image2_copy.png', cv_image2)
    im2=cv2.imshow('window2', self.cv_image2)
    cv2.waitKey(1)

    # Publish the results
    try: 
      self.image_pub2.publish(self.bridge.cv2_to_imgmsg(self.cv_image2, "bgr8"))
      self.end_effector_pub.publish(self.end_effector_pos)
 #     self.target_pub.publish(self.target_pos)

    except CvBridgeError as e:
      print(e)

# call the class
def main(args):
  ic = image_converter()
  try:
    rospy.spin()
  except KeyboardInterrupt:
    print("Shutting down")
  cv2.destroyAllWindows()

# run the code if the node is called
if __name__ == '__main__':
    main(sys.argv)


