import subprocess
import os
if __name__ == "__main__":
    command =[
            "python", "detect_dual_tracker.py",
            "--weights", "yolov9-c.pt",
            "--source", "floor1.mp4",
            "--classes", "0",
            "--view-img",
            "--draw-trails"
        ]
    print(os.environ)

    my_env = os.environ
    my_env["PATH"] = "TORCH:D:\\Studies\\Projects\\mini_project_2\\.myenv2\\Scripts\\torch\\bin" + my_env["PATH"]
    
    process = subprocess.Popen(command,env=my_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        print(f"Error: {error.decode()}")