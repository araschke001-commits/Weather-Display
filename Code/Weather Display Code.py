from machine import Pin, I2C
from Modules import sh1106
from Modules import urequests
from Modules import weather_icons
import network, time, json, sys

### Setup code ###

## Variables ##

# Credentials for Wi-Fi
# CHANGE VALUES TO ACTUAL WIFI NAME AND PASSWORD
ssid = "YOUR WIFI NAME"
password = "YOUR WIFI PASSWORD"
WIFI_TIMEOUT = 30 # Seconds before Wi-Fi times out

lat = 0
long = 0
apiKey = "YOUR API KEY"


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


# Tries to connect to wifi with the given ssid and passwords for an amount of attempts, handling wifi timing out and retrying a certain amount of attempts.
def wifiConnect(ssid, password, attempts=3):
    # Show it is trying to connect
    print("Connecting...")
    display.fill(0) # Clear screen
    display.text("Connecting...", centerX(13, 63), centerY(1, 31)) # Make text at roughly center
    display.show() # Display text on screen
    
    # Try to connect until the attempts limit has been reached #
    for attempt in range(attempts):
        
        # If Wi-Fi isn't connected, try to connect it
        if not wlan.isconnected():

            wifiFailed = False

            # Wait for a second each time until connected or timeout
            try:
                wlan.connect(ssid, password)
                seconds = 0
                while not wlan.isconnected():
                    if seconds >= WIFI_TIMEOUT:
                        raise RuntimeError("Wi-Fi Timed Out")

                    time.sleep(1)

                    seconds += 1

            except RuntimeError as e:
                
                print(f"Error: {e}")

                # Show on the screen that wifi failed to connect
                display.fill(0) # Clear screen
                display.text("Wi-Fi\nTimed Out", centerX(9, 63), centerY(2, 31)) # Make text at roughly center
                display.show() # Display text on screen

                # Wait to give time to show the message
                time.sleep(1)

                # If attempts are reached, signify an error happened and exit
                if attempt >= attempts:
                    wifiFailed = True
                    sys.exit(1)

            else:
                # Show it is connected properly
                print("Connected")
                display.fill(0) # Clear screen
                display.text("Connected", centerX(9, 63), centerY(1, 31)) # Make text at roughly center
                display.show() # Display text on screen

                # Give time to let them see it is connected
                time.sleep_ms(500)

            finally:
                if wifiFailed:
                    # Turn off the screen
                    display.poweroff()

                    # Turn off Wi-Fi fully
                    if wlan.isconnected():
                        wlan.disconnect()
                    wlan.active(False)

# Set up Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Try to connect to wifi
wifiConnect(ssid, password)


## Weather API Functions ##

# Returns name of weather icon
def getWeatherIcon(weather_id):

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

# Returns the worst of the icons given in the list of weather icon names
def getWorstIcon(iconNames):
    iconFailed = False

    # Order of icons from BEST -> WORST
    iconOrder = ["sunny", "partly cloudy", "cloudy", "rain", "snow", "storm"]

    try:
        # Set the worst icon index to the index in the iconNames list matching to the worst icon index in iconOrder
        worstIconIndex = 0
        for i in range(len(iconNames)):

            # If current icon in iconNames is worse than current worst icon, set worst icon index to that index
            currentIconIndex = iconOrder.index(iconNames[i])
            if currentIconIndex > worstIconIndex:
                worstIconIndex = currentIconIndex

        # Return the name of the worst icon at the worst icon index
        return iconOrder[worstIconIndex]

    except Exception as e:
        print(f"Worst Icon Error: {e}")

        # Show on the screen that api failed to connect
        display.fill(0) # Clear screen
        display.text("Worst Icon\nError", centerX(10, 63), centerY(2, 31)) # Make text at roughly center
        display.show() # Display text on screen

        # Wait to give time to show the message
        time.sleep(1)

        sys.exit(1)

    finally:
        if iconFailed:
            # Turn off the screen
            display.poweroff()

            # Turn off Wi-Fi fully
            if wlan.isconnected():
                wlan.disconnect()
            wlan.active(False)

# Returns (temperature to 0.1, precipitation percent, weather icon name) for the current day
def getWeather(lat, long, apiKey):
    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        "?lat=" + lat +
        "&lon=" + long +
        "&units=imperial"
        "&appid=" + apiKey
    )

    try:

        response = urequests.get(url)

        # Bad API key
        if response.status_code == 401:
            response.close()
            raise ValueError("Invalid API Key")

        # Other API errors
        if response.status_code != 200:
            response.close()
            raise RuntimeError(str(response.status_code))

        data = response.json()

        response.close()

        forecasts = data["list"]

        temps = []
        icons = []
        precips = []

        # Get temps, precips, and icons
        for entry in forecasts:

            temps.append(round(entry["main"]["temp"]))

            icons.append(getWeatherIcon(entry["weather"][0]["id"]))

            precips.append(round(entry.get("pop", 0)))

        # High temperature for the day
        temp = max(temps)

        # Calculate probability of any rain in the day
        precip = 1
        for p in precips:
            precip *= 1 - p
        precip = 1 - precip

        # Get the worst weather icon from the day
        icon = getWorstIcon(icons)

        return temp, precip, icon

    except ValueError as e:
        print(f"API Error: {e}")

    except RuntimeError as e:
        print(f"API Runtime Error: {e}")

    except Exception as e:
        print(f"API Unknown Error: {e}")

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

    # Try to reconnect to wifi if disconnected
    wifiConnect(ssid, password)

    ## Retrieve weather variables from API

    TRY_LIMIT = 3

    for tryNum in range(TRY_LIMIT):

        apiFailed = False

        try:
            temp, precip, iconName = getWeather(lat, long, apiKey)

        except ValueError as e:
            # Print error and whether or not retrying
            if tryNum < TRY_LIMIT - 1:
                print(f"Error: {e}, retrying")
            else:
                apiFailed = True
                print(f"Error: {e}, exiting")

                # Show on the screen that api failed to connect
                display.fill(0) # Clear screen
                display.text("API Fetch\nFailed", centerX(9, 63), centerY(2, 31)) # Make text at roughly center
                display.show() # Display text on screen
        
                # Wait to give time to show the message
                time.sleep(1)

                # Exit while signaling an error happened
                sys.exit(1)

        except OSError as e:
            apiFailed = True
            print(f"OS Error: {e}")

            # Show on the screen that api failed to connect
            display.fill(0) # Clear screen
            display.text("Network\nError", centerX(7, 63), centerY(2, 31)) # Make text at roughly center
            display.show() # Display text on screen
    
            # Wait to give time to show the message
            time.sleep(1)

            sys.exit(1)

        except Exception as e:
            apiFailed = True
            print(f"Unknown Error: {e}")

            # Show on the screen that api failed to connect
            display.fill(0) # Clear screen
            display.text("Unknown\nAPI Error", centerX(9, 63), centerY(2, 31)) # Make text at roughly center
            display.show() # Display text on screen
    
            # Wait to give time to show the message
            time.sleep(1)

            sys.exit(1)
            
        finally:
            if apiFailed:
                # Turn off the screen
                display.poweroff()
        
                # Turn off Wi-Fi fully
                if wlan.isconnected():
                    wlan.disconnect()
                wlan.active(False)

    ## Display weather to screen (and print that it is updating)

    # Print update
    print(f"Weather Update - Temp: {temp}, Precip: {precip}, Icon Name: {iconName}")

    # Clear screen
    display.fill(0)

    # Make text for temperature
    length = len(str(temp))
    display.text(str(temp) + "°F", centerX(length + 2, 31), centerY(1, 15))

    # Make text for precip
    length = len(str(precip))
    display.text(str(precip) + "%", centerX(length + 1, 31), centerY(1, 47))

    iconFailed = False

    # Make weather icon
    try:
        drawIcon(iconName)
        
        # Display update on screen
        display.show()

    except RuntimeError as e:
        iconFailed = True
        print(f"Icon Error: {e}")

        # Show on the screen that api failed to connect
        display.fill(0) # Clear screen
        display.text("Icon\nError", centerX(5, 63), centerY(2, 31)) # Make text at roughly center
        display.show() # Display text on screen

        # Wait to give time to show the message
        time.sleep(1)

        sys.exit(1)

    except Exception as e:
        iconFailed = True
        print(f"Unknown Error: {e}")

        # Show on the screen that api failed to connect
        display.fill(0) # Clear screen
        display.text("Unknown\nError", centerX(7, 63), centerY(2, 31)) # Make text at roughly center
        display.show() # Display text on screen

        # Wait to give time to show the message
        time.sleep(1)

    finally:
        if iconFailed == True:
            # Turn off the screen
            display.poweroff()
    
            # Turn off Wi-Fi fully
            if wlan.isconnected():
                wlan.disconnect()
            wlan.active(False)


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