import time
import cv2
import torch
import urllib.request
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO
from client_class import CarClient

model_type = "DPT_Large"     # MiDaS v3 - Large     (highest accuracy, slowest inference speed)
#model_type = "DPT_Hybrid"   # MiDaS v3 - Hybrid    (medium accuracy, medium inference speed)
#model_type = "MiDaS_small"  # MiDaS v2.1 - Small   (lowest accuracy, highest inference speed)
midas = torch.hub.load("intel-isl/MiDaS", model_type)
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
#device =  torch.device("cpu")
print("Using device:", device)
midas.to(device)
midas.eval()
midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")

if model_type == "DPT_Large" or model_type == "DPT_Hybrid":
    transform = midas_transforms.dpt_transform
else:
    transform = midas_transforms.small_transform


############################
yolo = YOLO('yolo11n.pt')


def __ex3(p):
    client = None
    try:
        client = CarClient(port=p)
        client.frame_updater()
        ex_ai_depth(client.current_frame)
    except Exception as e:
        print(f"There has been an error: {e}")
    finally:
        client.send_command("END")
        client.frame_updater(close=True)
        client.disconnect()
        cv2.destroyAllWindows()


def __ex4(p):
    client = None
    try:
        client = CarClient(port=p)
        running = True
        while running:
            client.frame_updater()
            if client.current_frame is not None:
                ret = ex_ai_objects(client.current_frame)
                # If ex_ai_objects returns None (e.g., user pressed 'q'), exit the loop
                if ret == -1:
                    running = False
            else:
                print("No frame available")
                time.sleep(0.1)  # Prevent CPU overuse when no frames are available
    except Exception as e:
        print(f"There has been an error: {e}")
    finally:
        if client:
            client.send_command("END")
            client.frame_updater(close=True)
            client.disconnect()
        cv2.destroyAllWindows()

##------------- Functions using ML models ------------------##

def ex_ai_depth(img_provided=None):
    """
        This function tests the AI capabilities of the car.
        It uses a pre-trained model to predict depth from an image.
    """
    if img_provided is None:
        url, filename = ("https://github.com/pytorch/hub/raw/master/images/dog.jpg", "dog.jpg")
        urllib.request.urlretrieve(url, filename)
        img = cv2.imread(filename)
    elif isinstance(img_provided, str):
        img = cv2.imread(img_provided)
    elif isinstance(img_provided, np.ndarray):
        img = img_provided
    else:
        raise ValueError("img_provided must be a file path, a NumPy array, or None.")

    start = time.time()
    input_batch = transform(img).to(device)

    with torch.no_grad():
        prediction = midas(input_batch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()
    end = time.time() - start
    print(f"Prediction took {end:.2f} seconds")
    output = prediction.cpu().numpy()

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB for correct display
    # Display both original image and depth map
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.imshow(img)
    plt.title('Original Image')
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.imshow(output, cmap='plasma')  # Using a colormap for better depth visualization
    plt.title('Depth Map')
    plt.axis('off')

    plt.tight_layout()
    plt.show()  # This will actually display the images


def ex_ai_objects(img_provided=None):
    """
        This function tests the AI capabilities of the car.
        It uses a pre-trained model to detect objects in an image.
    """

    # Define videoCap properly
    videoCap = None
    was_img_provided = False

    try:
        # Load the video capture
        if img_provided is None:
            videoCap = cv2.VideoCapture("http://10.42.0.1:5000/raw_stream")
            ret, frame = videoCap.read()
            if not ret:
                print("Failed to capture video stream.")
                return None
        else:
            frame = img_provided
            was_img_provided = True

        # Function to get class colors
        def getColours(cls_num):
            base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
            color_index = cls_num % len(base_colors)
            increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
            color = [base_colors[color_index][i] + increments[color_index][i] *
                     (cls_num // len(base_colors)) % 256 for i in range(3)]
            return tuple(color)

        results = yolo.track(frame, stream=True)

        for result in results:
            # get the classes names
            classes_names = result.names

            # iterate over each box
            for box in result.boxes:
                # check if confidence is greater than 50 percent
                if box.conf[0] > 0.5:
                    # get coordinates
                    [x1, y1, x2, y2] = box.xyxy[0]
                    # convert to int
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    # get the class
                    cls = int(box.cls[0])

                    # get the class name
                    class_name = classes_names[cls]

                    # get the respective colour
                    colour = getColours(cls)

                    # draw the rectangle
                    cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)

                    # put the class name and confidence on the image
                    cv2.putText(frame, f'{classes_names[int(box.cls[0])]} {box.conf[0]:.2f}', (x1, y1),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, colour, 2)

        # show the image
        cv2.imshow('frame', frame)

        # wait for key press with timeout
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return -1

    finally:
        # Always release the video capture if it was created
        if videoCap is not None and not was_img_provided:
            videoCap.release()


if __name__ == "__main__":
    p = 50002
    # ex_ai_depth()  # You can pass a file path or a NumPy array as an argument if needed
    # ex_ai_tests("path_to_your_image.jpg")  # Example of passing a file path
    # ex_ai_tests(np.random.rand(480, 640, 3))  # Example of passing a random NumPy array
    # ex_ai_objects()  # You can pass a file path or a NumPy array as an argument if needed
    # __ex3(p)
    __ex4(p)