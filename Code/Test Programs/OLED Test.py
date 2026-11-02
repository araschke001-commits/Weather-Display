from machine import Pin, I2C
from Modules import sh1106

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