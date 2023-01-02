#!/usr/bin/env python3

import sys
import os
from optparse import OptionParser

from talkToScreen import TalkToScreen

execDir = os.path.dirname(os.path.realpath(__file__))

sleepSecondsDefault = 300
screenNameDefault = "PIComms"

def setupCmdLineArgs(cmdLineArgs):
  usage = "usage: %prog [-h|--help] [options] screen_name command_to_run"
  usage +=\
"""
       where:
         -h|--help to see options

         screen_name =
          The name of the screen in which to run the communication program

         command to run =
          The command that will be run in the screen named --screenName (default is "%s").
          Arguments to the command are set with zero or more -a|--argumnet options.
          The command is wrapped in a loop that re-runs the command after -s|--sleepSeconds
          seconds (default is %s secs) if the command exits.
""" % (screenNameDefault, sleepSecondsDefault)

  parser = OptionParser(usage)
                       
  help="verbose mode."
  parser.add_option("-v", "--verbose",
                    action="store_true", default=False,
                    dest="verbose",
                    help=help)

  help="No operation, just echo commands"
  parser.add_option("-n", "--noOp",
                    action="store_true", 
                    default=False,
                    dest="noOp",
                    help=help)
  
  help="Arguments to command_to_run. You can use multiple -a arguments "+\
        "to specify multiple arguments. Quote the argument if it contains "+\
        "spaces."
  parser.add_option("-a", "--argument",
                    action="append", type="string", 
                    default=None,
                    dest="argumentList",
                    help=help)

  help="Arguments to command_to_run. You can use multiple -a arguments "+\
        "to specify multiple arguments. Quote the argument if it contains "+\
        "spaces."
  parser.add_option("--screenName",
                    action="store", type="string", 
                    default=screenNameDefault,
                    dest="argumentList",
                    help=help)

  help="Number of seconds as an integer to sleep before re-executing command if "+\
       "it exits. Default is %s" % sleepSecondsDefault
  parser.add_option("-s", "--sleepSeconds",
                    action="store_true", default=sleepSecondsDefault,
                    dest="sleepSeconds", type="int",
                    help=help)

  # To Do Next: Need to check all this stuff
  (cmdLineOptions, cmdLineArgs) = parser.parse_args(cmdLineArgs)
  clo = cmdLineOptions

  if cmdLineOptions.verbose:
    print("cmdLineOptions:",cmdLineOptions)
    for index in range(0,len(cmdLineArgs)):
      print("cmdLineArgs[%s] = '%s'" % (index, cmdLineArgs[index]))

  if len(cmdLineArgs) != 1:
    parser.error("A command to run must be given on the command line")

  return (cmdLineOptions, cmdLineArgs)

def main(cmdLineArgs):
  (clo, cla) = setupCmdLineArgs(cmdLineArgs)

  command      = cla[0]
  arguments    = clo.argumentList
  screenName   = clo.screenName
  sleepSeconds = clo.sleepSeconds

  if clo.verbose:
    print("verbose      =", clo.verbose )
    print("noOp         =", clo.noOp    )
    print("command      =", command     )
    print("argumentList =", argumentList)
    print("screenName   =", screenName  )
    print("sleepSeconds =", sleepSeconds)

  command = command + " " + " ".join(argumentList)

  if clo.noOp:
    print("Would be creating TalkToScreen object using name '%s'" % screenName)
  else:
    screen = TalkToScreen.createWithName(screenName)

  if not clo.noOp:
    if screen.screenAlreadyRunning():
      print("Screen with name '%s' already running.  Exiting...", 
            file=sys.stderr)

      return

  if clo.noOp:
    print("Would be starting screen with name '%s'" % screenName)
  else:
    if clo.verbose:
      print("Starting screen with name '%s'" % screenName)
    screen.startScreen()

  cmdList = []
  cmdList.append("cd '%s'" % execDir)
  cmdList.append("while :; do")
  cmdList.append("date")
  cmdList.append(command)
  cmdList.append("echo 'Sleeping for %s seconds (Ctrl-c to exit)...'" % sleepSeconds)
  cmdList.append("sleep %s" % sleepSeconds)
  cmdList.append("done")

  try:
    for cmd in cmdList:
      if clo.noOp:
        print("Would be executing the following in screen '%s':\n" \
              % screenName, cmd)
      else:
        if clo.verbose:
          print("Executing the following command in screen '%s':\n" \
                % screenName, cmd)
          screen.executeCmdInScreen(cmd)
  except KeyboardInterrupt:
    if clo.verbose:
      print("Caught KeyboardInterrupt, exiting screen '%s':\n" \
            % screenName)
      screen.exitScreen()

if (__name__ == '__main__'):
  main(sys.argv[1:])
