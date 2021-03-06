# ChartDataStats.py
#
# Scan an InterMapper Settings folder to find all the chart data files
# Categorize them by their filesystem dates as well as internal time stamps
# Correlate with the current Maps folder (stub: Maps/5.6 folder) to determine
#    if the charts are associated with enabled, disabled, or deleted maps
# Write a tab-delimited file that gives info about all the files
#
# January 2013 -reb

import os
import time
import sys
import struct
import getopt
import socket


def toDate(secs):
    """
    Convert seconds (from the epoch) to a desired date format
        If time cannot be converted (wrong byte order?) just return "odd-time"
    """
    try:
        return time.strftime("%d%b%Y",time.localtime(secs))
    except:
        return "odd-time"

def GetMyIPAddr():
    '''
    GetMyIPAddr() - return a valid IPv4 address
        First try to connect to Google, and use the resulting local address
        If that fails, sort through the IPv4 addresses returned by gethostname() and returns the first
        Found at: http://www.linux-support.com/cms/get-local-ip-address-with-python/
            and other sites
    '''

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('www.google.com', 8000))
        myIPadrs = s.getsockname()[0]
        s.close()
    except:
        addrList = socket.getaddrinfo(socket.gethostname(), None)
        myList=[]
        for item in addrList:
            if (item[0] == 2):		        # "2" indicates IPv4 address
                myList.append(item[4][0])
        myList = sorted(set(myList))        # now list holds unique addresses
        myIPadrs = myList[0]

    return myIPadrs

def findChartDir(dir):
    '''
    findChartDir - given the IM settings path, return a path to the Chart Data directory
    '''
    chartdir = os.path.join(dir, "Chart Data")
    if (not os.path.exists(chartdir)):
        chartdir = chartdir + ".noindex"
    return chartdir

def findMapsDir(dir):
    '''
    findMapsDir - return the path the the current IM version's Maps folder (containing Enabled & Disabled folders)
    '''
    maps = os.path.join(dir, "Maps")
    return os.path.join(maps, "5.6")        # stub - needs to find newest #.# directory (ignoring deleted & backup)

def enabledState(filename, enabledMaps, disabledMaps):
    '''
    enabledState() - return the customer's map name, as well as whether it's enabled or disabled.
        If not in either list, assume it's deleted, and return its original mapname/gid.
    '''
    mapname = enabledMaps.isInDir(filename)
    if (mapname != ""):
        return (mapname, "-")
    mapname = disabledMaps.isInDir(filename)
    if (mapname != ""):
        return (mapname, "Disabled")
    return (filename, "Deleted")

class mapDir():
    '''
    mapDir - return the customer's "map name" if the str matches the prefix of one of the file in dir
        Return "" if it doesn't match the gxxxxxxxx- prefix
        Used to scan the Maps/Enabled or Maps/Disabeled folders
    '''

    def __init__(self, theDir):
        self.paths = []
        self.lastmatch = ""
        self.lastname = ""
        for root, subFolders, files in os.walk(theDir):
            for file in files:
                self.paths.append(file)

    def isInDir(self, gid):
        if (gid == self.lastmatch):         # if they asked the same question...
            return self.lastname            # give the same answer
        for file in self.paths:
            if (file.find(gid) == 0):       # found the name at first position
                self.lastmatch = gid
                self.lastname = file[len(gid)+1:]
                return self.lastname
        else:
            return ""

def ScanChartDataFolder(chartdir, mapdir, outfile, brief, inactivedays):
    '''
    Process all the files in the Chart Data folder

    Display file change/mod dates as well as first and last time stamps from the file
    Compute the "age" of the file in number of days since last time stamp
    Ignore "MetaDataCache" files (but count them)

    '''
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
    deletedcount = 0
    deletedsize = 0
    newestfile = 0
    enabledMaps = mapDir(os.path.join(mapdir, "Enabled"))
    disabledMaps = mapDir(os.path.join(mapdir, "Disabled"))

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
            elif (fname == ".DS_Store"):                    # ignore MacOSX .DS_Store files
                continue
            elif (fname[0:15] == "ChartDataSurvey"):        # ignore any of our ChartDataSurvey files
                continue
            else:
                fileList.append(fpath)                      # collect a list of paths of chart data files
                if (os.path.getmtime(fpath) > newestfile):
                    newestfile = os.path.getmtime(fpath)    # remember the newest file mod date
        # print ("Newest: %d, %s") % (newestfile, toDate(newestfile))

    # Figure out whether the files are big-endian or little-endian
    for fp in fileList:                                     # scan the files looking for evidence of big/little endian-ness
        if (fp[-4:] == "RtyB"):                             # Only need to find one - usually won't have to look at very many
            byteorder = "<i"                                # little endian
            break
        elif (fp[-4:] == "BytR"):
            byteorder = ">i"                                # big endian
            break

    # Scan each file to collect its information
    fileStats = []          # Formatted info about each file
    for fp in fileList:
        filename = os.path.split(fp)[1]
        dirname = os.path.split(os.path.dirname(fp))[1]
        chtime  = toDate(os.path.getctime(fp))
        modtime = toDate(os.path.getmtime(fp))
        flen = os.path.getsize(fp)
        # print "%s %s" % (dirname, filename)
        (dirname, mapState) = enabledState(dirname, enabledMaps, disabledMaps)
        if (mapState == "Deleted"):
            deletedcount += 1
            deletedsize += flen
        if (flen <= 0):
            emptyCount += 1
            first = "-"
            last = "-"
            inactive = "-"
        elif (brief):                                   # if brief, don't open the file
            first = "-"
            last = "-"
            inactive = "-"
        else:                                           # otherwise, open the file and get its info
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
            if (now - lastsec > inactivedays):          # no data within last N days? treat as inactive
                inactive = str(int(now-lastsec))
                inactivecount += 1
                inactivesize += flen
            else:
                inactive = "-"
            f.close()
        outstr = dirname + "\t" + filename + "\t" + mapState  + "\t" + str(flen) + "\t" + chtime + "\t" + modtime + "\t" + first + "\t" + last + "\t" + inactive

        fileStats.append(outstr)

    retstr = ""
    retstr += "Chart Data Survey for %s on %s\n" % (GetMyIPAddr(), time.strftime("%d%b%Y-%H:%M"))
    retstr += "%d Chart Files containing %d bytes\n" % (len(fileList), fileSize)
    retstr += "%d Chart files containing %d bytes associated with deleted maps \n" % (deletedcount, deletedsize)
    retstr += "%d Inactive files containing %d bytes with no new data for %d days\n" % (inactivecount, inactivesize, inactivedays)
    #    retstr += "Cache files: %d containing %d bytes\n" % (cachecount, cachesize)
    retstr += "%d Empty files\n" % (emptyCount)
    retstr += "%d Total maps\n" % (folderCount)

    outfile.write(retstr)
    outfile.write("Map      \tDatapoint\tState\tLength\tcTime    \tmTime    \tFirst   \tLast    \tDays Idle\n")

    for line in fileStats:
        outfile.write(line + "\n")
    return retstr

def main(argv=None):

    def check(arg):
        """Return the argument as a string if it exists. If not, return None. Used to type cast input from InterMapper."""
        if arg == '' or arg is None: #InterMapper puts spaces in for blank values
            return None
        else:
            return str(arg) #explicitly type-cast

        ### Get the first argument that was passed into the script
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:b:", ["settings=", "brief="])
    except getopt.GetoptError, e:
        print "ChartDataSurvey.p [--settings 'IM-Settings-Path'] [--brief=1]"
        sys.exit(1)

    settingsdir = ""
    brief = False
    for o,a in opts:
        if o in ("-s", "--settings"):
            settingsdir = check(a)
        elif o in ("-b", "--brief"):
            if (check(a) and a == "1"):
                brief = True

    if (settingsdir == ""):                     # no chart directory specified, so we're running from Tools directory
        wd = os.getcwd()                        # Get path of working directory of the script (InterMapper Settings/Tools/your.domain.your.package)
        (toolsd, rem) = os.path.split(wd)       # split off the parent directory - this yields the path to the "Tools" directory
        (settingsdir, rem) = os.path.split(toolsd)    # settingsdir is path to InterMapper Settings directory
        outfiledir = os.path.join(settingsdir, "Extensions")
        chartdir = findChartDir(settingsdir)
    else:                                       # argument supplied the IM settings directory
        chartdir = findChartDir(settingsdir)
        outfiledir = os.getcwd()                # Output the results to the current working directory

    mapdir = findMapsDir(settingsdir)
    outfilename = "ChartDataSurvey-%s.txt" % (toDate(time.time()))
    outfile = open(os.path.join(outfiledir,outfilename), 'w')
    retstr = ScanChartDataFolder(chartdir, mapdir, outfile, brief, 30)
    retstr += "Use the web interface to retrieve the results at ~files/extensions/%s" % (outfilename)
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

    ### Print a line to stdout with variables
    print "\{ $val1 := '%s' }%s" % (outfilename,retstr)
    #print "Done!

    ### Return value from this function sets the script's exit code
    return returnval

if __name__ == "__main__":
    sys.exit(main())
