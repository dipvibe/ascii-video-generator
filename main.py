import cv2 

VIDEO_PATH= "input.mp4"
COLS= 100
CHAR_ASPECT=0.5

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

rows=int(COLS* (height/width)*CHAR_ASPECT)
print(f"ASCII grid: {COLS} x {rows} character")

frame_count=0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    small=cv2.resize(gray,(COLS,rows), interpolation=cv2.INTER_AREA)

    if frame_count==0:
       print(f"First frame shape : {frame.shape}")
       print(f"Grayscale shape   : {gray.shape}")
       print(f"Small shape       : {small.shape}")
       print(f"Brightness range  : {small.min()} to {small.max()}")

       preview = cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)
       cv2.imwrite("preview_grid.png", preview)
    frame_count+=1


print(f"Frames read  : {frame_count} (actual)")

cap.release()