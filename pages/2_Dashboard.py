import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
# import seaborn as sns
import matplotlib.pyplot as plt
import dateutil.relativedelta
import openpyxl
st.set_page_config(
    page_title="Chicken Eggonomics",
    page_icon=":chicken:",
    layout="wide")
st.title(":chicken: Chicken Eggonomics :egg::egg::egg:")

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

#@st.cache_data
def premise_lookup():
    ## premise lookup codes
    premise_url = 'https://storage.data.gov.my/pricecatcher/lookup_premise.parquet'
    
    lookup_premise = pd.read_parquet(premise_url)
    if 'date' in lookup_premise.columns: lookup_premise['date'] = pd.to_datetime(lookup_premise['date'])
    # lookup_premise = pd.read_csv("./data/lookup_premise.csv")
    lookup_premise = lookup_premise.dropna()
    premise_type_list = ['Borong', 'Hypermarket', 'Kedai Runcit', 'Pasar Basah', 'Pasar Basah ', 'Pasar Mini', 'Pasar Raya / Supermarket']
    lookup_premise = lookup_premise.loc[lookup_premise['premise_type'].isin(premise_type_list)]
    list_state = sorted(lookup_premise['state'].unique())
    
    # lookup item
    # item_url = 'https://storage.data.gov.my/pricecatcher/lookup_item.parquet'
    # item_df = pd.read_parquet(item_url)
    # if 'date' in item_df.columns: item_df['date'] = pd.to_datetime(item_df['date'])
    # item_df = item_df.dropna()
    
    # only takes telur and ayam products
    # lookup_item = item_df.loc[(item_df['item_category'].isin(['TELUR','AYAM'])) & (item_df['item_group'] == 'BARANGAN SEGAR')]
    lookup_item = pd.read_csv("./data/lookup_item.csv")
    
    lookup_item['item_unit'] = lookup_item['item'].astype(str) + " (" + lookup_item['unit'].astype(str) + ")"
    lookup_item = lookup_item.sort_values(by=['item_unit'])
    list_item = lookup_item['item_unit'].unique()
    return list_state, list_item, lookup_premise, lookup_item
    
list_state, list_item, lookup_premise, lookup_item = premise_lookup()

# date settings
earliest_month = pd.Timestamp.now().strftime("%Y-01-01")
current_month = pd.Timestamp.now().strftime("%Y-%m")
last_month = (pd.Timestamp.now() - dateutil.relativedelta.relativedelta(months=1)).strftime("%Y-%m")
month_list = pd.date_range(start=earliest_month, end=current_month, freq='MS').strftime("%Y-%m")
current_week = pd.Timestamp.now().isocalendar().week

@st.cache_data
def extract_data(list_of_month):
    extracted_df = pd.DataFrame()

    for ym in month_list:
        # extract month
        URL_DATA = f'https://storage.data.gov.my/pricecatcher/pricecatcher_{ym}.parquet'
        df = pd.read_parquet(URL_DATA)
        if 'date' in df.columns: df['date'] = pd.to_datetime(df['date'])

        # merge with item lookup df and create week columns
        temp = df.merge(lookup_item, how='inner',on='item_code')
        temp['week'] = temp['date'].dt.isocalendar().week
        temp['week_date'] = temp['date'].dt.to_period('W').apply(lambda r: r.start_time)
        temp['year_month'] = temp['date'].dt.strftime("%Y-%m")
        temp = temp.drop(columns=["item_category","item_group","date"])
        extracted_df = pd.concat([extracted_df, temp])

    extracted_df = extracted_df.groupby(by=["week_date","week","year_month", "item","unit","item_unit","premise_code","item_code"]).agg('mean').reset_index()
    extracted_df = extracted_df.merge(lookup_premise,how='inner',on='premise_code')   
    extracted_df=extracted_df.drop(columns=["premise_code","item_code","item","unit","address","premise_type"])
    extracted_df["price"] = extracted_df["price"].round(2)
    return extracted_df


agg_data = extract_data(month_list)
last_year_agg_data = pd.read_excel("data/ayam_telur_price_2023.xlsx")

# curyearweekly = agg_data(rawdata, unit='weekly')
# curyearmonthly = agg_data(rawdata, unit='monthly')

with st.sidebar:
    st.subheader("Filters")
    select_item = st.selectbox(
        "Item",
        list_item
    )
    select_state = st.selectbox(
    "State",
    list_state
    )
    # form = st.form("filter_form",border=False)

    list_district = sorted(lookup_premise.loc[lookup_premise['state']==select_state]['district'].unique())
    select_district = st.multiselect(
    "District",
    list_district,
    placeholder='All'
    )

    list_premise = sorted(lookup_premise.loc[(lookup_premise['state']==select_state) 
                                             & (lookup_premise['district'].isin(select_district))
                                            ]['premise'].unique())
    select_premise= st.multiselect(
    "Premise",
    list_premise,
    placeholder='All'
    )
    # form_search = form.form_submit_button("Search")


with st.container(height=250,border=True):
    st.markdown(":blue-background[**Filtered Options**]")
    # col1, col2 = st.columns(2)
    # with col1:
    st.write(f"**Item:** {select_item}")
    st.write(f"**State:** {select_state}")

    if len(select_district) < 1:
        st.write(f"**Districts:** All districts")
    else:
        districts = ', '.join(select_district)
        st.write(f"**Districts:** {districts}")

    if len(select_premise) < 1:
        st.write(f"**Premises:** All premises")
    else:
        premises = ', '.join(select_premise)
        st.write(f"**Premises:** {premises}")
    # with col2:
        # st.image("./data/ayam_standard.png",width=100,use_column_width='auto')

def filterData(df, item, state, district,premise):
    availability = 1
    if len(district) > 0 and len(premise) == 0:
        tmp = df.loc[(df['item_unit'] == item) 
                & (df['state'] == state) & (df['district'].isin(district))]
    elif len(district) > 0 and len(premise) > 0:
        tmp = df.loc[(df['item_unit'] == item) 
            & (df['state'] == state) & (df['district'].isin(district))
            & (df['premise'].isin(premise))]
    elif len(district) == 0:
        tmp = df.loc[(df['item_unit'] == item) & (df['state'] == state)]
        
    if len(tmp) == 0:
        availability = 0
        
    return tmp, availability

def filterDataRank(df, item, state, district, rank='top'):
    availability = 1
    if len(district) > 0:
        tmp = df.loc[(df['item_unit'] == item) 
                & (df['state'] == state) & (df['district'].isin(district))]
    elif len(district) == 0:
        tmp = df.loc[(df['item_unit'] == item) & (df['state'] == state)]
        
    if len(tmp) == 0:
        availability = 0
    tmp = tmp.loc[tmp['week']==current_week]
    if rank == 'top':
        tmp = tmp.sort_values(by=['price'], ascending=True).head(15)
    elif rank =='bottom':
        tmp = tmp.sort_values(by=['price'], ascending=False).head(15)

    tmp = tmp[['premise','price','state','district']].reset_index(drop=True)
    return tmp



filtered_data, status = filterData(agg_data, select_item, select_state, select_district,select_premise)
filtered_data_ly, status_ly = filterData(last_year_agg_data, select_item, select_state, select_district,select_premise)

st.subheader("Current Average Price Summary")
colweek, colmonth, colyear = st.columns(3)

# week column
colweek.subheader('Week')
if status == 1:
    currentWeekPrice = round(filtered_data.loc[filtered_data['week']==current_week]['price'].mean(),2)
    lastWeekPrice = round(filtered_data.loc[filtered_data['week']==current_week-1]['price'].mean(),2)
    wowprice = round(currentWeekPrice - lastWeekPrice,2)
    wow = round(wowprice/lastWeekPrice * 100,2)
    colweek.write(f'This week: **RM{currentWeekPrice}**')
    colweek.write(f'Last week: **RM{lastWeekPrice}**')
    if wow > 0:
        colweek.write(f'Increase by :red[**RM{wowprice} ({wow}%)**]')
    else:
        colweek.write(f'Decrease by :green[**RM{wowprice} ({wow}%)**]')
else:
    colweek.write('This item is not sold in this location.')
    currentWeekPrice = 0
    lastWeekPrice = 0

# month column
colmonth.subheader('Month')
if status == 1:
    currentMonthPrice = round(filtered_data.loc[filtered_data['year_month']==current_month]['price'].mean(),2)
    lastMonthPrice = round(filtered_data.loc[filtered_data['year_month']==last_month]['price'].mean(),2)
    momprice = round(currentMonthPrice - lastMonthPrice,2)
    mom = round(momprice/lastMonthPrice * 100,2)
    colmonth.write(f'This month: **RM{currentMonthPrice}**')
    colmonth.write(f'Last month: **RM{lastMonthPrice}**')
    if mom > 0:
        colmonth.write(f'Increase by :red[**RM{momprice} ({mom}%)**]')
    else:
        colmonth.write(f'Decrease by :green[**RM{momprice} ({mom}%)**]')
else:
    colmonth.write('This item is not sold in this location.')
    currentMonthPrice = 0
    lastMonthPrice = 0

# year column
colyear.subheader('Year')
if status == 1 and status_ly == 1:
    currentYearPrice = round(filtered_data['price'].mean(),2)
    lastYearPrice = round(filtered_data_ly['price'].mean(),2)
    yoyprice = round(currentYearPrice - lastYearPrice,2)
    yoy = round(yoyprice/lastYearPrice * 100,2)
    colyear.write(f'This year: **RM{currentYearPrice}**')
    colyear.write(f'Last year: **RM{lastYearPrice}**')
    if yoy > 0:
        colyear.write(f'Increase by :red[**RM{yoyprice} ({yoy}%)**]')
    else:
        colyear.write(f'Decrease by :green[**RM{yoyprice} ({yoy}%)**]')
else:
    colyear.write('This item is not sold in this location.')
    currentYearPrice = 0
    lastYearPrice = 0

st.subheader("Top 15 Cheapest Premises This Week")
st.write(filterDataRank(agg_data, select_item, select_state, select_district, rank='top'))

# st.subheader("Top 10 Expensive Premises This Week")
# st.write(filterDataRank(agg_data, select_item, select_state, select_district, rank='bottom'))

# # Pie chart, where the slices will be ordered and plotted counter-clockwise:
# # labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
# sizes = [wowprice]
# explode = (0.1)  # only "explode" the 2nd slice (i.e. 'Hogs')

# fig1, ax1 = plt.subplots()
# ax1.pie(sizes,  autopct='%1.1f%%',colors='red', startangle=90)
# ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

# colweek.pyplot(fig1)
