import network
import time

# Credentials for Wi-Fi
# I'm not using my own for privacy, although I will replace it when I actually use it
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

# Print Wi-Fi configurations
print(wlan.ifconfig())