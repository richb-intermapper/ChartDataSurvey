# Chart Data Survey for InterMapper

There are three interesting files here:

* ChartDataStats.py - a Python program that scans a named Chart Data folder,
and displays the creation date/data last modified for all charts present, 
the size of each of the files,
and the time stamps of the first and last data value contained within the chart data file.

* com.dartware.chartdatasurvey.txt - an InterMapper probe that a customer can import
to scan their Chart Data folder. 
This probe invokes the ChartDataStats.py program as a command-line, then saves the output in the
Extensions folder so that it can be retrieved via the HTTP API.

* Sample ChartDataSurvey-28Mar2013.txt - a sample output file showing the data that's displayed.

## Background

This InterMapper command-line probe collects survey information
about the chart data files of an InterMapper server, as well as aging information about each
chart data file. It collects the information, and dumps it to a file with this tab-delimited format:

map-ID chart-ID file-size os-creation-date os-last-modified first-timestamp last-timestamp inactive-time

The probe runs the command-line program and saves the data to the InterMapper Settings/Temporary folder.
The status window shows the name of the saved file, and has a URL that allows it to be retrieved
using a web browser.

The probe has a built-in poll_interval of six hours, although Cmd/Ctl-K will reprobe it immediately

The output filename has this format: CharDataFiles-ddMMMyyyy.txt, and will be saved in the
InterMapper Settings/Extensions folder. Its URL will be:

http://im-server-info:port/~files/extensions/CharDataFiles-ddMMMyyyy.txt

The program scans the entire "Chart Data" folder ("Chart Data.noindex" on OSX) and does a depth-first
traversal of the file system. There are only two levels of hierarchy: the Chart Data folder holds
folders with the "graph ID" of a map (the "map-ID" above); Each of the folders holds zero or more
chart data files that contain the data samples.

Chart data files have entries that consist of a four-byte time stamp (in seconds since the epoch)
and a four-byte data value. This program finds the first-timestamp at offset zero in the file, and
the last-timestamp at the offset EOF-8.
