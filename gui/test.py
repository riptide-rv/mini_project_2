import tkinter as tk
from PIL import Image, ImageTk
import cv2
import threading

from yolov9.test_gui import TrackerModel
from yolov9.get_video_details import get_video_details
import socket
import pickle

class GUIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GUI Application")
        self.create_widgets()
        self.tracker_model = None
        self.frame_updater_thread = None
        self.frame_queue = None
        self.server_socket = None
        self.client_connection = None

    def create_widgets(self):
        # Create the "Source" label and entry field
        source_label = tk.Label(self, text="Source:")
        source_label.pack()
        self.source_entry = tk.Entry(self)
        self.source_entry.pack()

        # Create the "Run" button
        run_button = tk.Button(self, text="Run", command=self.run_function)
        run_button.pack()

        # Create a canvas to display the video
        self.canvas = tk.Canvas(self, width=640, height=480)
        self.canvas.pack()

    def run_function(self):
        source = self.source_entry.get()
        fps, width, height = get_video_details(source)
        print(f"FPS: {fps}, Width: {width}, Height: {height}")

        # Create a queue to share frames between threads
        

        # Create and start the object creation thread
        object_creation_thread = threading.Thread(target=self.create_tracker_model, args=(source,))
        object_creation_thread.start()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = 'localhost'
        port = 8000
        self.client_socket.connect((host, port))
        print("Connected to server")
        self.receive_frames()

    def receive_frames(self):
        while True:
            # Receive the serialized frame from the client
            serialized_frame = b''
            
            chunk = self.client_socket.recv(1229958)  # Adjust buffer size as needed
            print("is chunk")
            if not chunk:
                print("No chunk")
            
            serialized_frame += chunk

            if serialized_frame:
                # Deserialize the frame
                frame = pickle.loads(serialized_frame)
                print(frame)
                # Update the GUI with the received frame
                self.update_video_frame(frame)
            

        # Clean up the connection
        self.client_connection.close()

    def update_video_frame(self, frame):
        cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(cv2_image)
        tk_image = ImageTk.PhotoImage(pil_image)

        # Update the canvas with the new frame
        self.canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
        self.canvas.image = tk_image

    def create_tracker_model(self, source):
        self.tracker_model = TrackerModel(source)
        

  