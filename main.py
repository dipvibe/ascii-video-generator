import cv2 

VIDEO_PATH= "input.mp4"

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print(f"Error: could not open {VIDEO_PATH}")
    exit()

fps= cap.get(cv2.CAP_PROP_FPS)
width= int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height= int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"FPS          : {fps}")
print(f"Resolution   : {width} x {height}")
print(f"Frame count  : {total_frames} (reported)")
print(f"Duration     : {total_frames / fps:.2f} seconds")

frame_count=0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    if frame_count==0:
        print(f"first frame shape:{frame.shape}")

    frame_count+=1


print(f"Frames read  : {frame_count} (actual)")

cap.release()