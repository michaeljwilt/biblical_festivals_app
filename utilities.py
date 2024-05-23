import requests
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime
import pytz
from pyluach import dates

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
        sunset = sunset_local.strftime("%H:%M %p")
        return sunset
    except ValueError as e:
        return str(e)

def next_shabbat():
    # Get today's Gregorian date
    today = dates.GregorianDate.today()

    # Calculate the number of days until the next Friday (weekday 4 in pyluach)
    days_until_friday = (4 - today.weekday()) % 7

    # If today is Friday, we need to check if it's before Shabbat starts (sundown), and if so, today is Shabbat
    # Otherwise, we need to move to the next Friday
    if days_until_friday == 0:
        shabbat_start = today
    else:
        shabbat_start = today.add(days_until_friday)
    
    # Return the next Shabbat date
    return shabbat_start
