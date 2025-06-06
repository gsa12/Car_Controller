import time
import cv2
import torch
import urllib.request
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO

#model_type = "DPT_Large"     # MiDaS v3 - Large     (highest accuracy, slowest inference speed)
#model_type = "DPT_Hybrid"   # MiDaS v3 - Hybrid    (medium accuracy, medium inference speed)
model_type = "MiDaS_small"  # MiDaS v2.1 - Small   (lowest accuracy, highest inference speed)
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


def ai_depth(img_provided=None):
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


def ai_objects(img_provided=None):
        """
            This function tests the AI capabilities of the car.
            It uses a pre-trained model to detect objects in an image."""

        # Load the video capture
        videoCap = cv2.VideoCapture("http://10.42.0.1:5000/raw_stream")

        # Function to get class colors
        def getColours(cls_num):
            base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
            color_index = cls_num % len(base_colors)
            increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
            color = [base_colors[color_index][i] + increments[color_index][i] *
                     (cls_num // len(base_colors)) % 256 for i in range(3)]
            return tuple(color)

        while True:
            ret, frame = videoCap.read()
            if not ret:
                continue
            results = yolo.track(frame, stream=True)

            for result in results:
                # get the classes names
                classes_names = result.names

                # iterate over each box
                for box in result.boxes:
                    # check if confidence is greater than 40 percent
                    if box.conf[0] > 0.4:
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

            # break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # release the video capture and destroy all windows
        videoCap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    #ai_depth()  # You can pass a file path or a NumPy array as an argument if needed
    # ai_tests("path_to_your_image.jpg")  # Example of passing a file path
    # ai_tests(np.random.rand(480, 640, 3))  # Example of passing a random NumPy array
    ai_objects()  # You can pass a file path or a NumPy array as an argument if needed