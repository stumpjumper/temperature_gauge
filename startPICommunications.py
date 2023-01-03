#!/usr/bin/env python3

import sys
import os
from optparse import OptionParser

from talkToScreen import TalkToScreen

execDir = os.path.dirname(os.path.realpath(__file__))

sleepSecondsDefault = 300
screenNameDefault = "PIComms"

def setupCmdLineArgs(cmdLineArgs):
  usage =  "usage: %prog [-h|--help] [options] command_to_run\n"
  usage += "usage: %prog [-h|--help] -e|--exitScreen\n"
  usage += "usage: %prog [-h|--help] -l|--listScreens"
  usage +=\
"""
       where:
         -h|--help to see options

         screen_name =
          The name of the screen in which to run the communication program

         command to run =
          The command that will be run in the screen named --screenName
          (default is "%s").
          Arguments to the command are set with zero or more -a|--argumnet options.
          If --noLoop is not used, the command is wrapped in an endless loop that
          re-runs the command after -s|--sleepSeconds seconds (default is %s secs) 
          when the command exits.
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
                    dest="screenName",
                    help=help)

  help="Number of seconds as an integer to sleep before re-executing command if "+\
       "it exits. Default is %s" % sleepSecondsDefault
  parser.add_option("-s", "--sleepSeconds",
                    action="store", default=sleepSecondsDefault,
                    dest="sleepSeconds", type="int",
                    help=help)

  help="Do not put an execution loop around the command to execute. "+\
    "This will ignoreSleepSeconds"
  parser.add_option("--noLoop",
                    action="store_true", 
                    default=False,
                    dest="noLoop",
                    help=help)

  help="Send command to screen even if screen is already running.  NOTE: Without the --noLoop option, commands run using this script are put in an endless loop. Sending a command to a screen with a looping command will not have any effect unless the loop for some reason exits."
  parser.add_option("-f", "--force",
                    action="store_true", 
                    default=False,
                    dest="forceExecution",
                    help=help)

  help="Exit the given screen if it exists."
  parser.add_option("-e", "--exitScreen",
                    action="store_true", 
                    default=False,
                    dest="exitScreen",
                    help=help)
  
  help="List all running screens and exit."
  parser.add_option("-l", "--listScreens",
                    action="store_true", 
                    default=False,
                    dest="listScreens",
                    help=help)
  

  # To Do Next: Need to check all this stuff
  (cmdLineOptions, cmdLineArgs) = parser.parse_args(cmdLineArgs)
  clo = cmdLineOptions

  if cmdLineOptions.verbose:
    print("cmdLineOptions:",cmdLineOptions)
    for index in range(0,len(cmdLineArgs)):
      print("cmdLineArgs[%s] = '%s'" % (index, cmdLineArgs[index]))

  if (len(cmdLineArgs) != 1
      and not cmdLineOptions.exitScreen
      and not cmdLineOptions.listScreens):
    parser.error("A command to run must be given on the command line")

  if (cmdLineOptions.exitScreen and cmdLineOptions.listScreens):
    parser.error("Cannot specify both --exitScreen and --listScreens")

  if (len(cmdLineArgs) != 0
      and (cmdLineOptions.exitScreen or cmdLineOptions.listScreens)):
    parser.error("Cannot specify the commnd to run '%s' on the command line "
                 % cmdLineArgs[0] +\
                 "when either --exitScreen or --listScreens are given")

  return (cmdLineOptions, cmdLineArgs)

def main(cmdLineArgs):
  (clo, cla) = setupCmdLineArgs(cmdLineArgs)

  command = ""
  if not clo.exitScreen and not clo.listScreens:
    command = cla[0]

  if clo.verbose:
    print("clo.verbose      =", clo.verbose        )
    print("clo.noOp         =", clo.noOp           )
    print("forceExecution    =", clo.forceExecution)
    print("clo.screenName   =", clo.screenName     )
    print("clo.sleepSeconds =", clo.sleepSeconds   )
    print("clo.noLoop       =", clo.noLoop         )
    print("clo.exitScreen   =", clo.exitScreen     )
    print("command          = '%s'" % command      )
    print("clo.argumentList =", clo.argumentList   )

  if clo.listScreens:
    if clo.noOp:
      print("Would be listing all running screens")
    else:
      screenList = TalkToScreen.getScreenList()
      print(screenList)
      
    return

  if clo.noOp:
    print("Would be creating TalkToScreen object using name '%s'" % clo.screenName)
  else:
    screen = TalkToScreen.createWithName(clo.screenName)

  if clo.exitScreen:
    if clo.noOp:
      print("Would be exiting screen with name '%s'" % clo.screenName)
    else:
      screen.exitScreen()
      
    return

  if clo.noOp:
    screenRunning = False # Just choose this value for noOp
  else:
    screenRunning = screen.screenAlreadyRunning()

  if not clo.noOp :
    if not clo.forceExecution:
      if screenRunning:
        print("Screen with name '%s' already running.  Exiting..." % clo.screenName, 
              file=sys.stderr)
        return

  if not screenRunning:
    if clo.noOp:
      print("Would be starting screen with name '%s'" % clo.screenName)
    else:
      if clo.verbose:
        print("Starting screen with name '%s'" % clo.screenName)
      screen.startScreen()

  command = command
  if clo.argumentList:
    command +=  " " + " ".join(clo.argumentList)

  cmdList = []
  if clo.noLoop:
    cmdList.append("date")
    cmdList.append(command)
  else:
    cmdList.append("cd '%s'" % execDir)
    cmdList.append("while :; do")
    cmdList.append("date")
    cmdList.append(command)
    cmdList.append("echo 'Sleeping for %s seconds (Ctrl-c to exit)...'"
                   % clo.sleepSeconds)
    cmdList.append("sleep %s" % clo.sleepSeconds)
    cmdList.append("done")

  for cmd in cmdList:
    if clo.noOp:
      print("Would be executing the following in screen '%s':\n" \
            % clo.screenName, cmd)
    else:
      if clo.verbose:
        print("Executing the following command in screen '%s':\n" \
              % clo.screenName, cmd)
        screen.executeCmdInScreen(cmd)

if (__name__ == '__main__'):
  main(sys.argv[1:])
