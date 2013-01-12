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

def toDate(secs):
    return time.strftime("%d%b%Y",time.localtime(secs))

def ScanChartDataFolder(outfile):
    #================================================================================
    # List of all the files, total count of files and folders & Total size of files.
    # http://mayankjohri.wordpress.com/2008/07/02/create-list-of-files-in-a-dir-tree/
    #================================================================================

    fileList = []
    fileSize = 0
    folderCount = 0
    emptyCount = 0
    rootdir = "/Library/Application Support/InterMapper Settings/Chart Data.noindex"

    for root, subFolders, files in os.walk(rootdir):
        folderCount += len(subFolders)
        for file in files:
            fp = os.path.join(root,file)                # fp is a file path
            fileSize = fileSize + os.path.getsize(fp)
            if (os.path.getsize(fp) == 0):
                emptyCount += 1
            elif (os.path.split(fp)[1] == "MetaDataCache"):
                continue
            else:
                fileList.append(fp)                     # collect a list of non-empty paths

    outfile.write("Total Size is {0} bytes".format(fileSize) + "\n")
    outfile.write("Data Files "+ str(len(fileList)) + "\n")
    outfile.write("Empty Files "+ str(emptyCount) + "\n")
    outfile.write("Total Folders "+ str(folderCount) + "\n")
    outfile.write("Map      \tDatapoint\tLength\tcTime    \tmTime    \tFirst  \tLast" + "\n")

    for fp in fileList:
        filename = os.path.split(fp)[1]
        dirname = os.path.split(os.path.dirname(fp))[1]
        chtime  = toDate(os.path.getctime(fp))
        modtime = toDate(os.path.getmtime(fp))
        flen = os.path.getsize(fp)

        f = open(fp, "rb")
        first = toDate(struct.unpack("i",f.read(4))[0])
        eof = (flen-8)/8
        eof = eof*8
        f.seek(eof)
        last = toDate(struct.unpack("i",f.read(4))[0])
        if (eof+8 != flen):
            last+="::"+str(flen%8)
        f.close()
        # first = "123"
        #last = "9876"
        outstr = dirname + "\t" + filename + "\t" + str(flen) + "\t" + chtime + "\t" + modtime + "\t" + first + "\t" + last

        outfile.write(outstr + "\n")



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
    print "\{ $val1 := 1, $val2 := 'abcdef' }%s%s" % (severity, stdinstr)

    ### Return value from this function sets the script's exit code
    return returnval

if __name__ == "__main__":
    sys.exit(main())
