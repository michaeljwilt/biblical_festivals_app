#---------------Import Packages---------------#
from pyluach import dates, hebrewcal
from pyluach.hebrewcal import Year
import datetime
import pandas as pd
from utilities import calculate_sunset, get_next_shabbat, get_location_info, read_yaml
import streamlit as st

#---------------Configurations---------------#
st.set_page_config(page_title="Biblical Festivals", page_icon="🌟", layout="wide")

# -------------------------CSS-------------------------#
# open/create css object
with open("styles.css") as f:
    css = f.read()
# apply css to page
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

#---------------Date Work---------------#
#get todays date and the current year
today = datetime.datetime.today()
year = Year(today.year)


start = pd.offsets.YearBegin().rollback(today).date()
end = pd.offsets.YearEnd().rollforward(today).date()
end_next_year = (end + pd.DateOffset(years=1)).date()
date_range = pd.date_range(start=start, end=end)

# Create a DataFrame from the date range
df = pd.DataFrame(date_range, columns=['Date'])


#adding dates for festivals
# For each date in the DataFrame, convert to Hebrew date
df['Hebrew Date'] = df['Date'].apply(lambda x: dates.GregorianDate(x.year, x.month, x.day).to_heb())
# For each date in the DataFrame, get the festival
df['Festival'] = df['Hebrew Date'].apply(lambda x: hebrewcal.festival(x, include_working_days=True))
# Group by 'Festival' and aggregate start and end dates
festival_df = df.groupby('Festival').agg(Start_Date=('Date', 'min'), End_Date=('Date', 'max')).sort_values(by="Start_Date").reset_index()


#---------------Location Work---------------#
#hard coding location info to Nashville, TN for now
geo_name_id = '4644585'
latitude, longitude, user_timezone = get_location_info(geo_name_id)



#---------------Festival Info---------------#
#for each festival, calculate the sunset time
festival_df['start_date_timestamp'] = festival_df.apply(lambda x: str(x['Start_Date'].date()) + ' ' + calculate_sunset(latitude, longitude, x['Start_Date'], user_timezone), axis=1)
festival_df['end_date_timestamp'] = festival_df.apply(lambda x: str(x['End_Date'].date()) + ' ' + calculate_sunset(latitude, longitude, x['End_Date'], user_timezone), axis=1)
festival_df["full_start_timestamp"] = pd.to_datetime(festival_df["start_date_timestamp"].str.replace(" PM", ""))


#separating days, minutes, and hours until the festival
filtered_df = festival_df[festival_df['Start_Date'] > today].reset_index(drop=True)
filtered_df["time_until_festival"] = filtered_df["full_start_timestamp"] - today
filtered_df["days_until_festival"] = filtered_df["time_until_festival"].dt.days
filtered_df["hours_until_festival"] = (filtered_df["time_until_festival"].dt.seconds // 3600)
filtered_df["minutes_until_festival"] = (filtered_df["time_until_festival"].dt.seconds % 3600) // 60
filtered_df["event_countdown"] = filtered_df.apply(lambda x: f"{x['days_until_festival']} day(s), {x['hours_until_festival']} hour(s), {x['minutes_until_festival']} minute(s)", axis=1)



#---------------Shabbat Info---------------#
next_shabbat_date = get_next_shabbat(geo_name_id)
time_till_shabbat = pd.to_datetime(next_shabbat_date) - today
shabbat_countdown = f"{time_till_shabbat.days} day(s) {time_till_shabbat.seconds // 3600} hour(s) {time_till_shabbat.seconds % 3600 // 60} minute(s)"



#---------------Streamlit Page Build---------------#
st.title("Biblical Festivals - 2024")
st.header("Upcoming Festival & Shabbat", divider="gray")
col1, col2 = st.columns(2)
with col1.container(border=True):
    st.subheader(f"{filtered_df.iloc[0]['Festival']} begins in:")
    st.subheader(f"{filtered_df.iloc[0]['event_countdown']}")
    
with col2.container(border=True):
    st.subheader("Next Shabbat begins in:")
    st.subheader(shabbat_countdown)

#button to show more upcoming festivals
checkbox = st.checkbox("Show More Upcoming Festivals")
#if button is checked
if checkbox:
    yaml_info = read_yaml("festivals.yaml")
    #for each row in the dataframe, display the festival and the sunset time in an st.expander
    for index, row in filtered_df.iterrows():
        description = yaml_info.get(row['Festival'], "Description not found")
        st.subheader(row['Festival'], divider='blue')
        start_date_str = row['start_date_timestamp'].replace(' PM', '')
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d %H:%M')
        difference = start_date - today
        if difference.days < 1:
            diff = difference.total_seconds() // 3600
            st.write(f"{row['Festival']} starts in {diff:.0f} hour(s)")
        else:
            st.write(f"{row['Festival']} starts in {difference.days} day(s)")
        with st.expander("More Info", expanded=False):
            st.write(f"Begins on: {row['start_date_timestamp']}")
            st.write(description)
        st.subheader("")

