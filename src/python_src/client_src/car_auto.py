import time
import cv2
import numpy as np

import keyboard as key

from client_class import CarClient
from car_examples_ml import ex_ai_objects


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
        ignore_mask_color = 255
    # creating a polygon to focus only on the road in the picture
    rows, cols = image.shape[:2]
    bottom_left = [0, rows]
    middle_left = [0, 0.85*rows]
    top_left = [0.15*cols, int(rows * 0.5)]
    bottom_right = [cols, rows]
    middle_right = [cols, 0.85*rows]
    top_right = [0.85*cols, int(rows * 0.5)]

    vertices = np.array([[bottom_left, middle_left,top_left, top_right, middle_right ,bottom_right]], dtype=np.int32)
    # filling the polygon with white color and generating the final mask
    cv2.fillPoly(mask, vertices, ignore_mask_color)
    cv2.imshow('Mask', mask)
    masked_image = cv2.bitwise_and(image, mask)
    return masked_image


def average_slope_intercept(lines, image=None):
    """
    Find the slope and intercept of the left and right lanes of each image.
    Parameters:
        lines: output from Hough Transform
    """

    if lines is None or image is None:
        print("No lines detected or image is None.")
        return None, None

    left_lines = []  # (slope, intercept)
    left_weights = []  # (length,)
    right_lines = []  # (slope, intercept)
    right_weights = []  # (length,)
    horizontal_line = 0
    middle_x = image.shape[1]/2

    for line in lines:
        for x1, y1, x2, y2 in line:
            if x1 == x2:
                continue
            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - (slope * x1)
            length = np.sqrt(((y2 - y1) ** 2) + ((x2 - x1) ** 2))
            angle = abs(np.arctan(slope) * 180 / np.pi)
            if 10 <= angle <= 80:  # filter out very steep or very shallow lines
                bottom_x = x1 if y1 > y2 else x2
                dist_from_center = abs(bottom_x - middle_x)
                weight = length / ( 1 + dist_from_center**2)  # The bigger the line, and the closer to the center, the more weight it gets
                if slope < 0:
                    left_lines.append((slope, intercept))
                    left_weights.append((weight**2))
                else:
                    right_lines.append((slope, intercept))
                    right_weights.append((weight**2))
            elif angle <= 5:
                horizontal_line = horizontal_line + 1

    if horizontal_line > 2:
        # If we have more than 2 horizontal lines detected, we assume it's a finish line
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
    Returns:
        A tuple containing the start and end pixel points of the line.
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
    Create full length lines from the line's slope and intercept.
    Parameters:
        image: The input test image.
        lines: The output lines from Hough Transform.
    Returns:
        left_lane: A tuple containing the x and y points of the start and end of the left lane line.
        right_lane: A tuple containing the x and y points of the start and end of the right lane line.
        Both limited to the bottom of the image and 80% of the height.
    """
    left_line, right_line = average_slope_intercept(lines, image)
    if isinstance(left_line, int) and left_line == 1 and isinstance(right_line, int) and right_line == 1:
        # If we detected a horizontal line, return 1 for both lanes
        return 1, 1
    y1 = image.shape[0]
    y2 = y1 * 0.5
    #The line will be drawn from the bottom of the image to 80% of the height
    left_lane = pixel_points(y1, y2, left_line)
    right_lane = pixel_points(y1, y2, right_line)
    return left_lane, right_lane


def draw_lane_lines(image, lines, color=(255, 0, 0), thickness=15):
    """
    Draw lines onto the input image.
        Parameters:
            image: The input test image (video frame in our case).
            lines: The output lines from Hough Transform.
            color (Default = blue): Line color.
            thickness (Default = 15): Line thickness.
    """
    line_image = np.zeros_like(image)
    for line in lines:
        if line is not None:
            cv2.line(line_image, *line, color, thickness)
    return cv2.addWeighted(image, 0.8, line_image, 1.0, 0.0)


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
                                          threshold=40,
                                          minLineLength=70,
                                          maxLineGap=40)

            hough_lines_image = np.zeros_like(image)
            if hough_lines is not None:
                for line in hough_lines:
                    R = 0
                    G = 60
                    B = 220
                    for x1, y1, x2, y2 in line:
                        color = (B,G,R)  # Green color for lines
                        cv2.line(hough_lines_image, (x1, y1), (x2, y2), color, 2)

                cv2.imshow('Hough Lines', hough_lines_image)

            left_line, right_line = lane_lines(image, hough_lines)

            if isinstance(left_line, int) and left_line == 1 and isinstance(right_line, int) and right_line == 1:
                print("A horizontal line has been detected")
                for i in range(5): #Do 5 checks before stopping the car
                    ret, image = cap.read()  # Read the next frame
                    classes = ex_ai_objects(img_source=image, only_results=True)
                    time.sleep(0.2) # Wait for a second before sending the next command, and for the AI to process
                    if classes is not None and "person" in classes or "dog" in classes:
                        print("A person or dog has been detected after the horizotal line, keeping the car stopped.")
                        while "person" in classes or "dog" in classes:
                            ret, image = cap.read()  # Read the next frame
                            cv2.imshow("Current frame (with a person or a dog)", image)
                            cv2.waitKey(1)
                            if not ret:
                                print("Failed to capture image from camera.")
                                break
                            time.sleep(0.2) # Wait for a short time before checking again
                            print("A person or dog has been detected, keeping the car stopped.")
                            classes = ex_ai_objects(img_source=image, only_results=True)
                        print("The person has left the road, closing the program.")
                        break
                raise Exception("Lane detection has stopped the program. Horizontal line detected, without a dog or a person.")
            else:
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
                else: #Both lanes detected
                    x_left = min(left_line[0][0], left_line[1][0])
                    x_right = max(right_line[0][0], right_line[1][0])
                    image_width = image.shape[1]
                    print(x_right, x_left)
                    x_right_threshold = image_width * 1.04  # Adjusted threshold for right lane detection
                    x_left_threshold = -image_width * 0.04  # Adjusted threshold for left lane detection
                    if x_left < x_left_threshold:
                        #print("Left lane detected but too far left. Sending command to turn right.")
                        client.send_command("r", expected_response=False)
                        time.sleep(0.02)
                    elif x_right > x_right_threshold:
                        #print("Right lane detected but too far right. Sending command to turn left.")
                        client.send_command("l", expected_response=False)
                        time.sleep(0.02)
                    else:
                        #print("Both lanes detected and the car seems centered. Sending command to move forward.")
                        client.send_command("f", expected_response=False)
                        time.sleep(0.02)
            if key.is_pressed('c'):
                print("Automatic mode stopped by user.")
                client.send_command("STOP")
                break

    except Exception as e:
        print(f"There has been raised an exception: {e}")
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")
    finally:
        if client is not None:
            client.send_command("\n ", expected_response=False)
            time.sleep(0.5)
            client.send_command("END", expected_response=False)
        if commands_thread is not None:
            commands_thread.join()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    p = 50000
    car_road_circulate(p)
