import os
import cgi
import urllib
import time
import socket
import subprocess
import sys
import struct
import time
import os.path
import re
import pprint

'''
Convert seconds (from the epoch) to a desired date format
'''
def toDate(secs):
    return time.strftime("%d%b%Y",time.localtime(secs))

'''
Process all the files in the Chart Data folder

Display file change/mod dates as well as first and last time stamps from the file
Compute the "age" of the file in number of days since last time stamp
Ignore "MetaDataCache" files (but count them)

'''
def ScanChartDataFolder(chartdir, outfile):
    #================================================================================
    # List of all the files, total count of files and folders & Total size of files.
    # http://mayankjohri.wordpress.com/2008/07/02/create-list-of-files-in-a-dir-tree/
    #================================================================================

    fileList = []
    fileSize = 0
    folderCount = 0
    emptyCount = 0
    cachesize = 0
    cachecount = 0
    inactivecount = 0
    inactivesize = 0
    newestfile = 0

    # sys.path.append(os.path.join(pd, "YOUR-MODULE")) # insert the directory into the sys.path variable
    # rootdir = "/Library/Application Support/InterMapper Settings/Chart Data.noindex"

    for root, subFolders, files in os.walk(chartdir):
        folderCount += len(subFolders)
        for file in files:
            fpath = os.path.join(root,file)                 # fp is a file path
            fileSize += os.path.getsize(fpath)
            fname = os.path.split(fpath)[1]
            if (fname == "MetaDataCache"):                  # count, but ignore MetaDataCache files
                cachesize += os.path.getsize(fpath)
                cachecount += 1
            elif (fname[0:2] == "._"):                      # ignore files with ._ prefix
                continue
            elif (fname[0:15] == "ChartDataSurvey"):        # ignore any of our ChartDataSurvey files
                continue
            else:
                fileList.append(fpath)                      # collect a list of paths of chart data files
                if (os.path.getmtime(fpath) > newestfile):
                    newestfile = os.path.getmtime(fpath)    # remember the newest file mod date

    # print ("Newest: %d, %s") % (newestfile, toDate(newestfile))

    for fp in fileList:                                     # scan the files looking for evidence of big/little endian-ness
        if (fp[-4:] == "RtyB"):                             # Only need to find one - usually won't have to look at very many
            byteorder = "<i"                                # little endian
            break
        elif (fp[-4:] == "BytR"):
            byteorder = ">i"                                # big endian
            break

    fileStats = []          # Formatted info about each file
    for fp in fileList:
        filename = os.path.split(fp)[1]
        dirname = os.path.split(os.path.dirname(fp))[1]
        chtime  = toDate(os.path.getctime(fp))
        modtime = toDate(os.path.getmtime(fp))
        flen = os.path.getsize(fp)
        if (flen <= 0):
            emptyCount += 1
            first = "-"
            last = "-"
            inactive = "-"
        else:
            f = open(fp, "rb")
            firstsec = struct.unpack(byteorder,f.read(4))[0]
            first = toDate(firstsec)
            eof = (flen-8)/8
            eof = eof*8
            f.seek(eof)
            lastsec = struct.unpack(byteorder,f.read(4))[0]
            last = toDate(lastsec)
            if (eof+8 != flen):
                last+="::"+str(flen%8)
            lastsec = lastsec/(3600*24)
            now = newestfile/(3600*24)
            if (now - lastsec > 30):                    # no data within last N days? treat as inactive
                inactive = str(int(now-lastsec))
                inactivecount += 1
                inactivesize += flen
            else:
                inactive = "-"
            f.close()
        outstr = dirname + "\t" + filename + "\t" + str(flen) + "\t" + chtime + "\t" + modtime + "\t" + first + "\t" + last + "\t" + inactive

        fileStats.append(outstr)

    retstr = ""
    retstr += "Chart Data Survey: %s\n" % (time.strftime("%d%b%Y-%H:%M"))
    retstr += "Data Files: %d contining %d bytes\n" % (len(fileList), fileSize)
    retstr += "Inactive files: %d containing %d bytes\n" % (inactivecount, inactivesize)
    retstr += "Cache files: %d containing %d bytes\n" % (cachecount, cachesize)
    retstr += "Empty Files: %d\n" % (emptyCount)
    retstr += "Total Folders: %d\n" % (folderCount)

    outfile.write(retstr)
    outfile.write("Map      \tDatapoint\tLength\tcTime    \tmTime    \tFirst   \tLast    \tDays Idle\n")

    for line in fileStats:
        outfile.write(line + "\n")
    return retstr

def main(argv=None):

### Get the first argument that was passed into the script
    args = sys.argv[1:]                      # retrieve the arguments
    if len(args) == 0:                       # handle missing argument
        chartdir = ""
    else:
        chartdir = args[0]
        # print "Arg is: '%s'" % arg            # debugging - comment out

    ##### Read one line from stdin (that's all that will be passed in)
    #    f = sys.stdin                            # open stdin
    #    stdinstr = f.readline().strip()          # get the line & remove leading & trailing whitespace
    #    stdinstr = "stdin contains '%s'" % stdinstr
    # print stdinstr                         # debugging - comment out
    stdinstr = ""

    wd = os.getcwd()                    # Get path of working directory of the script (InterMapper Settings/Tools/your.domain.your.package)
    if (chartdir == ""):                # no chart directory specified
        (toolsd, rem) = os.path.split(wd)   # split off the parent directory - this yields the path to the "Tools" directory
        (imdir, rem) = os.path.split(toolsd) # imdir is path to InterMapper Settings directory
        chartdir = os.path.join(imdir, "Chart Data")
        if (not os.path.exists(chartdir)):
            chartdir = chartdir + ".noindex"
        outfiledir = os.path.join(imdir, "Extensions")
    else:
        outfiledir = chartdir           # just put the ChartDataSurvey file in the chart directory

    datestamp = "ChartDataSurvey-" + toDate(time.time()) + ".txt"
    outfile = open(os.path.join(outfiledir,datestamp), 'w')
    retstr = ScanChartDataFolder(chartdir, outfile)
    outfile.close()

    ### Set the return value from the script
    ### Choices are: OK, Warn, Alarm, Critical, Down
    # argl = arg.lower()                       # allow upper/lowercase severity
    argl = "ok"
    if argl == "ok":
        returnval = 0
    elif argl == "warn":
        returnval = 1
    elif argl == "alarm":
        returnval = 2
    elif argl == "critical":
        returnval = 3
    elif argl == "down":
        returnval = 4
    else:
        returnval = 3
    # severity = "Severity is '%s'; " % arg

    ### Print a line to stdout with variables ($val1 & $val2) as well as the condition string
    print "\{ $val1 := '%s' }%s%s" % (datestamp,retstr, stdinstr)
    #print "Done!

    ### Return value from this function sets the script's exit code
    return returnval

if __name__ == "__main__":
    sys.exit(main())
