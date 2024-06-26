import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
# import seaborn as sns
import matplotlib.pyplot as plt


#streamlit run d:/pyfile/priceChecker/1_Home.py
st.set_page_config(
    page_title="Chicken Eggonomics",
    page_icon=":chicken:",
    layout="wide")
# w = 500
# h = 350



st.title(":chicken: Chicken Eggonomics :egg::egg::egg:")
st.write("*A Data Science Project by Mirim.*")
st.write("*Price Catcher for Chicken and Eggs products (Barangan Segar) across Malaysia.*")
url = "https://open.dosm.gov.my/data-catalogue"
st.write("Link to [Open Data Catalogue](%s) by DOSM." % url)
# tab1, tab2 = st.tabs(["Region", "Rep Office"])

# https://wearesutd.sutd.edu.sg/wp-content/uploads/2018/08/Chicken-Art-Background-Wallpaper-19893.jpg
page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
background-image: url("https://static.vecteezy.com/system/resources/previews/007/740/353/original/seamless-pattern-of-fried-eggs-on-gray-background-minimalist-style-wallpaper-vector.jpg");
background-size: cover;
background-position: center center;
background-repeat: no-repeat;
background-attachment: local;
}}
[data-testid="stHeader"] {{
background: rgba(0,0,0,0);
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

st.subheader('List of Items Tracked')

lookup_item = pd.read_csv("./data/lookup_item.csv")
lookup_item['item_unit'] = lookup_item['item'].astype(str) + " (" + lookup_item['unit'].astype(str) + ")"
lookup_item = lookup_item.sort_values(by=['item_unit']).reset_index(drop=True)
lookup_item = lookup_item.drop(columns=['item_group','item','unit'])
st.write(lookup_item)