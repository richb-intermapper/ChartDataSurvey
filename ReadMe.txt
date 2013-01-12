This InterMapper command-line probe collects survey information
about the chart data files of an InterMapper server, as well as aging information about each
chart data file. It collects the information, and dumps it to a file with this tab-delimited format:

map-ID chart-ID os-creation-date os-last-modified first-timestamp last-timestamp file-size

The probe runs the command-line program and saves the data to the InterMapper Settings/Temporary folder.
The status window shows the name of the saved file, and has a URL that allows it to be retrieved
using a web browser.

The probe has a built-in poll_interval of one million seconds (about 11.5 days), although Cmd/Ctl-K
will reprobe it.

The output filename has this format: CharDataFiles-ddMMMyyyyhhmm

The program scans the entire "Chart Data" folder ("Chart Data.noindex" on OSX) and does a depth-first
traversal of the file system. There are only two levels of hierarchy: the Chart Data folder holds
folders with the "graph ID" of a map (the "map-ID" above); Each of the folders holds zero or more
chart data files that contain the data samples.

Chart data files have entries that consist of a four-byte time stamp (in seconds since the epoch)
and a four-byte data value. This program finds the first-timestamp at offset zero in the file, and
the last-timestamp at the offset EOF-8.