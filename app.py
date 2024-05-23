#%%
from pyluach import dates, hebrewcal
from pyluach.hebrewcal import Year
import datetime
import pandas as pd
from utilities import calculate_sunset
import streamlit as st
import pytz
import requests

st.set_page_config(page_title="Biblical Festivals", page_icon="🌟", layout="wide")
#%%
today = datetime.datetime.today()
year = Year(today.year)

# Beginning of the year
start = pd.offsets.YearBegin().rollback(today).date()
end = pd.offsets.YearEnd().rollforward(today).date()
end_next_year = (end + pd.DateOffset(years=1)).date()
date_range = pd.date_range(start=start, end=end)

#%%
# Create a DataFrame from the date range
df = pd.DataFrame(date_range, columns=['Date'])

#%%
# For each date in the DataFrame, convert to Hebrew date
df['Hebrew Date'] = df['Date'].apply(lambda x: dates.GregorianDate(x.year, x.month, x.day).to_heb())

#%%
# For each date in the DataFrame, get the festival
df['Festival'] = df['Hebrew Date'].apply(lambda x: hebrewcal.festival(x, include_working_days=True))

#%%
# Group by 'Festival' and aggregate start and end dates
festival_df = df.groupby('Festival').agg(Start_Date=('Date', 'min'), End_Date=('Date', 'max')).sort_values(by="Start_Date").reset_index()


# latitude = location["latitude"]
latitude = 35.9251
longitude = -86.8689
user_timezone = pytz.timezone('America/New_York')

sunset = calculate_sunset(latitude, longitude, today, user_timezone)


#for each festival, calculate the sunset time
festival_df['Start_Date_Timestamp'] = festival_df.apply(lambda x: str(x['Start_Date'].date()) + ' ' + calculate_sunset(latitude, longitude, x['Start_Date'], user_timezone), axis=1)
festival_df['End_Date_Timestamp'] = festival_df.apply(lambda x: str(x['End_Date'].date()) + ' ' + calculate_sunset(latitude, longitude, x['End_Date'], user_timezone), axis=1)
festival_df["Start_Timestamp"] = pd.to_datetime(festival_df["Start_Date_Timestamp"].str.replace(" PM", ""))

filtered_df = festival_df[festival_df['Start_Date'] > today].reset_index(drop=True)
filtered_df["time_until_festival"] = filtered_df["Start_Timestamp"] - today
filtered_df["days_until_festival"] = filtered_df["time_until_festival"].dt.days
filtered_df["hours_until_festival"] = (filtered_df["time_until_festival"].dt.seconds // 3600)
filtered_df["minutes_until_festival"] = (filtered_df["time_until_festival"].dt.seconds % 3600) // 60
filtered_df["event_countdown"] = filtered_df.apply(lambda x: f"{x['days_until_festival']} days, {x['hours_until_festival']} hours, {x['minutes_until_festival']} minutes", axis=1)


# get the next shabbat
def get_next_shabbat(city):
    url = f"https://www.hebcal.com/shabbat?cfg=json&geonameid={city}"
    response = requests.get(url)
    data = response.json()
    for item in data['items']:
        if item['category'] == 'candles':
            date = pd.to_datetime(item['date'])
            return date.strftime('%Y-%m-%d %H:%M')

# Replace '5128581' with the geonameid for your city (e.g., New York City)
next_shabbat_date = get_next_shabbat('4644585')
time_till_shabbat = pd.to_datetime(next_shabbat_date) - today
st.write()
shabbat_countdown = f"{time_till_shabbat.days} days {time_till_shabbat.seconds // 3600} hours {time_till_shabbat.seconds % 3600 // 60} minutes"



st.title("Biblical Festivals")
st.header("Upcoming Festival", divider="gray")
col1, col2 = st.columns(2)
with col1.container(border=True):
    st.subheader(f"{filtered_df.iloc[0]['Festival']} begins in:")
    st.subheader(f"{filtered_df.iloc[0]['event_countdown']}")
    
with col2.container(border=True):
    st.subheader("Next Shabbat begins in:")
    st.subheader(shabbat_countdown)






button = st.checkbox("Show More Upcoming Festivals")

if button:
    #for each row in the dataframe, display the festival and the sunset time in an st.expander
    for index, row in filtered_df.iterrows():
        st.subheader(row['Festival'], divider='gray')
        start_date_str = row['Start_Date_Timestamp'].replace(' PM', '')
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d %H:%M')
        difference = start_date - today
        if difference.days < 1:
            diff = difference.total_seconds() // 3600
            st.write(f"{row['Festival']} starts is {diff:.0f} hours")
        else:
            st.write(f"{row['Festival']} starts is {difference.days} days")
        if index == min(filtered_df.index):
            with st.expander("More Info", expanded=True):
                st.write(f"Start Date: {row['Start_Date_Timestamp']}")
                st.write(f"End Date: {row['End_Date_Timestamp']}")
        else:
            with st.expander("More Info", expanded=False):
                st.write(f"Start Date: {row['Start_Date_Timestamp']}")
                st.write(f"End Date: {row['End_Date_Timestamp']}")


