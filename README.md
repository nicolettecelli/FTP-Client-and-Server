# FTP Client & Server
The following is an implementation of an FTP client and server in Python3.


## Getting Started
Make sure you have Python3 installed on your machine.

Open 2 separate terminal windows
On one, type the following to run the server:
```
python ftp_server.py
```

On the other, type the following to run the client:
```
python ftp_client.py
```

Open your connection by typing:
```
>open [hostname]
```
or
```
>ftp
```

Use the following credentials to login as an admin:
```
Username: user1
Password: pass1
```

Type `help` or `?` to display the list of client commands.


## Server Configuration
The server configuration is located in `/ftpserver/conf/sys.cfg` and has the following format:

```
FTP_ROOT ftpserver/ftproot
USER_DATA_PATH ftpserver/conf/users.cfg
FTP_MODE ACTIVE
DATA_PORT_FTP_SERVER 2028
FTP_ENABLED 1
MAX_USER_SUPPORT 200
FTP_LOG_PATH ftpserver/log/client.log
SERVICE_PORT 2143
```

## Client Configuration
The client configuration is located in `ftp_client.cfg` and has the following format:

```
DATA_PORT_MAX 6999
DATA_PORT_MIN 6500
DEFAULT_FTP_PORT 2028
DEFAULT_MODE Active
DEFAULT_DEBUG_MODE false
DEFAULT_VERBOSE_MODE false
DEFAULT_TEST_FILE tests/test1.txt
DEFAULT_LOG_FILE ftpserver/log/client.log
```

## User Configuration
The user configuration is located in `/ftpserver/conf/users.cfg` and has the following format:

```
user1 pass1 admin
user2 pass2 user
user3 pass3 notallowed
user4 pass4 locked
```
There are only 4 users in the system. To create another user, add a new line to this file with the following format:

```
username password type
```

## Usage
The client and server can run with no arguments. However, add `--help` to see the following information:

```
usage: python3 ftp [-h] [-hn HN] [-u USER] [-w W] [-fp FP] [-p] [-a] [-D] [-V]
                   [-dpr DPR] [-c CONFIG] [-t T] [-T T] [-L LOG] [-LALL LALL]
                   [-LONLY LONLY] [-v] [-info]

optional arguments:
  -h, --help            show this help message and exit
  -hn HN                hostname
  -u USER, --user USER  username
  -w W                  password
  -fp FP                FTP ftpserver port
  -p, --passive         passive
  -a, --active          active
  -D, --debug           debug mode on/off
  -V, --verbose         verbose for additional output
  -dpr DPR              data port range
  -c CONFIG, --config CONFIG
                        configuration file
  -t T                  run test file
  -T T                  run default test file
  -L LOG, --log LOG     log messages
  -LALL LALL            log all output to log file and screen
  -LONLY LONLY          log all output to a log file
  -v, --version         print version number of client
  -info                 prints info about the student and FTP client
```
