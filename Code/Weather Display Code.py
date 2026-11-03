from machine import Pin, I2C
from Modules import sh1106
from Modules import urequests
from Modules import weather_icons
import network, time, json, sys

### Setup code ###

## OLED ##

# Function to return the x of the text centered at a point from the amount of letters
def centerX(letterNum, x):
    return int(x - ((letterNum / 2) * 8))

# Function to return the y of the text centered at a point from the amount of rows
def centerY(rowNum, y):
    return int(y - ((rowNum / 2) * 8))

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

WIFI_TIMEOUT = 30

# Set up Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# If Wi-Fi isn't connected, try to connect it
if not wlan.isconnected():
    wlan.connect(ssid, password)

    # Wait for a second each time until connected or timeout
    seconds = 0
    try:
        while not wlan.isconnected():
            if seconds >= WIFI_TIMEOUT:
                raise RuntimeError("Wi-Fi Timed Out")

            time.sleep(1)
    except RuntimeError as e:
        print(f"Error: {e}")

        # Signify an error happened and exit
        sys.exit(1)
    finally:
        # Show on the screen that wifi failed to connect
        display.fill(0) # Clear screen
        display.text("Wi-Fi\nTimed Out", centerX(9, 63), centerY(3, 31)) # Make text at roughly center
        display.show() # Display text on screen

        # Wait to give time to show the message
        time.sleep(5)

        # Turn off the screen
        display.poweroff()

        # Turn off Wi-Fi fully
        if wlan.isconnected():
            wlan.disconnect()
        wlan.active(False)

# Show it is connected properly
print("Connected")
display.fill(0) # Clear screen
display.text("Connected", centerX(9, 63), centerY(1, 31)) # Make text at roughly center
display.show() # Display text on screen

# Give time to let them see it is connected
time.sleep_ms(500)


## Weather Functions ##

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
        "https://api.openweathermap.org/data/2.5/weather" +
        "?lat=" + str(lat) +
        "&lon=" + str(long) +
        "&units=imperial" +
        "&appid=" + str(apiKey)
    )

    response = urequests.get(url)

    if response.status_code == 401:
        response.close()
        raise ValueError("Invalid API key")

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
        display.blit(weather_icons.sun_icon, 67, 3)

    elif icon == "partly cloudy":
        display.blit(weather_icons.partly_icon, 67, 3)

    elif icon == "cloudy":
        display.blit(weather_icons.cloudy_icon, 67, 3)

    elif icon == "rain":
        display.blit(weather_icons.rain_icon, 67, 3)

    elif icon == "storm":
        display.blit(weather_icons.storm_icon, 67, 3)

    elif icon == "snow":
        display.blit(weather_icons.snow_icon, 67, 3)

    else:
        raise RuntimeError(f"Invalid Icon Name of \"{icon}\"")



### Main loop ###

while True:

    ## Handle Wi-Fi reconnecting

    # If Wi-Fi isn't connected, try to connect it again
    if not wlan.isconnected():
        # Show it is trying to connect
        print("Reconnecting...")
        display.fill(0) # Clear screen
        display.text("Reconnecting...", centerX(15, 63), centerY(1, 31)) # Make text at roughly center
        display.show() # Display text on screen

        # Try to connect
        wlan.connect(ssid, password)

        # Wait for a second each time until connected or timeout
        seconds = 0
        try:
            while not wlan.isconnected():
                if seconds >= WIFI_TIMEOUT:
                    raise RuntimeError("Wi-Fi Timed Out")
    
                time.sleep(1)
        except RuntimeError as e:
            print(f"Error: {e}")
    
            # Signify an error happened and exit
            sys.exit(1)
        finally:
            # Show on the screen that wifi failed to connect
            display.fill(0) # Clear screen
            display.text("Wi-Fi\nTimed Out", centerX(9, 63), centerY(3, 31)) # Make text at roughly center
            display.show() # Display text on screen
    
            # Wait to give time to show the message
            time.sleep(5)
    
            # Turn off the screen
            display.poweroff()
    
            # Turn off Wi-Fi fully
            if wlan.isconnected():
                wlan.disconnect()
            wlan.active(False)
            
        # Show it is connected properly
        print("Connected")
        display.fill(0) # Clear screen
        display.text("Connected", centerX(9, 63), centerY(1, 31)) # Make text at roughly center
        display.show() # Display text on screen

        # Give time to let them see it is connected
        time.sleep_ms(500)

    ## Weather variables from API

    TRY_LIMIT = 3

    for tryNum in range(TRY_LIMIT):
        try:
            # CHANGE VALUES TO ACTUAL VALUES OF LATITUDE, LONGITUDE, AND API KEY FROM OpenWeatherMap
            temp, precip, iconName = getWeather(0, 0, "API KEY")

            # Successful attempt
            break
        except Exception as e:
            # Print error and whether or not retrying
            if tryNum < TRY_LIMIT - 1:
                print(f"Error: {e}, retrying")
            else:
                print(f"Error: {e}, exiting")

                # Exit while signaling an error happened
                sys.exit(1)
        finally:
            # Show on the screen that wifi failed to connect
            display.fill(0) # Clear screen
            display.text("API Key\nTimed Out", centerX(9, 63), centerY(3, 31)) # Make text at roughly center
            display.show() # Display text on screen
    
            # Wait to give time to show the message
            time.sleep(5)
    
            # Turn off the screen
            display.poweroff()
    
            # Turn off Wi-Fi fully
            if wlan.isconnected():
                wlan.disconnect()
            wlan.active(False)

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

    ## Now we wait because... what's the rush for?
    # This weather is for the full day, not just a minute in advance.
    # If you were to live life too quickly, you would not get all the benefits of it.
    # The same is true for the board.
    # If it doesn't wait for a minute (or 5) every once in a while,
    # it will get bogged down with all of the busyness in life and not be able to enjoy it.
    # The board has to slow down.
    # It is unable to keep up with the business in life,
    # and there is no point in doing so,
    # since that slows it down even more and makes it unproductive.

    time.sleep(300) # Wait a full 5 minutes before giving next weather update