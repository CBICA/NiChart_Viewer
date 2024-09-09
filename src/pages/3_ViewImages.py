import streamlit as st
import pandas as pd
import pydeck as pdk
from urllib.error import URLError
import nibabel as nib
import numpy as np

st.set_page_config(page_title="Nifti Viewer Demo", page_icon="🌍")

st.markdown("# Nifti Viewer Demo")
st.sidebar.header("Nifti Viewer Demo")
st.write(
    """This demo shows how to display Nifti images"""
)

st.write('Hello')

# FIXME: Input data is hardcoded here for now
f1 = "../examples/test_input3/IXI002-Guys-0828_T1.nii.gz"
f2 = "../examples/test_input3/IXI002-Guys-0828_T1_DLMUSE.nii.gz"
sel_roi = 51
mask_color = (0, 255, 0)  # RGB format


nii1 = nib.load(f1)
nii2 = nib.load(f2)

img1 = nii1.get_fdata()
img2 = nii2.get_fdata()

img1 = np.rot90(img1)
img2 = np.rot90(img2)

img1 = np.stack((img1,)*3, axis=-1)
img1[img2 == sel_roi] = mask_color

img1 = img1 / img1.max()

# Create a slider to select the slice index
slice_index = st.slider("Select Slice Index", 0, img1.shape[2] - 1, value=95)

# Extract the slice and display it
st.image(img1[:, :, slice_index], width=800)
