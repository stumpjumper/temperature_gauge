#!/usr/bin/env python

import serial
import os
import sys
import time
import ast
import thingspeak
import signal
import select

from optparse import OptionParser

modeMap = {'O':0,'B':1,'E':2,'N':3,'P':4,'M':5,'D':6}

(execDirName,execName) = os.path.split(sys.argv[0])
execBaseName = os.path.splitext(execName)[0]
defaultLogFileRoot = "/tmp/"+execBaseName
defaultConfigFilename  = "lucky7ToThingSpeak.conf"

mySerial = None

class MySignalCaughtException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

def setupCmdLineArgs(cmdLineArgs):
  usage = """\
usage: %prog [-h|--help] [options] serial_port
       where:
         -h|--help to see options

         serial_port =
           Serial port to connect to. Hint: Do a 
           "dmesg | grep tty" and look at last serial port added.
           Usually looks something like /dev/ttyACM0 or /dev/ttyUSB0
           and is at the bottom of the grep output.
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
    print "cmdLineOptions.verbose = '%s'" % cmdLineOptions.verbose
    for index in range(0,len(cmdLineArgs)):
      print "cmdLineArgs[%s] = '%s'" % (index, cmdLineArgs[index])

  if len(cmdLineArgs) != 1:
    parser.error("Must specify a serial port on the command line.")

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

  dataDict = ast.literal_eval(configData)

  bannerToKeyMap = dataDict["bannerToKeyMap"]

  idKey = getIdKey(bannerToKeyMap)
  
  assert dataDict.has_key(idKey),\
    "Could not find key '%s' in file '%s'. Keys in file are '%s'" %\
    (idKey, configFilename, dataDict.keys())

  return dataDict[idKey]

def handler(signum, frame):
  raise MySignalCaughtException("Signal caught")

def getIdKey(bannerToKeyMap):
  global mySerial
  assert mySerial, "The varialble mySerial is null"
  idKey = None
  for i in range(5):
    if not idKey:
      print "Attempting to get identification line..."
      mySerial.write('i')
      buffer = mySerial.read(mySerial.inWaiting())
      lines = buffer.split('\r\n')
      for line in lines:
        if line:
          print line
          for banner in bannerToKeyMap.keys():
            if banner in line:
              idKey = bannerToKeyMap[banner]
              break
      time.sleep(3)

  assert idKey, "Could not match any banner in lines to bannerToKeyMap\n" +\
    "lines:\n%s\nbannerToKeyMap:\n%s" % (lines, bannerToKeyMap)

  print "Found idKey:", idKey
  return idKey

def readInputFromTerminal(prompt,timeout):
  inputLine=None
  print "You have %s seconds to enter input..." % timeout
  print prompt,
  sys.stdout.flush()
  rlist, _, _ = select.select([sys.stdin], [], [], timeout)
  if rlist:
    inputLine = sys.stdin.readline().strip()
    print "Read: %s\n" % inputLine
  return inputLine

def processTerminalInput(timeout):
  global mySerial
  assert mySerial, "The varialble mySerial is null"
  while True:
    inputLine = readInputFromTerminal("Command [continue, quit]: ",timeout)
    if not inputLine:
      print "\nNo input read. Moving on..."
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
          print line
    timeout = 30

def main(cmdLineArgs):
  global mySerial
  (clo, cla) = setupCmdLineArgs(cmdLineArgs)
  serialPort     = cla[0]
  logFileRoot    = clo.logFileRoot
  configFilename = clo.configFilename
  
  if clo.verbose or clo.noOp:
    print "verbose        =", clo.verbose
    print "noOp           =", clo.noOp
    print "serialPort     =", serialPort
    print "configFilename =", configFilename
    print "logFileRoot    =", logFileRoot

  mySerial = serial.Serial(serialPort,115200)
  time.sleep(5)
  localFrequency = 5

  dataDict = readConfigData(configFilename)

  if clo.verbose or clo.noOp:
    print "dataDict:"
    print dataDict

  if clo.noOp:
    sys.exit(0)

  channel_id     = dataDict["channel_id"]
  write_key      = dataDict["write_key"]
  frequency      = dataDict["update_frequency"]
  channelKeys    = dataDict["channel_keys"]

  channel = thingspeak.Channel(id=channel_id,write_key=write_key)

  currentDateStamp = None
  outputStream     = None

  # Register the signal function handler
  signal.signal(signal.SIGALRM, handler)

  while True:
    mySerial.write('?')
    buffer = mySerial.read(mySerial.inWaiting())
    lines = buffer.split('\r\n')
    for line in lines:
      if line:
        line = line.strip()
        print line
        if line[0] == "{":
          localFrequency = frequency
          if currentDateStamp != createDateStamp():
            currentDateStamp = createDateStamp()
            outputFileName = makeOutputFileName(logFileRoot, createDateStamp())
            print "New outputfile = '%s'" % outputFileName
            if outputStream:
              outputStream.close()
            outputStream = makeOutputStream(outputFileName)
          try:
            outputDict = ast.literal_eval(line)
          except Exception, e:
            print "'outputDict = ast.literal_eval(line)' error"
            try:
              print str(e)
            except:
              print "  Sorry, could not print ast.literal_eval()  error. Continuing..."
          print outputDict
          print >>outputStream , outputDict
          outputStream.flush()
          try:
            line = time.asctime() + " " + line
            channelDict = {1:outputDict[channelKeys[0]][0],
                           2:outputDict[channelKeys[1]][0],
                           3:outputDict[channelKeys[2]][0],
                           4:outputDict[channelKeys[3]][0],
                           5:outputDict['v'],
                           6:outputDict['p'],
                           7:modeMap[outputDict['m']],
                           8:outputDict['lN'],
                           "status":line}
            print "channelDict =", channelDict
            try:
              signal.alarm(120) # Throw MySignalCaughtException in (n) secs
              response = channel.update(channelDict)
              signal.alarm(0) # Cancel alarm
              print response
            except MySignalCaughtException, e:
              print "Signal alarm caught, channel.update(channelDict) timed out.  Continuing..."
            except Exception, e:
              print "channel.update(channelDict) failed:"
              try:
                print str(e)
                print "Continuing..."
              except:
                print "  Sorry, could not print channel.update() error. Continuing..."
          except Exception, e:
            print "Creation of channelDict failed:"
            try:
              print str(e)
              print "Continuing..."
            except:
              print "  Sorry, could not print creation error.  Continuing..."

    processTerminalInput(localFrequency)

  outputStream.close()

if (__name__ == '__main__'):
  main(sys.argv[1:])
