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
def ScanChartDataFolder(outfile):
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
    rootdir = "/Library/Application Support/InterMapper Settings/Chart Data.noindex"

    for root, subFolders, files in os.walk(rootdir):
        folderCount += len(subFolders)
        for file in files:
            fpath = os.path.join(root,file)                # fp is a file path
            fileSize = fileSize + os.path.getsize(fpath)
            if (os.path.split(fpath)[1] == "MetaDataCache"):
                cachesize += os.path.getsize(fpath)
                cachecount += 1
            else:
                fileList.append(fpath)                     # collect a list of non-empty paths

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
            firstsec = struct.unpack("i",f.read(4))[0]
            first = toDate(firstsec)
            eof = (flen-8)/8
            eof = eof*8
            f.seek(eof)
            lastsec = struct.unpack("i",f.read(4))[0]
            last = toDate(lastsec)
            if (eof+8 != flen):
                last+="::"+str(flen%8)
            lastsec = lastsec/(3600*24)
            now = time.time()/(3600*24)
            if (now - lastsec > 120):
                inactive = str(int(now-lastsec))
                inactivecount += 1
                inactivesize += flen
            else:
                inactive = "-"
            f.close()
        outstr = dirname + "\t" + filename + "\t" + str(flen) + "\t" + chtime + "\t" + modtime + "\t" + first + "\t" + last + "\t" + inactive

        fileStats.append(outstr)

    outfile.write("Data Files: %d contining %d bytes\n" % (len(fileList), fileSize))
    outfile.write("Inactive files: %d containing %d bytes\n" % (inactivecount, inactivesize) )
    outfile.write("Cache files: %d containing %d bytes\n" % (cachecount, cachesize) )
    outfile.write("Empty Files: %d\n" % (emptyCount) )
    outfile.write("Total Folders: %d\n" % (folderCount))
    outfile.write("Map      \tDatapoint\tLength\tcTime    \tmTime    \tFirst   \tLast    \tDays Idle\n")

    for line in fileStats:
        outfile.write(line + "\n")


def main(argv=None):

### Get the first argument that was passed into the script
    args = sys.argv[1:]                      # retrieve the arguments
    if len(args) == 0:                       # handle missing argument
        arg = "First argument missing"
    else:
        arg = args[0]
        # print "Arg is: '%s'" % arg            # debugging - comment out

    ##### Read one line from stdin (that's all that will be passed in)
    #    f = sys.stdin                            # open stdin
    #    stdinstr = f.readline().strip()          # get the line & remove leading & trailing whitespace
    #    stdinstr = "stdin contains '%s'" % stdinstr
    # print stdinstr                         # debugging - comment out
    stdinstr = ""

    outfile = open('/tmp/workfile', 'w')
    ScanChartDataFolder(outfile)
    outfile.close()

    ### Set the return value from the script
    ### Choices are: OK, Warn, Alarm, Critical, Down
    argl = arg.lower()                       # allow upper/lowercase severity
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
    severity = "Severity is '%s'; " % arg

    ### Print a line to stdout with variables ($val1 & $val2) as well as the condition string
    #print "\{ $val1 := 1, $val2 := 'abcdef' }%s%s" % (severity, stdinstr)
    print "Done!"

    ### Return value from this function sets the script's exit code
    return returnval

if __name__ == "__main__":
    sys.exit(main())
