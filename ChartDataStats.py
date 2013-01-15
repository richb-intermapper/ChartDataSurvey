import os
import time
import sys
import struct
import getopt


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
def ScanChartDataFolder(chartdir, outfile, brief):
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

    def check(arg):
        """Return the argument as a string if it exists. If not, return None. Used to type cast input from InterMapper."""
        if arg == '' or arg is None: #InterMapper puts spaces in for blank values
            return None
        else:
            return str(arg) #explicitly type-cast

### Get the first argument that was passed into the script
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:b:", ["charts=", "brief="])
    except getopt.GetoptError, e:
        print "ChartDataSurvey.p [--charts='directorypath'] [--brief=1]"
        sys.exit(1)

    chartdir = ""
    brief = False
    for o,a in opts:
        if o in ("-c", "--charts"):
            chartdir = check(a)
        elif o in ("-b", "--brief"):
             if (check(a) and a == "1"):
                brief = True

    wd = os.getcwd()                            # Get path of working directory of the script (InterMapper Settings/Tools/your.domain.your.package)
    if (chartdir == ""):                        # no chart directory specified
        (toolsd, rem) = os.path.split(wd)       # split off the parent directory - this yields the path to the "Tools" directory
        (imdir, rem) = os.path.split(toolsd)    # imdir is path to InterMapper Settings directory
        chartdir = os.path.join(imdir, "Chart Data")
        if (not os.path.exists(chartdir)):
            chartdir = chartdir + ".noindex"
        outfiledir = os.path.join(imdir, "Extensions")
    else:
        outfiledir = chartdir           # just put the ChartDataSurvey file in the chart directory

    datestamp = "ChartDataSurvey-" + toDate(time.time()) + ".txt"
    outfile = open(os.path.join(outfiledir,datestamp), 'w')
    retstr = ScanChartDataFolder(chartdir, outfile, brief)
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
    print "\{ $val1 := '%s' }%s" % (datestamp,retstr)
    #print "Done!

    ### Return value from this function sets the script's exit code
    return returnval

if __name__ == "__main__":
    sys.exit(main())
