from pymavlink import mavutil
#from time import sleep
from goprocam import GoProCamera, constants
import time
import sys
import os


def main():
    
    fc = mavutil.mavlink_connection("/dev/serial0", baud=57600)

    print("Waiting for heartbeat")
    fc.wait_heartbeat()

    print("Sending heartbeat")
    fc.mav.heartbeat_send(30, 8, 100, 0, 0)
    
    while(True):
        #print(fc.recv_match(blocking=True))
        continue

    try:
        cam = GoProCamera.GoPro()
    except Exception as e:
        raise(e, "Failed to connect to camera. Is the controller on the correct WiFi network?")

    TakePhoto(cam, "test.jpg")

# Takes photo, downloads to local directory, wipes from GoPro
def TakePhoto(cam, filename):
    cam.take_photo()
    cam.downloadLastMedia(custom_filename=os.getcwd()+f"/{filename}")
    cam.delete("last")

if __name__ == '__main__':
    main()