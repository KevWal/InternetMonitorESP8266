# Internet Monitor
# Jack Walton

# Runs on a Wemos D1 mini - ESP8266EX, 26Mhz, 4MB
# https://wiki.wemos.cc/products:retired:d1_mini_v2.2.0
# with an oled shield and a neopixel RGB shield

# Write firmware with:
# C:\Apps\Python27\Scripts>esptool.py.exe --chip esp8266 --port COM4 erase_flash
# C:\Apps\Python27\Scripts>esptool.py.exe --chip esp8266 --port COM4 write_flash 0x0000 esp8266-20170612-v1.9.1.bin
# View files
# C:\Apps\Python27\Scripts>ampy -p COM4 ls
# Upload file
# C:\Apps\Python27\Scripts>ampy -p COM4 put main.py


# Esp8266 hardware control
#import machine
#import os
import time
from machine import I2C
from machine import Pin

# Network Comms
import network
import socket

# Control Neopixel LED
import neopixel

# Control OLED Display
import ssd1306

print("Turn off esp8266 debug output")
import esp
esp.osdebug(None)

# Access ESP8266 using ampy, set AMPY_PORT=COM3 or -p //com6, 115200 Baud,
# check serial port in device manager
# Navigate to D:\python in CMD before attempting to use ampy

Latencies = [0,0,0]
Off = (0x00, 0x00, 0x00)
White = (0xff, 0xff, 0xff) # Issues connecting to wifi
Red = (0xff, 0x00, 0x00) # Latency checked and too long
Orange = (0xff, 0x22, 0x00) # Latency checked and not great
Green = (0x00, 0xff, 0x00) # Latency checked and fine
Blue = (0x00, 0x00, 0xff) # Not used
Purple = (0x99, 0x00, 0xff) # Failed to connect to any of the test web sites

print("Setup")
Stream = socket.socket()

LED = neopixel.NeoPixel(Pin(14, Pin.OUT), 1)
LED[0] = Off
LED.write()

i2c = I2C(sda=Pin(4), scl=Pin(5))
display = ssd1306.SSD1306_I2C(64, 48, i2c)
display.fill(0)

def WiFi_Connect(ESSID, PASS):
    ConnectTimeOut = 0
    WiFi_Net_STA_IF = network.WLAN(network.STA_IF)
    WiFi_Net_STA_IF.active(True)
    Connected = True
    if not WiFi_Net_STA_IF.isconnected():
        print("Connecting to network..")
        try:
            WiFi_Net_STA_IF.active(True)
            WiFi_Net_STA_IF.connect(ESSID, PASS)
        except OSError:
            LED[0] = White
            LED.write()
            time.sleep(5)
            machine.reset()
        while not WiFi_Net_STA_IF.isconnected():
            ConnectTimeOut += 1
            print(".")
            time.sleep(1)

            if ConnectTimeOut > 30:
                print("Connection Failed")
                WiFi_Net_STA_IF.active(False)
                Connected = False

    if Connected:
        print('Network connected, Config: \n' +
str(WiFi_Net_STA_IF.ifconfig()))
        LED[0] = Off
        LED.write()
        display.text('Joined',10,5)
        display.text('WiFi',17,15)
        display.show()
        time.sleep_ms(50)
        display.fill(0)
    return WiFi_Net_STA_IF


def TestLatancy(FQDN):
    StartTime = time.ticks_ms()
    Stream = socket.socket()
    TestSuccess = bool
    try:
        Addr_Info = socket.getaddrinfo(FQDN, 80)

        IP_Addr = Addr_Info[0][-1]
        Stream.connect(IP_Addr)

        Stream.send(b"GET / HTTP/1.0\r\n\r\n")

    except OSError:
        TestSuccess = False
        LED[0] = Off
        LED.write()


    RecvData = 0
    while True:
        if RecvData == None:
            RecvData = Stream.recvfrom(4096)
        else:
            Latancy = time.ticks_diff(time.ticks_ms(), StartTime)
            break

    if TestSuccess:
        Latancy = time.ticks_diff(time.ticks_ms(), StartTime)
    else:
        Latancy = "Failed"

    Stream.close()

    return Latancy

#MAIN
while True:
    WiFi_Net_STA_IF = WiFi_Connect("54g", "Believeinbetter")

    while not WiFi_Net_STA_IF.isconnected():
        WiFi_Connect("54g", "Believeinbetter")
        LED[0] = White
        LED.write()
        time.sleep_ms(50)
        LED[0] = Off
        LED.write()
        if not WiFi_Net_STA_IF.isconnected():
            print("WiFi has not connected first time.")
            LED[0] = Off
            LED.write()


    FQDN_Array = ["www.google.com", "www.bing.com", "www.yahoo.co.uk"]
    ConnectionsMade = len(FQDN_Array)
    LatancyTotal = 0
    for i in range(len(FQDN_Array)):
        LatancyTime = TestLatancy(FQDN_Array[i])
        Latencies[i] = str(LatancyTime) + "ms"
        print("connection " + str(i+1) + " to " + FQDN_Array[i] + " took "
+ Latencies[i])

        if LatancyTime == "Failed":
            ConnectionsMade -= 1
        else:
            LatancyTotal += LatancyTime

    if ConnectionsMade == 0:
        LED[0] = Purple
        LED.write()
        time.sleep(10)
    else:
        AvgLatancy = LatancyTotal / ConnectionsMade

        print("Connections Made "+ str(ConnectionsMade) + " Total Latancy: " + str(LatancyTotal) + " Average Ping time: " + str(AvgLatancy))

        if AvgLatancy > 50:
            LED[0] = Red
        elif AvgLatancy > 25:
            LED[0] = Orange
        else:
            LED[0] = Green
        LED.write()

        for i in range (3):
            display.text('Google:',0,10)
            display.text(str(Latencies[0]),0,20)
            display.show()
            time.sleep(1)

            display.fill(0)
            display.text('Bing:',0,10)
            display.text(str(Latencies[1]),0,20)
            display.show()
            time.sleep(1)

            display.fill(0)
            display.text('Yahoo:',0,10)
            display.text(str(Latencies[2]),0,20)
            display.show()
            time.sleep(1)
            display.fill(0)

    #run once
        #break
    display.fill(0)
    display.show()
    LED[0] = Off
    LED.write()

