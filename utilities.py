import requests
from astral import LocationInfo
from astral.sun import sun
import pytz
import pandas as pd
import yaml

def get_location():
    response = requests.get('https://ipinfo.io')
    data = response.json()
    loc = data['loc'].split(',')
    latitude = float(loc[0])
    longitude = float(loc[1])
    return latitude, longitude

def convert_timezone(utc_timestamp, user_timezone):
    # Ensure the datetime is timezone-aware in UTC
    if utc_timestamp.tzinfo is None:
        utc_timestamp = pytz.utc.localize(utc_timestamp)
    # Convert to the user's timezone
    user_dt = utc_timestamp.astimezone(user_timezone)
    return user_dt

def calculate_sunset(latitude, longitude, date, user_timezone):
    try:
        location = LocationInfo(latitude=latitude, longitude=longitude)
        s = sun(location.observer, date=date)
        sunset_utc = s["sunset"]
        sunset_local = convert_timezone(sunset_utc, user_timezone)
        sunset = sunset_local.strftime("%I:%M %p")
        return sunset
    except ValueError as e:
        return str(e)

# get the next shabbat
def get_next_shabbat(city):
    url = f"https://www.hebcal.com/shabbat?cfg=json&geonameid={city}"
    response = requests.get(url)
    data = response.json()
    for item in data['items']:
        if item['category'] == 'candles':
            date = pd.to_datetime(item['date'])
            return date.strftime('%Y-%m-%d %H:%M')


def get_location_info(city):
    url = f"https://www.hebcal.com/shabbat?cfg=json&geonameid={city}"
    response = requests.get(url)
    data = response.json()
    latitude = data['location']['latitude']
    longitude = data['location']['longitude']
    timezone = pytz.timezone(data['location']['tzid'])
    return latitude, longitude, timezone

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data


    