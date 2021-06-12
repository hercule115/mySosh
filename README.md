# mySosh
Command-line tool to retrieve information about usage of SOSH mobile phones

My typical usage is to get the data usage for all my SOSH contracts and monitor them
in Home Assistant.

How to use:
After installation, simply run the script "mySosh.py" without any argument or with "-h" to get the help usage, e.g.:
python3 mySosh.py -h

At the very first run, the script will ask for your credentials to connect at https://www.sosh.fr
Provide your username and password as on the web interface.

Then, you can use the script to get information for a single phone number:
- python mySosh.py 06.01.02.03.04

Or for all your phone numbers:
- python mySosh.py all

Verbose mode is available (use "-v")

Information about extra balance can be retrieved using the "-e" flag.

A local cache file is managed by the tool (use "-c") which could be used to get 'locally available' data w/o connecting to the server.
Warning: Local information may be outdated.

Use: "python mySosh.py init" to re-init your configuration file containing your credentials (or simply delete the file config.py)
