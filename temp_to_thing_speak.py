#!/usr/bin/env python3

import os
import sys
import time
import ast
import signal
import socket
import thingspeak
import Adafruit_DHT


from optparse import OptionParser


(execDirName,execName) = os.path.split(sys.argv[0])
execBaseName           = os.path.splitext(execName)[0]

defaultLogFileRoot      = "/tmp/"+execBaseName
defaultConfigFilename   = execBaseName + ".conf"
thingspeakTimeoutSeconds = 120

hostname = socket.gethostname()

class MySignalCaughtException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

def setupCmdLineArgs(cmdLineArgs):
  usage = """\
usage: %prog [-h|--help] [options]
       where:
         -h|--help to see options
"""
  parser = OptionParser(usage)
  help="Verbose mode."
  parser.add_option("-v", "--verbose",
                    action="store_true", 
                    default=False,
                    dest="verbose",
                    help=help)
  help="No operation, just read data file and echo it"
  parser.add_option("-n", "--noOp",
                    action="store_true", 
                    default=False,
                    dest="noOp",
                    help=help)
  help="Root name of logfile.  Default is '%s', " % defaultLogFileRoot
  help+="which produces the log file '%s.2015-08-17.log'" % defaultLogFileRoot
  parser.add_option("-l", "--logFileRoot",
                    action="store", type="string", 
                    default=defaultLogFileRoot,
                    dest="logFileRoot",
                    help=help)
  help ="Name of file containing configuration data in the form of "
  help+="a dictionary.  Default is '%s'" % defaultConfigFilename
  parser.add_option("-c", "--configFile",
                    action="store", type="string", 
                    default=defaultConfigFilename,
                    dest="configFilename",
                    help=help)

  (cmdLineOptions, cmdLineArgs) = parser.parse_args(cmdLineArgs)

  if cmdLineOptions.verbose:
    print("cmdLineOptions.verbose = '%s'" % cmdLineOptions.verbose)
    for index in range(0,len(cmdLineArgs)):
      print("cmdLineArgs[%s] = '%s'" % (index, cmdLineArgs[index]))

  if len(cmdLineArgs) != 0:
    parser.error("All command-line arguments require a flag. "+\
                 "Found the following without flags: %s" % cmdLineArgs)

  return (cmdLineOptions, cmdLineArgs)

def createDateStamp():
  return time.strftime("%Y-%m-%d",time.localtime())

def makeOutputStream(outputFileName):
  return open(outputFileName,'a')

def makeOutputFileName(logFileRoot, dateStamp):
  return  logFileRoot + "." + createDateStamp() + ".log"

def readConfigData(configFilename):
  with open(configFilename,'r') as configStream:
    configData = configStream.read()

  configDataDict = ast.literal_eval(configData)

  hostnameToKeyMap = configDataDict["hostnameToKeyMap"]

  idKey = getIdKey(hostnameToKeyMap)
  
  assert idKey in configDataDict,\
    "Could not find key '%s' in file '%s'. Keys in file are '%s'" %\
    (idKey, configFilename, list(configDataDict.keys()))

  return configDataDict[idKey]

def handler(signum, frame):
  raise MySignalCaughtException("Signal caught")

def getIdKey(hostnameToKeyMap):
  idKey = None
  if hostname in hostnameToKeyMap:
    idKey = hostnameToKeyMap[hostname]
  else:
    assert idKey, \
      "Could not match hostname '%s' to key in config file" % hostname +\
      "Available keys are: %s" % list(hostnameToKeyMap)

  print("Found idKey:", idKey)
  return idKey

def readInputFromTerminal(prompt,timeout):
  inputLine=None
  print("You have %s seconds to enter input..." % timeout)
  print(prompt,end="")
  sys.stdout.flush()
  rlist, _, _ = select.select([sys.stdin], [], [], timeout)
  if rlist:
    inputLine = sys.stdin.readline().strip()
    print("Read: %s\n" % inputLine)
  return inputLine

def processTerminalInput(timeout):
  global mySerial
  assert mySerial, "The varialble mySerial is null"
  while True:
    inputLine = readInputFromTerminal("Command [continue, quit]: ",timeout)
    if not inputLine:
      print("\nNo input read. Moving on...")
      return
    else:
      if inputLine.lower() == 'continue':
        return
      if inputLine.lower() == 'quit':
        sys.exit(0)
      mySerial.write(inputLine)
      buffer = mySerial.read(mySerial.inWaiting())
      lines = buffer.split('\r\n')
      for line in lines:
        if line:
          print(line)
    timeout = 30

def main(cmdLineArgs):
  global mySerial
  (clo, cla) = setupCmdLineArgs(cmdLineArgs)
  logFileRoot    = clo.logFileRoot
  configFilename = clo.configFilename
  
  if clo.verbose or clo.noOp:
    print("verbose        =", clo.verbose   )
    print("noOp           =", clo.noOp      )
    print("configFilename =", configFilename)
    print("logFileRoot    =", logFileRoot   )

  configDataDict = readConfigData(configFilename)

  if clo.verbose or clo.noOp:
    print("configDataDict:")
    print(configDataDict)

  if clo.noOp:
    sys.exit(0)

  channel_id      = configDataDict["channel_id"]
  write_key       = configDataDict["write_key"]
  updateFrequency = configDataDict["update_frequency"]
  channelKeys     = configDataDict["channel_keys"]

  channel = thingspeak.Channel(id=channel_id,api_key=write_key)

  currentDateStamp = None
  outputStream     = None

  # Register the signal function handler
  signal.signal(signal.SIGALRM, handler)

  while True:
    humidity, temp_c = (None, None)
    try:
      humidity, temp_c = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)
    except Exception as e:
      print("'Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)' exception:")
      try:
        print(str(e))
      except:
        print("  Sorry, could not print Adafruit_DHT.read_retry() error msg.")
      print("Continuing...")

    if humidity and temp_c:
      temp_f = None
      try:
        temp_f = temp_c * 9.0 / 5.0 + 32.0
      except Exception as e:
        print("Conversion of temp_c = '%s' to Fahrenheit failed" % temp_c)
        try:
          print("Error msg:",str(e))
        except:
          print("  Sorry, could not print channel.update() error.")
        print("Continuing...")

      if temp_f:
        try:
          line = "%s: temp_f = %.2f(F), humidity = %.2f%s" % \
            (time.asctime(),temp_f, humidity,"%")
          print("humidity, temp_c:", humidity, temp_c)
          if clo.verbose:
            print("Status line:", line)

          channelDict = {1:temp_f,
                         2:humidity,
                         3:temp_f,
                         4:humidity,
                         "status":line}
          print("channelDict =", channelDict)
          try:
            signal.alarm(120) # Throw MySignalCaughtException in (n) secs
            response = channel.update(channelDict)
            signal.alarm(0) # Cancel alarm
            print("Channel update response",response)
          except MySignalCaughtException as e:
            print("Signal alarm caught, channel.update(channelDict) timed out.  Continuing...")
          except Exception as e:
            print("channel.update(channelDict) failed:")
            try:
              print("Error msg:",str(e))
            except:
              print("  Sorry, could not print channel.update() error.")
            print("Continuing...")
        except Exception as e:
          print("Creation of channelDict failed:")
          try:
            print("Error msg:",str(e))
            print("Continuing...")
          except:
            print("  Sorry, could not print creation error.  Continuing...")

    if clo.verbose:
      print("Sleeping for %s seconds" % updateFrequency)
    time.sleep(updateFrequency)

if (__name__ == '__main__'):
  main(sys.argv[1:])
