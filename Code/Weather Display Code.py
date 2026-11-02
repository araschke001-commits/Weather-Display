from machine import Pin, I2C
from Modules import sh1106
from Modules import urequests
import network
import time
import json
import framebuf

### Setup code ###

## OLED ##

# Function to return the x of the text centered at a point from the amount of letters
def centerX(letterNum, x):
    return x - ((letterNum / 2) * 8)

# Function to return the y of the text centered at a point from the amount of rows
def centerY(rowNum, y):
    return y - ((rowNum / 2) * 8)

# Set up i2c
i2c = I2C(
    0,
    sda=Pin(6),
    scl=Pin(7),
    freq=400000
)

# Scans the i2c to make sure it is working properly and outputs to console
# Expected output is [60] or [0x3C] (occasionally [61] or [0x3D])
print(i2c.scan())

# Create display object
display = sh1106.SH1106_I2C(
    128,
    64,
    i2c
)

# Display that it is initiated properly on both console and screen
print("Display Initiated")
display.fill(0) # Clear screen
display.text("Screen\nInitiated", centerX(9, 63), centerY(2, 31)) # Make text at roughly center
display.show() # Display text on screen

# Wait 0.5 seconds so there is time to see it
time.sleep_ms(500)


## Wi-Fi ##

# Show it is trying to connect
print("Connecting...")
display.fill(0) # Clear screen
display.text("Connecting...", centerX(13, 63), centerY(1, 31)) # Make text at roughly center
display.show() # Display text on screen

# Try to connect #

# Credentials for Wi-Fi
# CHANGE VALUES TO ACTUAL WIFI NAME AND PASSWORD
ssid = "YOUR WIFI NAME"
password = "YOUR WIFI PASSWORD"

# Set up Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# If Wi-Fi isn't connected, try to connect it
if not wlan.isconnected():
    wlan.connect(ssid, password)

    # Wait for a second each time until connected
    while not wlan.isconnected():
        time.sleep(1)

# Show it is connected properly
print("Connected")
display.fill(0) # Clear screen
display.text("Connected", centerX(9, 63), centerY(1, 31)) # Make text at roughly center
display.show() # Display text on screen

# Give time to let them see it is connected
time.sleep_ms(500)


## Weather Stuff ##

ICON_SIZE = 56

## ICONS HERE

# Returns name of weather icon
def get_weather_icon(weather_id):

    if weather_id == 800:
        return "sunny"

    elif weather_id in [801, 802]:
        return "partly cloudy"

    elif weather_id in [803, 804]:
        return "cloudy"

    elif 200 <= weather_id <= 232:
        return "storm"

    elif 300 <= weather_id <= 531:
        return "rain"

    elif 600 <= weather_id <= 622:
        return "snow"

    else:
        return "cloudy"

# Returns (temperature to 0.1, precipitation percent, weather icon name) for the current day
def getWeather(lat, long, apiKey):
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        "?lat=" + lat +
        "&lon=" + long +
        "&units=imperial"
        "&appid=" + apiKey
    )

    response = urequests.get(url)

    data = response.json()

    response.close()

    temperature = round(data["main"]["temp"] * 10) / 10

    weather_id = data["weather"][0]["id"]

    try:
        precipitation = data["rain"]["1h"]
    except:
        precipitation = 0

    icon = get_weather_icon(weather_id)

    return temperature, precipitation, icon

def drawIcon(icon):
    
    if icon == "sunny":
        display.blit(sun_icon, 0, 8)

    elif icon == "partly cloudy":
        display.blit(partly_icon, 0, 8)

    elif icon == "cloudy":
        display.blit(cloud_icon, 0, 8)

    elif icon == "rain":
        display.blit(rain_icon, 0, 8)

    elif icon == "storm":
        display.blit(storm_icon, 0, 8)

    elif icon == "snow":
        display.blit(snow_icon, 0, 8)



### Main loop ###

while True:

    ## Weather variables from API
    # CHANGE VALUES TO ACTUAL VALUES OF LATITUDE, LONGITUDE, AND API KEY FROM OpenWeatherMap
    temp, precip, iconName = getWeather(0, 0, "API KEY")

    ## Display weather to screen (and print that it is updating)

    # Print update
    print(f"Weather Update, Temp: {temp}, Precip: {precip}, Icon Name: {iconName}")

    # Clear screen
    display.fill(0)

    # Make text for temperature
    length = len(str(temp))
    display.text(str(temp) + "°F", centerX(length + 2, 31), centerY(1, 15))

    # Make text for precip
    length = len(str(precip))
    display.text(str(precip) + "%", centerX(length + 1, 31), centerY(1, 47))

    # Make weather icon
    drawIcon(iconName)

    # Display update on screen
    display.show()

    ## Wait because what's the rush?
    # This weather is for the full day, not just a minute in advance.
    time.sleep(300) # Wait a full 5 minutes before giving next weather update