#!/usr/bin/env python

import time
import Adafruit_DHT
#-# from ISStreamer.Streamer import Streamer
# --------- User Settings ---------
#-# SENSOR_LOCATION_NAME = "Office"
#-# BUCKET_NAME = ":partly_sunny: Room Temperatures"
#-# BUCKET_KEY = "rt0129"
#-# ACCESS_KEY = "PLACE YOUR INITIAL STATE ACCESS KEY HERE"

MINUTES_BETWEEN_READS = .25 # DHt22 max read rate is every 2 seconds (.0334 min)
METRIC_UNITS = False
# ---------------------------------
#-# streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY)
while True:
  humidity, temp_c = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)
  if not METRIC_UNITS:
    temp_f = format(temp_c * 9.0 / 5.0 + 32.0, ".2f")
  #-# streamer.log(SENSOR_LOCATION_NAME + " Temperature(F)", temp_f)
  humidity = format(humidity,".2f")
  #-# streamer.log(SENSOR_LOCATION_NAME + " Humidity(%)", humidity)
  #-# streamer.flush()
  print (time.asctime(), ": Temp(F), Humidity:", temp_f, humidity)
	
  time.sleep(60*MINUTES_BETWEEN_READS)

