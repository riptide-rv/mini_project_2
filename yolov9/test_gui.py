from yolov9.test_utils import Counter

import argparse
import os
import platform
import sys
from pathlib import Path
import math
import torch
import numpy as np
from yolov9.deep_sort_pytorch.utils.parser import get_config
from yolov9.deep_sort_pytorch.deep_sort import DeepSort
from collections import deque
import socket
import cv2
import pickle

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLO root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode


class TrackerModel:
    def __init__(self, source):
        self.deepsort = self.initialize_deepsort()
        self.data_deque = {}
        self.className = self.classNames()
        self.c = Counter()  
        self.source = source
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = 'localhost'
        self.port = 8000
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.conn, self.addr = self.server_socket.accept()    
        print("Server is listening for incoming connections")
        self.run()
    def get_next_frame(self):
        return self.frame
    def initialize_deepsort(self):
        print("Initializing DeepSort")
        
        # Create the Deep SORT configuration object and load settings from the YAML file
        cfg_deep = get_config()
        cfg_deep.merge_from_file("yolov9/deep_sort_pytorch/configs/deep_sort.yaml")

        # Initialize the DeepSort tracker
        deepsort = DeepSort(cfg_deep.DEEPSORT.REID_CKPT,
                            max_dist=cfg_deep.DEEPSORT.MAX_DIST,
                            # min_confidence  parameter sets the minimum tracking confidence required for an object detection to be considered in the tracking process
                            min_confidence=cfg_deep.DEEPSORT.MIN_CONFIDENCE,
                            #nms_max_overlap specifies the maximum allowed overlap between bounding boxes during non-maximum suppression (NMS)
                            nms_max_overlap=cfg_deep.DEEPSORT.NMS_MAX_OVERLAP,
                            #max_iou_distance parameter defines the maximum intersection-over-union (IoU) distance between object detections
                            max_iou_distance=cfg_deep.DEEPSORT.MAX_IOU_DISTANCE,
                            # Max_age: If an object's tracking ID is lost (i.e., the object is no longer detected), this parameter determines how many frames the tracker should wait before assigning a new id
                            max_age=cfg_deep.DEEPSORT.MAX_AGE, n_init=cfg_deep.DEEPSORT.N_INIT,
                            #nn_budget: It sets the budget for the nearest-neighbor search.
                            nn_budget=cfg_deep.DEEPSORT.NN_BUDGET,
                            use_cuda=True
            )

        return deepsort

    def classNames(self):
        print("Getting Class Names")
        cocoClassNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
                    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
                    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
                    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
                    "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
                    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
                    "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
                    "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
                    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
                    "teddy bear", "hair drier", "toothbrush"
                    ]
        return cocoClassNames
    

    def colorLabels(self, classid):

        if classid == 0: #person
            color = (85, 45, 255)
        elif classid == 2: #car
            color = (222, 82, 175)
        elif classid == 3: #Motorbike
            color = (0, 204, 255)
        elif classid == 5: #Bus
            color = (0,149,255)
        else:
            color = (200, 100,0)
        return tuple(color)

    def draw_boxes(self, frame, bbox_xyxy, draw_trails, identities=None, categories=None,offset=(0,0)):
        height, width, _ = frame.shape
        # for key in list(data_deque):
        #   if key not in identities:
        #     data_deque.pop(key)

        for i, box in enumerate(bbox_xyxy):
            x1, y1, x2, y2 = [int(i) for i in box]
            x1 += offset[0]
            y1 += offset[0]
            x2 += offset[0]
            y2 += offset[0]
            self.c.increment()
            # print(f"Counter: {self.c.count}")
            #Find the center point of the bounding box
            center = int((x1+x2)/2), int((y1+y2)/2)
            cat = int(categories[i]) if categories is not None else 0
            color = self.colorLabels(cat)
            #color = [255,0,0]#compute_color_labels(cat)
            id = int(identities[i]) if identities is not  None else 0
            # create new buffer for new object
            if id not in self.data_deque:
                self.data_deque[id] = deque(maxlen= 64)
            self.data_deque[id].appendleft(center)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            name = self.className[cat]
            label = str(id) + ":" + name
            text_size = cv2.getTextSize(label, 0, fontScale=0.5, thickness=2)[0]
            c2 = x1 + text_size[0], y1 - text_size[1] - 3
            cv2.rectangle(frame, (x1, y1), c2, color, -1)
            cv2.putText(frame, label, (x1, y1 - 2), 0, 0.5, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)
            cv2.circle(frame,center, 2, (0,255,0), cv2.FILLED)
            if draw_trails:
                # draw trail
                for i in range(1, len(self.data_deque[id])):
                    # check if on buffer value is none
                    if self.data_deque[id][i - 1] is None or self.data_deque[id][i] is None:
                        continue
                    # generate dynamic thickness of trails
                    thickness = int(np.sqrt(64 / float(i + i)) * 1.5)
                    # draw trails
                    cv2.line(frame, self.data_deque[id][i - 1], self.data_deque[id][i], color, thickness)
            serialized_frame = pickle.dumps(frame)
            # Accept a client connection
            print(f"Connected to {self.addr}")
            # Send the serialized frame to the client
            self.conn.sendall(serialized_frame)  
            print("size of frame", sys.getsizeof(serialized_frame))
        return frame


    def run(self,
            weights=ROOT /'yolov9-c.pt',  # model path or triton URL
            source= 'yolov9/floor1.mp4',  # file/dir/URL/glob/screen/0(webcam)
            data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
            imgsz=(640, 640),  # inference size (height, width)
            conf_thres=0.25,  # confidence threshold
            iou_thres=0.45,  # NMS IOU threshold
            max_det=1000,  # maximum detections per image
            device=0,  # cuda device, i.e. 0 or 0,1,2,3 or cpu
            view_img=False,  # show results
            nosave=True,  # do not save images/videos
            classes=0,  # filter by class: --class 0, or --class 0 2 3
            agnostic_nms=False,  # class-agnostic NMS
            augment=False,  # augmented inference
            visualize=False,  # visualize features
            update=False,  # update all models
            project=ROOT / 'runs/detect',  # save results to project/name
            name='exp',  # save results to project/name
            exist_ok=False,  # existing project/name ok, do not increment
            half=False,  # use FP16 half-precision inference
            dnn=False,  # use OpenCV DNN for ONNX inference
            vid_stride=1,  # video frame-rate stride
            draw_trails = False,
    ):
        print("Running infernce on the model")
        print(f"weights: {weights}")
        print(f"source: {self.source}")
        print(f"data: {data}")
        print(f"imgsz: {imgsz}")
        print(f"conf_thres: {conf_thres}")
        print(f"iou_thres: {iou_thres}")
        print(f"max_det: {max_det}")
        print(f"device: {device}")
        print(f"view_img: {view_img}")
        print(f"nosave: {nosave}")
        print(f"classes: {classes}")
        print(f"agnostic_nms: {agnostic_nms}")
        print(f"augment: {augment}")
        print(f"visualize: {visualize}")
        print(f"update: {update}")
        print(f"project: {project}")
        print(f"name: {name}")
        print(f"exist_ok: {exist_ok}")
        print(f"half: {half}")
        print(f"dnn: {dnn}")
        print(f"vid_stride: {vid_stride}")
        print(f"draw_trails: {draw_trails}")
        # Initialize
        source = str(self.source)
        save_img = not nosave and not source.endswith('.txt')  # save inference images
        is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
        is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
        webcam = source.isnumeric() or source.endswith('.txt') or (is_url and not is_file)
        screenshot = source.lower().startswith('screen')
        if is_url and is_file:
            source = check_file(source)  # download

        # Directories
        save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
        save_dir.mkdir(parents=True, exist_ok=True)  # make dir

        # Load model
        device = select_device(device)
        model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
        stride, names, pt = model.stride, model.names, model.pt
        imgsz = check_img_size(imgsz, s=stride)  # check image size
        print(f"image_size  { imgsz }")

        # Dataloader
        bs = 1  # batch_size
        if webcam:
            view_img = check_imshow(warn=True)
            dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
            bs = len(dataset)
        elif screenshot:
            dataset = LoadScreenshots(source, img_size=imgsz, stride=stride, auto=pt)
        else:
            print("rtsp")
            dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
        vid_path, vid_writer = [None] * bs, [None] * bs

        # Run inference
        model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
        seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
        for path, im, im0s, vid_cap, s in dataset:
            with dt[0]:
                im = torch.from_numpy(im).to(model.device)
                im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
                im /= 255  # 0 - 255 to 0.0 - 1.0
                if len(im.shape) == 3:
                    im = im[None]  # expand for batch dim

            # Inference
            with dt[1]:
                visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
                pred = model(im, augment=augment, visualize=visualize)
                pred = pred[0][1]

            # NMS
            with dt[2]:
                pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

            # Second-stage classifier (optional)
            # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

            # Process predictions
            for i, det in enumerate(pred):  # per image
                seen += 1
                if webcam:  # batch_size >= 1
                    p, im0, frame = path[i], im0s[i].copy(), dataset.count
                    s += f'{i}: '
                else:
                    p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

                p = Path(p)  # to Path
                save_path = str(save_dir / p.name)  # im.jpg
                txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
                s += '%gx%g ' % im.shape[2:]  # print string
                gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                ims = im0.copy()
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()

                    # Print results
                    for c in det[:, 5].unique():
                        n = (det[:, 5] == c).sum()  # detections per class
                        s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string
                    xywh_bboxs = []
                    confs = []
                    oids = []
                    outputs = []
                    # Write results
                    for *xyxy, conf, cls in reversed(det):
                        x1, y1, x2, y2 = xyxy
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        #Find the Center Coordinates for each of the detected object
                        cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                        #Find the Width and Height of the Boundng box
                        bbox_width = abs(x1-x2)
                        bbox_height = abs(y1-y2)
                        xcycwh = [cx, cy, bbox_width, bbox_height]
                        xywh_bboxs.append(xcycwh)
                        conf = math.ceil(conf*100)/100
                        confs.append(conf)
                        classNameInt = int(cls)
                        oids.append(classNameInt)
                    xywhs = torch.tensor(xywh_bboxs)
                    confss = torch.tensor(confs)
                    outputs = self.deepsort.update(xywhs, confss, oids, ims)
                    if len(outputs) > 0:
                        bbox_xyxy = outputs[:, :4]
                        identities = outputs[:, -2]
                        object_id = outputs[:, -1]
                        self.draw_boxes(ims, bbox_xyxy, draw_trails, identities, object_id)

                # Stream results
                if view_img:
                    if platform.system() == 'Linux' and p not in windows:
                        windows.append(p)
                        cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                        cv2.resizeWindow(str(p), ims.shape[1], ims.shape[0])
                    cv2.imshow(str(p), ims)
                    cv2.waitKey(1)  # 1 millisecond
                # Save results (image with detections)
                if save_img:
                    if vid_path[i] != save_path:  # new video
                        vid_path[i] = save_path
                        if isinstance(vid_writer[i], cv2.VideoWriter):
                            vid_writer[i].release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream

                            fps, w, h = 15, ims.shape[1], ims.shape[0]
                        save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                        vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    vid_writer[i].write(ims)

            # Print time (inference-only)
            # LOGGER.info(f"{s}{'' if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")
        if update:
            strip_optimizer(weights[0])  # update model (to fix SourceChangeWarning)


    def parse_opt(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolo.pt', help='model path or triton URL')
        parser.add_argument('--source', type=str, default=ROOT / 'data/images', help='file/dir/URL/glob/screen/0(webcam)')
        parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
        parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
        parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
        parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
        parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
        parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
        parser.add_argument('--view-img', action='store_true', help='show results')
        parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
        parser.add_argument('--draw-trails', action='store_true', help='do not drawtrails')
        parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
        parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
        parser.add_argument('--augment', action='store_true', help='augmented inference')
        parser.add_argument('--visualize', action='store_true', help='visualize features')
        parser.add_argument('--update', action='store_true', help='update all models')
        parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
        parser.add_argument('--name', default='exp', help='save results to project/name')
        parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
        parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
        parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
        parser.add_argument('--vid-stride', type=int, default=1, help='video frame-rate stride')
        opt = parser.parse_args()
        opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
        print_args(vars(opt))
        return opt





  