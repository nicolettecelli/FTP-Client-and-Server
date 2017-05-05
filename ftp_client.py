
from socket import *
import os
import sys
import argparse
import getpass
import distutils.util


RECV_BUFFER = 1024

CMD_APPEND = "APPEND"
CMD_ASCII = "ASCII"
CMD_BINARY = "BINARY"
CMD_BYE = "BYE"
CMD_CD = "CD"
CMD_CDUP = "CDUP"
CMD_CLOSE = "CLOSE"
CMD_DEBUG = "DEBUG"
CMD_DELETE = "DELETE"
CMD_DIR = "DIR"
CMD_DISCONNECT = "DISCONNECT"
CMD_EXIT = "EXIT"
CMD_FTP = "FTP"
CMD_GET = "GET"
CMD_HELP = "HELP"
CMD_IMAGE = "IMAGE"
CMD_LCD = "LCD"
CMD_LLS = "LLS"
CMD_LOGIN = "LOGIN"
CMD_LOGOUT = "LOGOUT"
CMD_LPWD = "LPWD"
CMD_LS = "LS"
CMD_MDELETE = "MDELETE"
CMD_MKDIR = "MKDIR"
CMD_NOOP = "NOOP"
CMD_OPEN = "OPEN"
CMD_PORT = "PORT"
CMD_PUT = "PUT"
CMD_PWD = "PWD"
CMD_QUIT = "QUIT"
CMD_RECV = "RECV"
CMD_RENAME = "RENAME"
CMD_RHELP = "RHELP"
CMD_RMDIR = "RMDIR"
CMD_SEND = "SEND"
CMD_SUNIQUE = "SUNIQUE"
CMD_TYPE = "TYPE"
CMD_USAGE = "USAGE"
CMD_USER = "USER"
CMD_VERBOSE = "VERBOSE"

parser = argparse.ArgumentParser(prog="python3 ftp_client")
parser.add_argument("-hn", help="hostname")
parser.add_argument("-u", "--user", default="", help="username")
parser.add_argument("-w", default="", help="password")
parser.add_argument("-fp", help="FTP ftpserver port")
parser.add_argument("-p", "--passive",  help="passive")
parser.add_argument("-a", "--active", help="active")
parser.add_argument("-D", "--debug", help="debug mode on/off")
parser.add_argument("-V", "--verbose", help="verbose for additional output")
parser.add_argument("-dpr", help="data port range")
parser.add_argument("-c", "--config", default="ftp_client.cfg", help="configuration file")
parser.add_argument("-t", help="run test file")
parser.add_argument("-T", help="run default test file")
parser.add_argument("-L", "--log", default="./ftpserver/log/client.log", help="log messages")
parser.add_argument("-LALL", default="store_false", help="log all output to log file and screen")
parser.add_argument("-LONLY", default="store_false", help="log all output to a log file")
parser.add_argument("-v", "--version", action="store_true", help="print version number of client")
parser.add_argument("-info", action="store_true", help="prints info about the student and FTP client")

args = parser.parse_args()

with open("ftp_client.cfg", "r") as config_file:
    data = config_file.read().split("\n")

DATA_PORT_MAX = int(data[0].split(" ")[1])
DATA_PORT_MIN = int(data[1].split(" ")[1])
FTP_PORT = int(data[2].split(" ")[1])
DEFAULT_MODE = data[3].split(" ")[1]
DEBUG_MODE = data[4].split(" ")[1]
VERBOSE_MODE = data[5].split(" ")[1]
TEST_FILE = data[6].split(" ")[1]
LOG_FILE = data[7].split(" ")[1]

config_file.close()

VERBOSE_MODE = distutils.util.strtobool(VERBOSE_MODE)
DEBUG_MODE = distutils.util.strtobool(DEBUG_MODE)

if args.t is not None:
    TEST_FILE = args.t
    run_test = True
else:
    run_test = False

config_file = args.config

if args.log is not None:
    LOG_FILE = args.log

log_all = args.LALL
log_only = args.LONLY
info = args.info
hostname = args.hn
username = args.user
password = args.w

if args.passive:
    print("Passive mode is not supported")

if args.active:
    print("Active mode is on")

if args.debug is not None:
    DEBUG_MODE = distutils.util.strtobool(args.debug)
    if DEBUG_MODE:
        print("Debugging mode on (debug=1)")
    else:
        print("Debugging mode off (debug=0)")

if args.verbose is not None:
    VERBOSE_MODE = distutils.util.strtobool(args.verbose)
    if VERBOSE_MODE:
        print("Verbose mode on")
    else:
        print("Verbose mode off")

if args.version:
    print("v1.0")
    sys.exit()

if args.info:
    print("FTP Client by Nicolette Celli 4174075")
    sys.exit()

DATA_PORT_BACKLOG = 1
next_data_port = 1

sunique = False
current_directory = os.getcwd()
base_directory = os.path.abspath("/")
set_type = "I"

def main():
    global username
    global password
    global hostname

    logged_on = False
    if username is None or password is None:
        logon_ready = False
    else:
        logon_ready = True

    ftp_socket = None
    if hostname is not None:
        ftp_socket = ftp_connecthost(hostname)
        msg = ftp_socket.recv(RECV_BUFFER)
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))

    if logon_ready and ftp_socket is not None:
        logged_on = login(username, password, ftp_socket)

    keep_running = True

    while keep_running:
        try:
            user_input = input("> ")

            if user_input is None or user_input.strip() == "":
                continue

            tokens = user_input.split()
            cmd_msg, logged_on, ftp_socket = run_commands(tokens, logged_on, ftp_socket)

            if cmd_msg != "":
                print(cmd_msg)

        except OSError as e:
            print("Socket error:", e)
            str_error = str(e)
            if str_error.find("[Errno 32]") >= 0:
                sys.exit()

    try:
        ftp_socket.close()
    except OSError as e:
        print("Socket error:", e)
    sys.exit()

def run_commands(tokens, logged_on, ftp_socket):
    global username
    global password
    global hostname
    global parser

    cmd = tokens[0].upper()

    if cmd == CMD_QUIT or cmd == CMD_BYE or cmd == CMD_EXIT:
        quit_ftp(logged_on, ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == "!":
        ftp_socket.close()
        sys.exit()
        return "", logged_on, ftp_socket

    if cmd == CMD_HELP or cmd == "?":
        help_ftp()
        return "", logged_on, ftp_socket

    if cmd == CMD_RHELP:
        rhelp_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_NOOP:
        noop_ftp(ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_PWD:
        pwd_ftp(ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_CD:
        cd_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_LCD:
        lcd_ftp(tokens)
        return "", logged_on, ftp_socket

    if cmd == CMD_LPWD:
        lpwd_ftp()
        return "", logged_on, ftp_socket

    if cmd == CMD_LLS:
        lls_ftp(tokens)
        return "", logged_on, ftp_socket

    if cmd == CMD_CDUP:
        cdup_ftp(ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_MKDIR:
        mkdir_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_RMDIR:
        rmdir_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_SUNIQUE:
        sunique_ftp()
        return "", logged_on, ftp_socket

    if cmd == CMD_DEBUG:
        debug_ftp()
        return "", logged_on, ftp_socket

    if cmd == CMD_VERBOSE:
        verbose_ftp()
        return "", logged_on, ftp_socket

    if cmd == CMD_RENAME:
        rename_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_ASCII:
        ascii_ftp(ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_IMAGE or cmd == CMD_BINARY:
        image_ftp(ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_APPEND:
        data_socket = ftp_new_dataport(ftp_socket)
        if data_socket is not None:
            append_ftp(tokens, ftp_socket, data_socket)
            return "", logged_on, ftp_socket
        else:
            return "[APPEND] Failed to get data port. Try again.", logged_on, ftp_socket

    if cmd == CMD_LS or cmd == CMD_DIR:
        data_socket = ftp_new_dataport(ftp_socket)
        if data_socket is not None:
            ls_ftp(tokens, ftp_socket, data_socket)
            return "", logged_on, ftp_socket
        else:
            return "[LS] Failed to get data port. Try again.", logged_on, ftp_socket

    if cmd == CMD_LOGIN or cmd == CMD_USER:
        logged_on = user_ftp(username, password, tokens, ftp_socket, hostname)
        return "", logged_on, ftp_socket

    if cmd == CMD_LOGOUT or cmd == CMD_CLOSE or cmd == CMD_DISCONNECT:
        logged_on, ftp_socket = logout(logged_on, ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_DELETE:
        delete_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_MDELETE:
        mdelete_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket

    if cmd == CMD_PUT or cmd == CMD_SEND:
        data_socket = ftp_new_dataport(ftp_socket)
        if data_socket is not None:
            put_ftp(tokens, ftp_socket, data_socket)
            return "", logged_on, ftp_socket
        else:
            return "[PUT] Failed to get data port. Try again.", logged_on, ftp_socket

    if cmd == CMD_GET or cmd == CMD_RECV:
        data_socket = ftp_new_dataport(ftp_socket)
        if data_socket is not None:
            get_ftp(tokens, ftp_socket, data_socket)
            return "", logged_on, ftp_socket
        else:
            return "[GET] failed to get data port. Try again.", logged_on, ftp_socket

    if cmd == CMD_USAGE:
        parser.print_help()
        return "", logged_on, ftp_socket

    if cmd == CMD_OPEN or cmd == CMD_FTP:
        logged_on, ftp_socket = open_ftp(tokens)
        return "", logged_on, ftp_socket

    if cmd == CMD_TYPE:
        type_ftp(tokens, logged_on, ftp_socket)
        return "", logged_on, ftp_socket

    return "Invalid command", logged_on, ftp_socket

def str_msg_encode(str_value):
    msg = str_value.encode()
    return msg

def str_msg_decode(msg, print_strip=False):
    str_value = msg.decode()
    if print_strip:
        str_value.strip('\n')
    return str_value

def open_ftp(tokens):
    global username
    global password
    global hostname

    if len(tokens) is 1:
        hostname = input("(to) ")
    else:
        hostname = tokens[1]

    ftp_socket = ftp_connecthost(hostname)
    msg = ftp_socket.recv(RECV_BUFFER)
    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))
    if str_msg_decode(msg).split()[0] == "530" and not VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True).replace("530 ", ""))

    logged_on = login(username, password, ftp_socket)

    return logged_on, ftp_socket

def ftp_connecthost(hostname):
    ftp_socket = socket(AF_INET, SOCK_STREAM)
    ftp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    ftp_socket.connect((hostname, FTP_PORT))

    print("Connected to " + hostname)

    return ftp_socket

def ftp_new_dataport(ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    global next_data_port

    data_port = next_data_port
    host = gethostname()
    host_address = gethostbyname(host)
    next_data_port += 1
    data_port = (DATA_PORT_MIN + data_port) % DATA_PORT_MAX

    data_socket = socket(AF_INET, SOCK_STREAM)
    data_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    data_socket.bind((host_address, data_port))
    data_socket.listen(DATA_PORT_BACKLOG)

    host_address_split = host_address.split('.')
    high_data_port = str(data_port // 256)
    low_data_port = str(data_port % 256)
    port_argument_list = host_address_split + [high_data_port, low_data_port]
    port_arguments = ','.join(port_argument_list)
    cmd_port_send = CMD_PORT + ' ' + port_arguments + "\r\n"

    try:
        if DEBUG_MODE:
            print("---> " + CMD_PORT + ' ' + port_arguments)
        ftp_socket.send(str_msg_encode(cmd_port_send))
    except socket.timeout:
        print("Socket timeout. Try again.")
        return None
    except OSError as e:
        print("Socket error. Try again.")
        return None

    msg = ftp_socket.recv(RECV_BUFFER)
    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))
    if str_msg_decode(msg).split()[0] == "530" and not VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True).replace("530 ", ""))

    if str_msg_decode(msg).split()[0] == "530":
        return None
    else:
        return data_socket

def noop_ftp(ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if DEBUG_MODE:
        print("---> NOOP")
    ftp_socket.send(str_msg_encode("NOOP\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    sys.stdout.write(str_msg_decode(msg, True))

def pwd_ftp(ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if DEBUG_MODE:
        print("---> PWD")
    ftp_socket.send(str_msg_encode("PWD\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    sys.stdout.write(str_msg_decode(msg, True))

def lcd_ftp(tokens):
    global current_directory
    global base_directory

    if len(tokens) is 2:
        local_directory = tokens[1]
    else:
        local_directory = ""

    if local_directory == "":
        print("Local directory now " + current_directory)
        return

    if local_directory == "/":
        current_directory = base_directory
        os.chdir(base_directory)
        print("Local directory now " + current_directory)
    elif local_directory == "..":
        if not os.path.samefile(current_directory, base_directory):
            current_directory = os.path.abspath(os.path.join(current_directory, ".."))
        print("Local directory now " + current_directory)
    elif local_directory[0] == "/":
        path = os.path.join(base_directory, local_directory[1:])

        if os.path.exists(path):
            current_directory = path
            os.chdir(path)
            print("Local directory now " + current_directory)
        else:
            print("local: " + local_directory[1:] + ": No such file or directory")
    else:
        path = os.path.join(current_directory, local_directory)

        if os.path.exists(path):
            current_directory = path
            os.chdir(path)
            print("Local directory now " + current_directory)
        else:
            print("local: " + local_directory + ": No such file or directory")

def lpwd_ftp():
    global current_directory

    print("Local directory now " + current_directory)

def lls_ftp(tokens):
    global current_directory

    if len(tokens) > 1:
        directory = tokens[1]
    else:
        directory = ""

    if directory != "":
        path = os.path.join(current_directory, directory)
        if os.path.exists(path):
            directory_list(path)
        else:
            print(directory + ": No such file or directory")

    directory_list(current_directory)

def directory_list(path):
    for item in os.listdir(path):
        print(item)

def cd_ftp(tokens, ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) is 1:
        remote_directory = input("(remote-directory) ")
    else:
        remote_directory = tokens[1]

    if DEBUG_MODE:
        print("---> " + "CWD " + remote_directory)
    ftp_socket.send(str_msg_encode("CWD " + remote_directory + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))
    if str_msg_decode(msg).split()[0] == "550" and not VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True).replace("550 ", ""))

def cdup_ftp(ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if DEBUG_MODE:
        print("---> CDUP")
    ftp_socket.send(str_msg_encode("CDUP\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))
    if str_msg_decode(msg).split()[0] == "530" and not VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True).replace("530 ", ""))

def mkdir_ftp(tokens, ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) is 1:
        directory_name = input("(directory-name) ")
    else:
        directory_name = tokens[1]

    if DEBUG_MODE:
        print("---> " + "MKD " + directory_name)
    ftp_socket.send(str_msg_encode("MKD " + directory_name + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)

    if str_msg_decode(msg).split()[0] == "501":
        print("usage: mkdir directory-name")
    else:
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))
        if str_msg_decode(msg).split()[0] == "550" and not VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True).replace("550 ", ""))
        if str_msg_decode(msg).split()[0] == "530" and not VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True).replace("530 ", ""))

def rmdir_ftp(tokens, ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) is 1:
        directory_name = input("(directory-name) ")
    else:
        directory_name = tokens[1]

    if DEBUG_MODE:
        print("---> " + "RMD " + directory_name)
    ftp_socket.send(str_msg_encode("RMD " + directory_name + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)

    response = str_msg_decode(msg)
    tokens = response.split()

    if tokens[0] == "501":
        print("usage: rmdir directory-name")
    else:
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))
        if str_msg_decode(msg).split()[0] == "550" and not VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True).replace("550 ", ""))
        if str_msg_decode(msg).split()[0] == "530" and not VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True).replace("530 ", ""))

def ascii_ftp(ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    global set_type
    set_type = "A"

    if DEBUG_MODE:
        print("---> TYPE A")
    ftp_socket.send(str_msg_encode("TYPE A\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

def image_ftp(ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    global set_type

    set_type = "I"

    if DEBUG_MODE:
        print("---> TYPE I")
    ftp_socket.send(str_msg_encode("TYPE I\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

def sunique_ftp():
    global sunique

    sunique = not sunique

    if sunique:
        print("Store unique on")
    else:
        print("Store unique off")

def debug_ftp():
    global DEBUG_MODE

    DEBUG_MODE = not DEBUG_MODE

    if DEBUG_MODE:
        print("Debugging on (debug=1)")
    else:
        print("Debugging off (debug=0)")

def verbose_ftp():
    global VERBOSE_MODE

    VERBOSE_MODE = not VERBOSE_MODE

    if VERBOSE_MODE:
        print("Verbose mode on")
    else:
        print("Verbose mode off")

def rename_ftp(tokens, ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) is 1:
        from_name = input("(from-name) ")

        if from_name is "":
            print("rename from-name to-name")
            return

        to_name = input("(to-name) ")

        if to_name is "":
            print("rename from-name to-name")
            return

    elif len(tokens) is 2:
        from_name = tokens[1]

        if from_name is "":
            print("rename from-name to-name")
            return

        to_name = input("(to-name) ")

        if to_name is "":
            print("rename from-name to-name")
            return

    elif len(tokens) is 3:
        from_name = tokens[1]
        to_name = tokens[2]
    else:
        from_name = tokens[1]
        to_name = tokens[2]

    if DEBUG_MODE:
        print("---> " + "RNFR " + from_name)
    ftp_socket.send(str_msg_encode("RNFR " + from_name + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)

    tokens = str_msg_decode(msg).split()

    if tokens[0] != "530":
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))

    if DEBUG_MODE:
        print("---> " + "RNTO " + to_name)
    ftp_socket.send(str_msg_encode("RNTO " + to_name + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)

    if str_msg_decode(msg).split()[0] == "550" and not VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True).replace("550 ", ""))
    if str_msg_decode(msg).split()[0] == "530" and not VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True).replace("530 ", ""))

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

def get_ftp(tokens, ftp_socket, data_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    global set_type

    if len(tokens) is 1:
        remote_file = input("(remote-file) ")
        local_file = input("(local-file) ")
    elif len(tokens) is 2:
        remote_file = tokens[1]
        local_file = remote_file
    else:
        remote_file = tokens[1]
        local_file = tokens[2]

    print("local: " + local_file + " remote: " + remote_file)

    if DEBUG_MODE:
        print("---> " + "RETR " + remote_file)
    ftp_socket.send(str_msg_encode("RETR " + remote_file + "\n"))

    msg = ftp_socket.recv(RECV_BUFFER)
    tokens = str_msg_decode(msg).split()

    if tokens[0] != "150":
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))
        return

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

    data_connection, data_host = data_socket.accept()

    file = open(local_file, get_file_mode("w"))
    size_recv = 0

    while True:
        file_data = data_connection.recv(RECV_BUFFER)

        if set_type == "A":
            try:
                file_data = file_data.decode()
            except UnicodeDecodeError:
                print("550 " + remote_file + " is an image. Please set file transfer mode to IMAGE")
                file.close()
                data_connection.close()
                break

        if not file_data or file_data == "" or len(file_data) <= 0:
            file.close()
            break

        if len(file_data) < RECV_BUFFER:
            file.write(file_data)
            size_recv += len(file_data)
            file.close()
            break
        file.write(file_data)

    data_connection.close()

    msg = ftp_socket.recv(RECV_BUFFER)
    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))
    if str_msg_decode(msg).split()[0] == "550" and not VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True).replace("550 ", ""))

def get_file_mode(mode):
    global set_type

    if set_type == "A":
        return mode
    else:
        return mode + "b"

def put_ftp(tokens, ftp_socket, data_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    global sunique

    if len(tokens) is 1:
        local_file = input("(local-file) ")
        remote_file = input("(remote-file) ")
    elif len(tokens) is 2:
        local_file = tokens[1]
        remote_file = local_file
    else:
        local_file = tokens[1]
        remote_file = tokens[2]

    if os.path.isfile(local_file) is False:
        print("local: " + local_file + " remote: " + remote_file)
        print("local: " + local_file + ": No such file or directory")
        return

    if not sunique:
        if DEBUG_MODE:
            print("---> " + "STOR " + remote_file)
        ftp_socket.send(str_msg_encode("STOR " + remote_file + "\n"))
    else:
        if DEBUG_MODE:
            print("---> " + "STOU " + remote_file)
        ftp_socket.send(str_msg_encode("STOU\n"))

    msg = ftp_socket.recv(RECV_BUFFER)
    tokens = str_msg_decode(msg).split()

    if tokens[0] != "150":
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))
        return

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

    data_connection, data_host = data_socket.accept()

    file = open(local_file, get_file_mode("r"))
    size_sent = 0

    while True:
        data = file.read(RECV_BUFFER)

        if isinstance(data, str):
            data = str_msg_encode(data)

        if len(data) < RECV_BUFFER:
            data_connection.send(data)
            size_sent += len(data)
            file.close()
            break
        data_connection.send(data)
        size_sent += len(data)

    data_connection.close()

    msg = ftp_socket.recv(RECV_BUFFER)
    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

def append_ftp(tokens, ftp_socket, data_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) is 1:
        local_file = input("(local-file) ")
        remote_file = input("(remote-file) ")
    elif len(tokens) is 2:
        local_file = tokens[1]
        remote_file = local_file
    else:
        local_file = tokens[1]
        remote_file = tokens[2]

    if os.path.isfile(local_file) is False:
        print("local: " + local_file + " remote: " + remote_file)
        print("local: " + local_file + ": No such file or directory")
        return

    if DEBUG_MODE:
        print("---> " + "APPE " + remote_file)
    ftp_socket.send(str_msg_encode("APPE " + remote_file + "\n"))

    msg = ftp_socket.recv(RECV_BUFFER)
    tokens = str_msg_decode(msg).split()

    if tokens[0] != "150":
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))
        return

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

    data_connection, data_host = data_socket.accept()

    file = open(local_file, get_file_mode("r"))
    size_sent = 0

    while True:
        data = file.read(RECV_BUFFER)

        if isinstance(data, str):
            data = str_msg_encode(data)

        if len(data) < RECV_BUFFER:
            data_connection.send(data)
            size_sent += len(data)
            file.close()
            break
        data_connection.send(data)
        size_sent += len(data)

    data_connection.close()

    msg = ftp_socket.recv(RECV_BUFFER)

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

def ls_ftp(tokens, ftp_socket, data_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) > 1:
        if DEBUG_MODE:
            print("---> " + "LIST " + tokens[1])
        ftp_socket.send(str_msg_encode("LIST " + tokens[1] + "\n"))
    else:
        if DEBUG_MODE:
            print("---> LIST")
        ftp_socket.send(str_msg_encode("LIST\n"))

    msg = ftp_socket.recv(RECV_BUFFER)
    tokens = str_msg_decode(msg).split()

    if tokens[0] != "150":
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))
        return

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

    if str_msg_decode(msg).split()[0] == "450" and not VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True).replace("450 ", ""))

    data_connection, data_host = data_socket.accept()

    while True:
        msg = data_connection.recv(RECV_BUFFER)
        if len(msg) < RECV_BUFFER:
            if VERBOSE_MODE:
                sys.stdout.write(str_msg_decode(msg, True))
            break
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))

    data_connection.close()

    msg = ftp_socket.recv(RECV_BUFFER)

    if str_msg_decode(msg).split()[0] != "226":
        return

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

def delete_ftp(tokens, ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) is 1:
        remote_file = input("(remote-file) ")

        if remote_file is "":
            print("usage: delete remote-file")
            return
    else:
        remote_file = tokens[1]

    if DEBUG_MODE:
        print("---> " + "DELE " + remote_file)
    ftp_socket.send(str_msg_encode("DELE " + remote_file + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)

    if str_msg_decode(msg).split()[0] == "501":
        print("usage: delete remote-file")
    else:
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))
        if str_msg_decode(msg).split()[0] == "550" and not VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True).replace("550 ", ""))
        if str_msg_decode(msg).split()[0] == "530" and not VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True).replace("530 ", ""))

def mdelete_ftp(tokens, ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) is 1:
        remote_files = input("(remote-files) ")
        tokens = remote_files.split(" ")

    for remote_file in tokens:
        if remote_file.upper() != CMD_MDELETE:
            confirm_delete = input("mdelete " + remote_file + "? ")

            if distutils.util.strtobool(confirm_delete):
                if DEBUG_MODE:
                    print("---> " + "DELE " + remote_file)
                ftp_socket.send(str_msg_encode("DELE " + remote_file + "\n"))
                msg = ftp_socket.recv(RECV_BUFFER)
                if VERBOSE_MODE:
                    sys.stdout.write(str_msg_decode(msg, True))
                if str_msg_decode(msg).split()[0] == "550" and not VERBOSE_MODE:
                    sys.stdout.write(str_msg_decode(msg, True).replace("550 ", ""))
                if str_msg_decode(msg).split()[0] == "530" and not VERBOSE_MODE:
                    sys.stdout.write(str_msg_decode(msg, True).replace("530 ", ""))

def logout(logged_on, ftp_socket):
    if ftp_socket is None or logged_on is False:
        print("Not connected")
        return False, ftp_socket

    try:
        if DEBUG_MODE:
            print("---> " + CMD_QUIT)
        ftp_socket.send(str_msg_encode("QUIT\n"))
        msg = ftp_socket.recv(RECV_BUFFER)
        if VERBOSE_MODE:
            sys.stdout.write(str_msg_decode(msg, True))
        ftp_socket = None
    except socket.error:
        print("Error logging out. Try again.")
        return False

    return False, ftp_socket

def quit_ftp(logged_on, ftp_socket):
    logged_on, ftp_socket = logout(logged_on, ftp_socket)

    try:
        if ftp_socket is not None:
            ftp_socket.close()
    except socket.error:
        print("Socket close error.")
    sys.exit()

def relogin(username, password, logged_on, tokens, hostname, ftp_socket):
    if len(tokens) < 3:
        username = input("Username: ")
        password = getpass.getpass("Password:")
    else:
        username = tokens[1]
        password = tokens[2]

    if ftp_socket is None:
        ftp_socket = ftp_connecthost(hostname)
        ftp_recv = ftp_socket.recv(RECV_BUFFER)
        print(ftp_recv.strip('\n'))

    logged_on = login(username, password, ftp_socket)
    return username, password, logged_on, ftp_socket

def user_ftp(username, password, tokens, ftp_socket, hostname):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) is 1:
        username = input("(username) ")
        password = ""
    elif len(tokens) is 2:
        username = tokens[1]
        password = ""
    else:
        username = tokens[1]
        password = tokens[2]

    if DEBUG_MODE:
        print("---> " + "USER " + username)
    ftp_socket.send(str_msg_encode("USER " + username + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

    if password is "":
        password = getpass.getpass("Password:")

    if DEBUG_MODE:
        print("---> PASS XXXX")
    ftp_socket.send(str_msg_encode("PASS " + password + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))
    if str_msg_decode(msg).split()[0] == "530" and not VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True).replace("530 ", ""))

    str_value = str_msg_decode(msg, False)
    tokens = str_value.split()

    if len(tokens) > 0 and tokens[0] != "230":
        print("Login failed")
        return False
    else:
        return True

def login(username, password, ftp_socket):
    global hostname
    global set_type

    if username is None or username.strip() is "":
        username = input("Name (" + hostname + "): ")

    if DEBUG_MODE:
        print("---> " + "USER " + username)
    ftp_socket.send(str_msg_encode("USER " + username + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

    if password is None or password.strip() is "":
        password = getpass.getpass("Password:")

    if DEBUG_MODE:
        print("---> PASS XXXX")
    ftp_socket.send(str_msg_encode("PASS " + password + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)

    if VERBOSE_MODE:
        sys.stdout.write(str_msg_decode(msg, True))

    str_value = str_msg_decode(msg, False)
    tokens = str_value.split()

    if len(tokens) > 0 and tokens[0] != "230":
        print("Login failed")
        return False
    else:
        if DEBUG_MODE:
            print("---> " + "TYPE " + set_type)
        ftp_socket.send(str_msg_encode("TYPE " + set_type + "\n"))
        ftp_socket.recv(RECV_BUFFER)
        print("Mode: " + get_type(set_type).lower())
        return True

def get_type(type):
    if type == "A":
        return "ASCII"
    elif type == "I":
        return "BINARY"
    else:
        return ""

def get_type_code(type):
    if type == "ASCII":
        return "A"
    elif type == "BINARY" or type == "IMAGE":
        return "I"
    else:
        return None

def type_ftp(tokens, logged_on, ftp_socket):
    global set_type

    if ftp_socket is None or logged_on is False:
        print("Not connected")
        return

    if len(tokens) is 1:
        print("Mode: " + get_type(set_type).lower())
        return
    else:
        new_type = tokens[1]
        temp_type = get_type_code(new_type.upper())

        if temp_type is None:
            print("Unknown mode: " + new_type)
        else:
            set_type = temp_type

            if DEBUG_MODE:
                print("---> " + "TYPE " + set_type)
            ftp_socket.send(str_msg_encode("TYPE " + set_type + "\n"))
            msg = ftp_socket.recv(RECV_BUFFER)
            if VERBOSE_MODE:
                sys.stdout.write(str_msg_decode(msg, True))

def help_ftp():
    print("FTP Help")
    print("Commands are not case sensitive")
    print("")
    print("!\t\t Exits FTP and attempts to logout")
    print("?\t\t Prints information about FTP Client commands")
    print(CMD_APPEND + "\t\t Appends a local file to a file on the remote machine. APPEND local_file [remote_file]")
    print(CMD_ASCII + "\t\t Sets the file transfer type to ASCII")
    print(CMD_BINARY + "\t\t Sets the file transfer type to support binary image transfer")
    print(CMD_BYE + "\t\t Exits FTP and attempts to logout")
    print(CMD_CD + "\t\t Changes remote working directory. CD remote_directory")
    print(CMD_CDUP + "\t\t Changes remote working directory to the parent of the current directory")
    print(CMD_CLOSE + "\t\t Logout from FTP but not client")
    print(CMD_DEBUG + "\t\t Toggles debugging mode")
    print(CMD_DELETE + "\t\t Deletes remote file. DELETE [remote_file]")
    print(CMD_DIR + "\t\t Prints out remote directory content")
    print(CMD_DISCONNECT + "\t\t Logout from FTP but not client")
    print(CMD_EXIT + "\t\t Exits FTP and attempts to logout")
    print(CMD_FTP + "\t\t Establishes a connection to the specified host FTP server")
    print(CMD_GET + "\t\t Gets remote file. GET remote_file [name_in_local_system]")
    print(CMD_HELP + "\t\t Prints information about FTP Client commands")
    print(CMD_IMAGE + "\t\t Sets the file transfer type to support binary image transfer")
    print(CMD_LCD + "\t\t Changes local working directory. LCD [directory]")
    print(CMD_LLS + "\t\t Prints out local directory content")
    print(CMD_LOGIN + "\t\t Logs in. It expects username and password. LOGIN [username] [password]")
    print(CMD_LOGOUT + "\t\t Logout from FTP but not client")
    print(CMD_LPWD + "\t\t Prints current local working directory")
    print(CMD_LS + "\t\t Prints out remote directory content")
    print(CMD_MDELETE + "\t\t Deletes multiple remote files")
    print(CMD_MKDIR + "\t\t Makes directory on remote machine. MKDIR directory_name")
    print(CMD_NOOP + "\t\t Keeps control channel alive during idle periods")
    print(CMD_OPEN + "\t\t Establishes a connection to the specified host FTP server")
    print(CMD_PORT + "\t\t ")
    print(CMD_PUT + "\t\t Sends local file. PUT local_file [name_in_remote_system]")
    print(CMD_PWD + "\t\t Prints current (remote) working directory")
    print(CMD_QUIT + "\t\t Exits FTP and attempts to logout")
    print(CMD_RECV + "\t\t Copies a remote file to the local computer")
    print(CMD_RENAME + "\t\t Renames the file on the remote machine. RENAME [from] [to]")
    print(CMD_RHELP + "\t\t Displays help for remote commands")
    print(CMD_RMDIR + "\t\t Deletes a directory. RMDIR directory_name")
    print(CMD_SEND + "\t\t Sends local file. SEND local_file [name_in_remote_system]")
    print(CMD_SUNIQUE + "\t\t Toggles the storing of files")
    print(CMD_TYPE + "\t\t Sets the file transfer type. TYPE [type_name]")
    print(CMD_USAGE + "\t\t Prints the usage for command line arguments")
    print(CMD_USER + "\t\t Logs in. It expects username and password. USER [username] [password]")
    print(CMD_VERBOSE + "\t\t Toggles the display of all responses from the FTP server")

def rhelp_ftp(tokens, ftp_socket):
    if ftp_socket is None:
        print("Not connected")
        return False

    if len(tokens) is 1:
        if DEBUG_MODE:
            print("---> HELP")
        ftp_socket.send(str_msg_encode("HELP\n"))
    else:
        if DEBUG_MODE:
            print("---> " + "HELP " + tokens[1])
        ftp_socket.send(str_msg_encode("HELP " + tokens[1] + "\n"))

    msg = ftp_socket.recv(RECV_BUFFER)
    sys.stdout.write(str_msg_decode(msg, True))

main()
