# mySosh

This tool is used to retrieve information about usage of SOSH mobile phones.
Both Internet, Voice and Extra Balance information can be retrieved.

This tool can run in two modes:
- A command-line tool,
- A RESTFul server (using the "-s" flag).

My typical usage is to get the data usage for all my SOSH contracts and monitor them
in Home Assistant.

How to use:
After installation, simply run the script "mySosh.py" without any argument or with "-h" to get the help usage, e.g.:
python mySosh.py -h

At the very first run, the script will ask for your credentials to connect at https://www.sosh.fr
Provide your username and password as on the web interface.

Then, you can use the script to get information for a single phone number:
- python mySosh.py 06.01.02.03.04

Or for all your phone numbers:
- python mySosh.py all

A Verbose mode is available using "-v" flag.

Information about Internet can be retrieved using the "-i" flag. This flag is 'True' by default.
Information about extra balance can be retrieved using the "-e" flag.
Information about voice calls can be retrieved using the "-c" flag.

A local cache file is managed by the tool (use "-C") which could be used to get 'locally available' data w/o connecting to the server.
Warning: Local information may be outdated.

A RESTful server can be started (localhost:5000) using the "-s" flag.
A mySosh-ws.service file is provided to allow running the tool through systemctl.

Use: "python mySosh.py init" to re-init your configuration file containing your credentials (or simply delete the file config.py)

This tool has been tested with python3 only.
