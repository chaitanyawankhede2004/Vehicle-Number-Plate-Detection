import cv2
import numpy as np

img = cv2.imread() # ('''FilePath''')
if img is None:
    print("Error: Image not found.")
    exit()

size = 300
img = cv2.resize(img, (size, size))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img_norm = img_rgb / 255.0
c = 1 - img_norm[:, :, 0]
m = 1 - img_norm[:, :, 1]
y = 1 - img_norm[:, :, 2]
cmy_img = np.dstack((c, m, y))
cmy_img = (cmy_img * 255).astype(np.uint8)
cmy_bgr = cv2.cvtColor(cmy_img, cv2.COLOR_RGB2BGR)

def color_splash_channel(img, channel_idx):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    splash = np.zeros_like(img)
    splash[:, :, :] = gray[:, :, None]
    splash[:, :, channel_idx] = img[:, :, channel_idx]
    return splash

blue_splash = color_splash_channel(img, 0)
green_splash = color_splash_channel(img, 1)
red_splash = color_splash_channel(img, 2)

inverted = 255 - img

edges = cv2.Canny(img, 100, 200)
edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

def pixelate(image, pixel_size=10):
    h, w = image.shape[:2]
    temp = cv2.resize(image, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)

pixelated = pixelate(img, pixel_size=15)

def put_label(image, text):
    cv2.putText(image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 2, cv2.LINE_AA)

original_labeled = img.copy()
gray_labeled = gray_bgr.copy()
cmy_labeled = cmy_bgr.copy()
blue_labeled = blue_splash.copy()
green_labeled = green_splash.copy()
red_labeled = red_splash.copy()
inverted_labeled = inverted.copy()
edges_labeled = edges_bgr.copy()
pixelated_labeled = pixelated.copy()
put_label(original_labeled, 'Original')
put_label(gray_labeled, 'Grayscale')
put_label(cmy_labeled, 'CMY')
put_label(blue_labeled, 'Blue Splash')
put_label(green_labeled, 'Green Splash')
put_label(red_labeled, 'Red Splash')
put_label(inverted_labeled, 'Inverted')
put_label(edges_labeled, 'Edges')
put_label(pixelated_labeled, 'Pixelated')

black_img = np.zeros((size, size, 3), dtype=np.uint8)
row1 = np.hstack((original_labeled, gray_labeled, cmy_labeled, blue_labeled))
row2 = np.hstack((green_labeled, red_labeled, inverted_labeled, edges_labeled))
row3 = np.hstack((pixelated_labeled, black_img, black_img, black_img))

grid = np.vstack((row1, row2, row3))

cv2.imshow('DIP - Extended Views', grid)
cv2.waitKey(0)
cv2.destroyAllWindows()
