from pymavlink import mavutil
#from time import sleep
from goprocam import GoProCamera, constants
import subprocess
from Wifi import Wifi

KEY_FILE = "/home/PayloadController/Smart-Payload/key.priv"
SERIAL_DEV = "/dev/serial0"
SERIAL_BAUD_RATE = 57600
ENCRYPTED_PARTITION='/dev/mmcblk0p3'
LUKS_MOUNT_NAME='encryptfs'
LUKS_MOUNT_POINT='/home/PayloadController/encryptfs'

GOPRO_SSID = "Nicks Hero 7"
GOPRO_PASS = "hike7424"
WIFI_INT = "wlan0"

def main():
    
    try:
        wifi = Wifi(server_name=GOPRO_SSID,
                password=GOPRO_PASS,
                interface=WIFI_INT)
        wifi.run()
    except:
        raise

    try:
        key = RetrieveKey()
    except Exception as e:
        raise

    try:
        cam = GoProCamera.GoPro()
    except Exception as e:
        raise
    

    fc = mavutil.mavlink_connection(SERIAL_DEV, baud=SERIAL_BAUD_RATE)

    print("Waiting for heartbeat")
    fc.wait_heartbeat()

    print("Sending heartbeat")
    fc.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
                                                mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)


    recordFlag = True
    while(True):

        msg = fc.recv_match(type="SERVO_OUTPUT_RAW", blocking=True)

        if (msg.servo8_raw >= 1660):
                if (recordFlag):
                    print("Starting Video")
                    StartVideo(cam)
                    
                recordFlag = False
        else:
            if (recordFlag == False):
                print("Stopping Video")
                StopVideo(cam, key, "test")
                recordFlag = True

        #print(msg.servo8_raw)
        #TakePhoto(cam, "test.jpg")
    
    


# Takes photo, downloads to local directory, wipes from GoPro
def TakePhoto(cam, key, filename):
    cam.take_photo()

    UnlockFilestore(key)

    cam.downloadLastMedia(custom_filename=f"{LUKS_MOUNT_POINT}/{filename}.jpg")

    LockFilestore()

    cam.delete("last")

def StartVideo(cam):
    #1080p @ 60fps
    cam.video_settings("1080p", "60")

    cam.shoot_video()


def StopVideo(cam, key, filename):
    #Stop video
    cam.shutter(constants.stop)

    UnlockFilestore(key)

    cam.downloadLastMedia(custom_filename=f"{LUKS_MOUNT_POINT}/{filename}.mp4")
    print("Downloaded Media")

    LockFilestore()

    cam.delete("last")
    print("Deleted Media")


def UnlockFilestore(password):
    subprocess.run(['sudo', 'cryptsetup', 'luksOpen', ENCRYPTED_PARTITION, LUKS_MOUNT_NAME], input='LABERGE', encoding='ascii')

    subprocess.run(['sudo', 'mount', f'/dev/mapper/{LUKS_MOUNT_NAME}', LUKS_MOUNT_POINT])

    print("Unlocked Filestore")

def LockFilestore():

    subprocess.run(['sudo', 'umount', LUKS_MOUNT_POINT])
    
    subprocess.run(['sudo', 'cryptsetup', 'luksClose', f'/dev/mapper/{LUKS_MOUNT_NAME}'])

    print("Locked Filestore")

def RetrieveKey():

    with open(KEY_FILE) as f:
        key = f.read()
        f.close()
        

    subprocess.run(['shred', '-n 100', '-u', KEY_FILE])
    print("Shredded Key")
    
    return key




if __name__ == '__main__':
    main()