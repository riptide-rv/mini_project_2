import cv2

def get_video_details(video_path):
    

    cap = cv2.VideoCapture(int(video_path) if video_path.isdigit() else str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Unable to open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()

    return fps, width, height