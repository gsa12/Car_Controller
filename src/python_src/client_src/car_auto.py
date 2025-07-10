import time
import cv2
import numpy as np
import threading

import keyboard as key

from networkx.algorithms.isomorphism.isomorph import is_isomorphic

from client_class import CarClient


# Functions for image processing and lane detection ---------------------------------------

def region_selection(image, ):
    """
    Determine and cut the region of interest in the input image.
    Parameters:
        image: we pass here the output from canny where we have
        identified edges in the frame
    """
    # create an array of the same size as of the input image
    mask = np.zeros_like(image)
    # if you pass an image with more then one channel
    if len(image.shape) > 2:
        print("Image has more than one channel, which is not accepted.")
        return None
    # our image only has one channel so it will go under "else"
    else:
        # color of the mask polygon (white)
        ignore_mask_color = 255
    # creating a polygon to focus only on the road in the picture (a rectangle with a little bit more than
    # half of the height of the image)
    rows, cols = image.shape[:2]
    bottom_left = [0, rows]
    middle_left = [0, 0.85*rows]
    top_left = [0.2*cols, int(rows * 0.4)]
    bottom_right = [cols, rows]
    middle_right = [cols, 0.85*rows]
    top_right = [0.8*cols, int(rows * 0.4)]

    vertices = np.array([[bottom_left, middle_left,top_left, top_right, middle_right ,bottom_right]], dtype=np.int32)
    # filling the polygon with white color and generating the final mask
    cv2.fillPoly(mask, vertices, ignore_mask_color)
    cv2.imshow('Mask', mask)
    # performing Bitwise AND on the input image and mask to get only the edges on the road
    masked_image = cv2.bitwise_and(image, mask)
    return masked_image


def average_slope_intercept(lines):
    """
    Find the slope and intercept of the left and right lanes of each image.
    Parameters:
        lines: output from Hough Transform
    """

    if lines is None:
        return None, None

    left_lines = []  # (slope, intercept)
    left_weights = []  # (length,)
    right_lines = []  # (slope, intercept)
    right_weights = []  # (length,)
    horizontal_line = 0

    for line in lines:
        for x1, y1, x2, y2 in line:
            if x1 == x2:
                continue
            # calculating slope of a line
            slope = (y2 - y1) / (x2 - x1)
            # calculating intercept of a line
            intercept = y1 - (slope * x1)
            # calculating length of a line
            length = np.sqrt(((y2 - y1) ** 2) + ((x2 - x1) ** 2))
            # slope of left lane is negative and for right lane slope is positive
            angle = abs(np.arctan(slope) * 180 / np.pi)
            if 5 <= angle <= 85:  # filter out very steep or very shallow lines
                if slope < 0:
                    left_lines.append((slope, intercept))
                    left_weights.append((length**3))
                else:
                    right_lines.append((slope, intercept))
                    right_weights.append((length**3))
            elif angle <= 5:
                horizontal_line = horizontal_line + 1

    if horizontal_line > 2:
        # If we have more than 2 horizontal lines detected, we assume it's a finish line
        print("Horizontal line detected, assuming finish line.")
        return 1, 1

    left_lane = np.dot(left_weights, left_lines) / np.sum(left_weights) if len(left_weights) > 0 else None
    right_lane = np.dot(right_weights, right_lines) / np.sum(right_weights) if len(right_weights) > 0 else None
    return left_lane, right_lane


def pixel_points(y1, y2, line):
    """
    Converts the slope and intercept of each line into pixel points.
        Parameters:
            y1: y-value of the line's starting point.
            y2: y-value of the line's end point.
            line: The slope and intercept of the line.
    """
    if line is None:
        return None
    slope, intercept = line
    if abs(slope) < 1e-5:
        # If slope is too small, return None to avoid division by zero
        return None

    x1 = int((y1 - intercept) / slope)
    x2 = int((y2 - intercept) / slope)
    y1 = int(y1)
    y2 = int(y2)
    return (x1, y1), (x2, y2)


def lane_lines(image, lines):
    """
    Create full length lines from pixel points.
        Parameters:
            image: The input test image.
            lines: The output lines from Hough Transform.
    """
    left_line, right_line = average_slope_intercept(lines)
    if isinstance(left_line, int) and left_line == 1 and isinstance(right_line, int) and right_line == 1:
        # If we detected a horizontal line, return 1 for both lanes
        return 1, 1
    y1 = image.shape[0]
    y2 = y1 * 0.6
    left_lane = pixel_points(y1, y2, left_line)
    right_lane = pixel_points(y1, y2, right_line)
    return left_lane, right_lane


def draw_lane_lines(image, lines, color=(255, 255, 255), thickness=20):
    """
    Draw lines onto the input image.
        Parameters:
            image: The input test image (video frame in our case).
            lines: The output lines from Hough Transform.
            color (Default = red): Line color.
            thickness (Default = 12): Line thickness.
    """
    line_image = np.zeros_like(image)
    for line in lines:
        if line is not None:
            cv2.line(line_image, *line, color, thickness)
    return cv2.addWeighted(image, 1.0, line_image, 20.0, 0.0)


# -------------------------------------------------------------------------------------

def car_road_circulate(p):
    """
        This function is used to control the car automatically in a given road.
        It is used to demonstrate the car's ability to navigate a road autonomously.
    """
    client = None
    commands_thread = None

    try:
        client = CarClient(port=p)
        cap = cv2.VideoCapture("http://10.42.0.1:5000/raw_stream")
        i = 0

        client.send_command("MANUAL", block_manual=False)

        while True:
            ret, image = cap.read()
            if not ret:
                print("Failed to capture image from camera.")
                while not ret:
                    ret, image = cap.read()
                    i = i + 1
                    if i == 10:
                        print("There have been too many missed frames, aborting.")
                        break
            #image = client.current_frame
            i = 0
            low_t = 75
            high_t = 140
            kernel_size = 15

            grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(grayscale, (kernel_size, kernel_size), 2)
            edges = cv2.Canny(blur, low_t, high_t)
            region = region_selection(edges)
            hough_lines = cv2.HoughLinesP(region,
                                          rho=1,
                                          theta=np.pi / 180,
                                          threshold=20,
                                          minLineLength=80,
                                          maxLineGap=60)

            hough_lines_image = np.zeros_like(image)
            if hough_lines is not None:
                for line in hough_lines:
                    R = 0
                    G = 60
                    B = 220
                    for x1, y1, x2, y2 in line:
                        color = (B,G,R)  # Green color for lines
                        cv2.line(hough_lines_image, (x1, y1), (x2, y2), color, 2)
                        length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                        print(length)

                cv2.imshow('Hough Lines', hough_lines_image)

            left_line, right_line = lane_lines(image, hough_lines)
            if isinstance(left_line, int) and left_line == 1 and isinstance(right_line, int) and right_line == 1:
                print("Horizontal line detected, assuming finish line.")
                break
            result = draw_lane_lines(image, (left_line, right_line))
            #cv2.imshow('Blurred image', blur)
            cv2.imshow('Lane Detection Canny in the desired Region', region)
            cv2.imshow('Lane Detection Result', result)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if not left_line and not right_line:
                print("No lane detected. No command sent.")
                time.sleep(0.05)
            elif left_line and not right_line:
                #print("Left lane detected. Sending command to turn right.")
                client.send_command("r", expected_response=False)
                time.sleep(0.02)
            elif right_line and not left_line:
                #print("Right lane detected. Sending command to turn left.")
                client.send_command("l", expected_response=False)
                time.sleep(0.02)
            else:
                #print("Both lanes detected. Sending command to move forward.")
                client.send_command("f", expected_response=False)
                time.sleep(0.02)
            if key.is_pressed('c'):
                print("Automatic mode stopped by user.")
                client.send_command("STOP")
                break

    except Exception as e:
        print(f"There has been an error: {e}")
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")
        cv2.destroyAllWindows()
    finally:
        if client:
            client.send_command("\n ", expected_response=False)
            time.sleep(0.5)
            client.send_command("END", expected_response=False)
            client.frame_updater(close=True)
            client.disconnect()
        if commands_thread:
            commands_thread.join()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    p = 50000
    car_road_circulate(p)
