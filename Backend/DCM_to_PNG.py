import pydicom
import matplotlib.pyplot as plt

ds = pydicom.dcmread("0002.DCM")
img = ds.pixel_array
slice_idx = 95
plt.imshow(img[slice_idx], cmap="gray")
plt.axis("off")
plt.show()