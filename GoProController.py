from pymavlink import mavutil
#from time import sleep
from goprocam import GoProCamera, constants
import subprocess

KEY_FILE = "/home/PayloadController/Smart-Payload/key.priv"
SERIAL_DEV = "/dev/serial0"
SERIAL_BAUD_RATE = 57600
ENCRYPTED_PARTITION='/dev/mmcblk0p3'
LUKS_MOUNT_NAME='encryptfs'
LUKS_MOUNT_POINT='/home/PayloadController/encryptfs'



def main():
    
    try:
        key = RetrieveKey()
    except Exception as e:
        raise(e, "Failed to read KEY_FILE from filesystem")

    try:
        cam = GoProCamera.GoPro()
    except Exception as e:
        raise(e, "Failed to connect to camera. Is the controller on the correct WiFi network?")
    

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
                    print("Taking Photo")
                    TakePhoto(cam, key, "test")
                    
                recordFlag = False
        else:
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

def UnlockFilestore(password):
    result = subprocess.run(['sudo', 'cryptsetup', 'luksOpen', ENCRYPTED_PARTITION, LUKS_MOUNT_NAME], input='LABERGE', encoding='ascii')
    print(result.stdout)

    result = subprocess.run(['sudo', 'mount', f'/dev/mapper/{LUKS_MOUNT_NAME}', LUKS_MOUNT_POINT])
    print(result.stdout)


def LockFilestore():

    result = subprocess.run(['sudo', 'umount', LUKS_MOUNT_POINT])
    print(result.stdout)

    result = subprocess.run(['sudo', 'cryptsetup', 'luksClose', f'/dev/mapper/{LUKS_MOUNT_NAME}'])
    print(result.stdout)


def RetrieveKey():

    with open(KEY_FILE) as f:
        key = f.read()
        f.close()
        

    result = subprocess.run(['shred', '-n 100', '-u', KEY_FILE])
    print(result.stdout)
    
    return key


if __name__ == '__main__':
    main()