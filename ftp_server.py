
from socket import *
import threading
import sys
import os
import string
import random
import argparse


RECV_BUFFER = 1024
thread_list = []

parser = argparse.ArgumentParser(prog="python3 ftp_server")
parser.add_argument("-port", help="port number")
parser.add_argument("-configuration", help="configuration file path")
parser.add_argument("-max", help="maximum number of connections")
parser.add_argument("-userdb", help="user file path")

args = parser.parse_args()

if args.configuration is not None:
    config_path = os.path.abspath(args.configuration)
else:
    config_path = os.path.abspath("ftpserver/conf/sys.cfg")

with open(config_path, "r") as config_file:
    data = config_file.read().split("\n")

FTP_ROOT = data[0].split(" ")[1]
USER_DATA_PATH = data[1].split(" ")[1]
FTP_MODE = data[2].split(" ")[1]
DATA_PORT_FTP_SERVER = int(data[3].split(" ")[1])
MAX_USER_SUPPORT = int(data[5].split(" ")[1])
FTP_LOG_PATH = data[6].split(" ")[1]
SERVICE_PORT = int(data[7].split(" ")[1])

config_file.close()

if args.port is not None:
    DATA_PORT_FTP_SERVER = args.port

if args.max is not None:
    MAX_USER_SUPPORT = args.max

if args.userdb is not None:
    USER_DATA_PATH = args.userdb

USER_TYPE_ADMIN = "ADMIN"
USER_TYPE_USER = "USER"
USER_TYPE_NOTALLOWED = "NOTALLOWED"
USER_TYPE_LOCKED = "LOCKED"

commands = {
    "CMD_USER": {
        "cmd": "USER",
        "syntax": "214 Syntax: USER <sp> username"
    },
    "CMD_PASS": {
        "cmd": "PASS",
        "syntax": "214 Syntax: PASS <sp> password"
    },
    "CMD_CWD": {
        "cmd": "CWD",
        "syntax": "214 Syntax: CWD <sp> pathname"
    },
    "CMD_CDUP": {
        "cmd": "CDUP",
        "syntax": "214 Syntax: CDUP (up one directory)"
    },
    "CMD_RETR": {
        "cmd": "RETR",
        "syntax": "214 Syntax: RETR <sp> pathname"
    },
    "CMD_STOR": {
        "cmd": "STOR",
        "syntax": "214 Syntax: STOR <sp> pathname"
    },
    "CMD_STOU": {
        "cmd": "STOU",
        "syntax": "214 Syntax: STOU (store unique filename)"
    },
    "CMD_APPE": {
        "cmd": "APPE",
        "syntax": "214 Syntax: APPE <sp> pathname"
    },
    "CMD_TYPE": {
        "cmd": "TYPE",
        "syntax": "214 Syntax: TYPE <sp> type-code (A, I)"
    },
    "CMD_RNFR": {
        "cmd": "RNFR",
        "syntax": "214 Syntax: RNFR <sp> pathname"
    },
    "CMD_RNTO": {
        "cmd": "RNTO",
        "syntax": "214 Syntax: RNTO <sp> pathname"
    },
    "CMD_DELE": {
        "cmd": "DELE",
        "syntax": "214 Syntax: DELE <sp> pathname"
    },
    "CMD_RMD": {
        "cmd": "RMD",
        "syntax": "214 Syntax: RMD <sp> pathname"
    },
    "CMD_MKD": {
        "cmd": "MKD",
        "syntax": "214 Syntax: MKD <sp> pathname"
    },
    "CMD_PWD": {
        "cmd": "PWD",
        "syntax": "214 Syntax: PWD (returns current working directory)"
    },
    "CMD_LIST": {
        "cmd": "LIST",
        "syntax": "214 Syntax: LIST [<sp> pathname]"
    },
    "CMD_NOOP": {
        "cmd": "NOOP",
        "syntax": "214 Syntax: NOOP (no operation)"
    },
    "CMD_QUIT": {
        "cmd": "QUIT",
        "syntax": "214 Syntax: QUIT (close control connection)"
    },
    "CMD_HELP": {
        "cmd": "HELP",
        "syntax": "214 Syntax: HELP [<sp> command]"
    }
}

def server_thread(connection_socket, address):
    try:
        print("Thread Server Entering Now...")
        print(address)

        local_thread = threading.local()
        local_thread.response = "220 FTP Server"
        local_thread.current_directory = ""
        local_thread.base_directory = ""
        local_thread.rename_from_path = ""
        local_thread.rename_from_file = ""
        local_thread.set_type = "I"
        local_thread.current_user = ""
        local_thread.user_type = ""
        local_thread.logged_on = False
        local_thread.data_socket = None

        connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

        while True:
            print("TID = ", threading.current_thread())
            print("Current Directory: " + local_thread.current_directory)
            print("Base Directory: " + local_thread.base_directory)
            print("Current user: " + local_thread.current_user)
            print("Type: " + local_thread.set_type)
            print("Logged on? " + str(local_thread.logged_on))

            cmd = str_msg_decode(connection_socket.recv(RECV_BUFFER))

            print("Received command: " + cmd)

            if cmd[0:4] == commands["CMD_QUIT"]["cmd"]:
                quit_ftp(connection_socket, local_thread)
            elif cmd[0:4] == commands["CMD_USER"]["cmd"]:
                user_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:4] == commands["CMD_PASS"]["cmd"]:
                pass_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:3] == commands["CMD_CWD"]["cmd"]:
                cwd_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:4] == commands["CMD_CDUP"]["cmd"]:
                cdup_ftp(connection_socket, local_thread)
            elif cmd[0:4] == commands["CMD_RETR"]["cmd"]:
                retr_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:4] == commands["CMD_STOR"]["cmd"]:
                stor_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:4] == commands["CMD_STOU"]["cmd"]:
                stou_ftp(connection_socket, local_thread)
            elif cmd[0:4] == commands["CMD_APPE"]["cmd"]:
                appe_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:4] == commands["CMD_TYPE"]["cmd"]:
                type_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:4] == commands["CMD_RNFR"]["cmd"]:
                rnfr_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:4] == commands["CMD_RNTO"]["cmd"]:
                rnto_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:4] == commands["CMD_DELE"]["cmd"]:
                dele_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:3] == commands["CMD_RMD"]["cmd"]:
                rmd_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:3] == commands["CMD_MKD"]["cmd"]:
                mkd_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:3] == commands["CMD_PWD"]["cmd"]:
                pwd_ftp(connection_socket, local_thread)
            elif cmd[0:4] == commands["CMD_LIST"]["cmd"]:
                list_ftp(connection_socket, local_thread, cmd)
            elif cmd[0:4] == commands["CMD_NOOP"]["cmd"]:
                noop_ftp(connection_socket, local_thread)
            elif cmd[0:4] == commands["CMD_HELP"]["cmd"]:
                help_ftp(connection_socket, local_thread, cmd)
            else:
                local_thread = ("? " + cmd)
                print(local_thread.response)
                connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

    except OSError as e:
        print("Socket error:", e)

def help_ftp(connection_socket, local_thread, cmd):
    global commands

    cmd = cmd[5:-1]
    if len(cmd) is 0:
        local_thread.response = "\n214-FTP Remote Help\n" \
                                "214-Commands are not case-sensitive:\n" \
                                "214-CWD     CDUP    QUIT    RNFR\n" \
                                "214-RNTO    DELE    RMD     MKD\n" \
                                "214-PWD     HELP    NOOP    TYPE\n" \
                                "214-RETR    STOR    STOU    APPE\n" \
                                "214-USER    PASS    LIST\n"

        connection_socket.send(str_msg_encode(response_msg(local_thread.response)))
    else:
        cmd = cmd.upper()
        cmd_key = "CMD_" + cmd
        for key in commands:
            if key == cmd_key:
                print(key)
                local_thread.response = commands[cmd_key]["syntax"]
                connection_socket.send(str_msg_encode(response_msg(local_thread.response)))
                found = True
                break
            else:
                found = False

        if not found:
            local_thread.response = "502 Unknown command '" + cmd + "'"
            connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def quit_ftp(connection_socket, local_thread):
    local_thread.response = response_msg("221 Bye!")
    connection_socket.send(str_msg_encode(local_thread.response))
    connection_socket.close()

def user_ftp(connection_socket, local_thread, cmd):
    local_thread.current_user = cmd[5:-1]
    local_thread.response = response_msg("331 Password required for " + local_thread.current_user)
    connection_socket.send(str_msg_encode(local_thread.response))

def pass_ftp(connection_socket, local_thread, cmd):
    global USER_DATA_PATH

    user_data_path = os.path.abspath(USER_DATA_PATH)

    with open(user_data_path, "r") as user_data_file:
        user_data = user_data_file.read().split("\n")

    for user in user_data:
        if local_thread.current_user == user.split(" ")[0]:
            print("Found user " + local_thread.current_user)

            if cmd[5:-1] == user.split(" ")[1]:
                local_thread.user_type = user.split(" ")[2].upper()

                if local_thread.user_type == USER_TYPE_ADMIN:
                    print("Admin type")
                    local_thread.base_directory = os.path.abspath(FTP_ROOT)
                    local_thread.current_directory = os.path.abspath(FTP_ROOT + "/" + local_thread.current_user)
                    local_thread.logged_on = True
                    local_thread.response = "230 Admin access granted"
                    break

                elif local_thread.user_type == USER_TYPE_USER:
                    print("User type")
                    local_thread.base_directory = os.path.abspath(FTP_ROOT + "/" + local_thread.current_user)
                    local_thread.current_directory = os.path.abspath(FTP_ROOT + "/" + local_thread.current_user)
                    local_thread.logged_on = True
                    local_thread.response = "230 User access granted"
                    break

                elif local_thread.user_type == USER_TYPE_NOTALLOWED:
                    print("User is not allowed")
                    local_thread.logged_on = False
                    local_thread.response = "530 " + local_thread.current_user + " is not allowed"
                    break

                elif local_thread.user_type == USER_TYPE_LOCKED:
                    print("User is locked. Try again later.")
                    local_thread.logged_on = False
                    local_thread.response = "530 " + local_thread.current_user + " is locked"
                    break

                else:
                    print("Setting type to " + USER_TYPE_NOTALLOWED)
                    local_thread.user_type = USER_TYPE_NOTALLOWED
                    local_thread.logged_on = False
                    local_thread.response = "530 " + local_thread.current_user + " is not allowed"
                    break

            else:
                print("Wrong password for " + local_thread.current_user)
                local_thread.logged_on = False
                local_thread.response = "530 Login incorrect"
                break

        else:
            print("Did not find " + local_thread.current_user)
            local_thread.logged_on = False
            local_thread.response = "530 Login incorrect"

    user_data_file.close()
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def cwd_ftp(connection_socket, local_thread, cmd):
    if local_thread.logged_on:
        directory = cmd[4:-1]

        if directory == "/":
            local_thread.current_directory = local_thread.base_directory
            local_thread.response = "250 CWD command successful"
        elif directory == "..":
            cdup_ftp(connection_socket, local_thread)
            return
        elif directory[0] == '/':
            path = os.path.join(local_thread.base_directory, directory[1:])

            if os.path.exists(path):
                local_thread.current_directory = path
                local_thread.response = "250 CWD command successful"
            else:
                local_thread.response = "550 " + directory[1:] + ": No such file or directory"
        else:
            path = os.path.join(local_thread.current_directory, directory)

            if os.path.exists(path):
                local_thread.current_directory = path
                local_thread.response = "250 CWD command successful"
            else:
                local_thread.response = "550 " + directory + ": No such file or directory"
    else:
        local_thread.response = "530 Please log in with USER and PASS"

    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def cdup_ftp(connection_socket, local_thread):
    if local_thread.logged_on:
        if not os.path.samefile(local_thread.current_directory, local_thread.base_directory):
            local_thread.current_directory = os.path.abspath(os.path.join(local_thread.current_directory, ".."))

        local_thread.response = "250 CDUP command successful"
    else:
        local_thread.response = "530 Please log in with USER and PASS"

    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def retr_ftp(connection_socket, local_thread, cmd):
    file = cmd.split()[1]
    path = os.path.join(local_thread.current_directory, file)

    if os.path.isdir(path):
        local_thread.response = "550 " + file + ": Not a regular file"
        connection_socket.send(str_msg_encode(response_msg(local_thread.response)))
    elif os.path.exists(path):
        local_thread.response = "150 Opening " + get_type(local_thread.set_type) + " mode data connection for " + file
        connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

        open_file = open(path, get_file_mode(local_thread, "r"))

        while True:
            file_data = open_file.read(RECV_BUFFER)

            if isinstance(file_data, str):
                file_data = str_msg_encode(file_data)

            if not file_data or file_data == "" or len(file_data) <= 0:
                print("i made it")
                open_file.close()
                local_thread.data_socket.close()
                break

            if len(file_data) < RECV_BUFFER:
                local_thread.data_socket.send(file_data)
                open_file.close()
                break
            local_thread.data_socket.send(file_data)

        local_thread.response = "226 Transfer complete"
        connection_socket.send(str_msg_encode(response_msg(local_thread.response)))
    else:
        local_thread.response = "550 " + file + ": No such file or directory"
        connection_socket.send(str_msg_encode(response_msg(local_thread.response)))


def get_file_mode(local_thread, mode):
    if local_thread.set_type == "A":
        return mode
    else:
        return mode + "b"

def stor_ftp(connection_socket, local_thread, cmd):
    file = cmd.split()[1]
    path = os.path.join(local_thread.current_directory, file)

    local_thread.response = "150 Opening " + get_type(local_thread.set_type) + " mode data connection for " + file
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

    open_file = open(path, get_file_mode(local_thread, "w"))

    while True:
        file_data = local_thread.data_socket.recv(RECV_BUFFER)

        if local_thread.set_type == "A":
            file_data = str_msg_decode(file_data)

        if len(file_data) < RECV_BUFFER:
            open_file.write(file_data)
            open_file.close()
            break
        open_file.write(file_data)

    local_thread.response = "226 Transfer complete"
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def stou_ftp(connection_socket, local_thread):
    file = "ftp"
    counter = 6
    while counter > 0:
        file += random.choice(string.ascii_letters + string.digits)
        counter -= 1

    path = os.path.join(local_thread.current_directory, file)

    local_thread.response = "150 File: " + file
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

    open_file = open(path, get_file_mode(local_thread, "w"))

    while True:
        file_data = local_thread.data_socket.recv(RECV_BUFFER)

        if local_thread.set_type == "A":
            file_data = str_msg_decode(file_data)

        if len(file_data) < RECV_BUFFER:
            open_file.write(file_data)
            open_file.close()
            break
        open_file.write(file_data)

    local_thread.response = "226 Transfer complete"
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def appe_ftp(connection_socket, local_thread, cmd):
    file = cmd.split()[1]
    path = os.path.join(local_thread.current_directory, file)

    local_thread.response = "150 Opening " + get_type(local_thread.set_type) + " mode data connection for " + file
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

    open_file = open(path, get_file_mode(local_thread, "a"))

    while True:
        file_data = local_thread.data_socket.recv(RECV_BUFFER)

        if local_thread.set_type == "A":
            file_data = str_msg_decode(file_data)

        if len(file_data) < RECV_BUFFER:
            open_file.write(file_data)
            open_file.close()
            break
        open_file.write(file_data)

    local_thread.response = "226 Transfer complete"
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def type_ftp(connection_socket, local_thread, cmd):
    local_thread.set_type = cmd[5]
    local_thread.response = "200 Type set to " + local_thread.set_type
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def rnfr_ftp(connection_socket, local_thread, cmd):
    local_thread.rename_from_file = cmd[5:-1]
    local_thread.rename_from_path = os.path.join(local_thread.current_directory, cmd[5:-1])

    if local_thread.logged_on:
        if os.path.exists(local_thread.rename_from_path):
            local_thread.response = "350 Ready for destination name"
        else:
            local_thread.response = "550 " + local_thread.rename_from_file + ": No such file or directory"
    else:
        local_thread.response = "530 Please login with USER and PASS"

    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def rnto_ftp(connection_socket, local_thread, cmd):
    if local_thread.logged_on:
        if os.path.exists(local_thread.rename_from_path):
            rename_to = os.path.join(local_thread.current_directory, cmd[5:-1])
            os.rename(local_thread.rename_from_path, rename_to)
            local_thread.response = "250 Rename successful"
    else:
        local_thread.response = "530 Please login with USER and PASS"

    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def dele_ftp(connection_socket, local_thread, cmd):
    if local_thread.logged_on:
        file = cmd[5:-1]
        path = os.path.join(local_thread.current_directory, file)

        if os.path.isdir(path):
            local_thread.response = "550 " + file + " is a directory"
        elif os.path.exists(path):
            os.remove(path)
            local_thread.response = "250 Delete command successful"
        else:
            local_thread.response = "550 " + file + ": No such file or directory"
    else:
        local_thread.response = "530 Please login with USER and PASS"

    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def rmd_ftp(connection_socket, local_thread, cmd):
    if local_thread.logged_on:
        remove_directory = cmd[4:-1]
        path = os.path.join(local_thread.current_directory, remove_directory)

        if remove_directory == "":
            local_thread.response = "501 Syntax error in parameters or arguments"
        elif os.path.exists(path):
            if directory_is_empty(path):
                os.rmdir(path)
                local_thread.response = "250 RMD command successful"
            else:
                local_thread.response = "550 " + remove_directory + ": Directory is not empty"

        else:
            local_thread.response = "550 " + remove_directory + ": No such file or directory"

    else:
        local_thread.response = "530 Please login with USER and PASS"

    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def mkd_ftp(connection_socket, local_thread, cmd):
    if local_thread.logged_on:
        new_directory = cmd[4:-1]
        path = os.path.join(local_thread.current_directory, new_directory)

        if not os.path.isdir(path):
            os.mkdir(path)
            local_thread.response = "257 /" + new_directory + " - Directory successfully created"
        else:
            if directory_is_empty(path):
                local_thread.response = "257 /" + new_directory + " - Directory successfully created"
            else:
                local_thread.response = "550 " + new_directory + ": Directory is not empty"
    else:
        local_thread.response = "530 Please login with USER and PASS"

    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def pwd_ftp(connection_socket, local_thread):
    if local_thread.logged_on:
        directory = os.path.relpath(local_thread.current_directory, local_thread.base_directory)

        if directory == ".":
            directory = ""

        local_thread.response = "257 \\" + directory + " is the current directory"
    else:
        local_thread.response = "530 Please login with USER and PASS"

    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def list_ftp(connection_socket, local_thread, cmd):
    local_thread.response = "150 Opening ASCII mode data connection for file list"
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

    directory = cmd[5:-1]
    if directory != "":
        path = os.path.join(local_thread.current_directory, directory)
        if os.path.exists(path):
            directory_list(path, local_thread)
        else:
            local_thread.data_socket.send(str_msg_encode(response_msg("450 " + directory + ": No such file or directory")))
            return

    directory_list(local_thread.current_directory, local_thread)
    local_thread.response = "226 Transfer complete"
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def noop_ftp(connection_socket, local_thread):
    local_thread.response = "200 NOOP command successful"
    connection_socket.send(str_msg_encode(response_msg(local_thread.response)))

def join_all_threads():
    global thread_list
    for t in thread_list:
        t.join()

def str_msg_encode(str_value):
    msg = str_value.encode()
    return msg

def str_msg_decode(msg, print_strip=False):
    str_value = msg.decode()
    if print_strip:
        str_value.strip('\n')
    return str_value

def response_msg(msg):
    return msg + "\r\n"

def directory_is_empty(path):
    if os.listdir(path) == []:
        return True
    else:
        return False

def get_type(type):
    if type == "A":
        return "ASCII"
    elif type == "I":
        return "BINARY"
    else:
        return ""

def directory_list(path, local_thread):
    if directory_is_empty(path):
        local_thread.data_socket.close()
    else:
        for item in os.listdir(path):
            local_thread.data_socket.send(str_msg_encode(response_msg(item)))

def main():
    try:
        global thread_list

        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind(('', DATA_PORT_FTP_SERVER))
        server_socket.listen(15)
        print("The server is ready to receive.\n")

        while True:
            connection_socket, address = server_socket.accept()
            t = threading.Thread(target=server_thread, args=(connection_socket, address))
            t.start()
            thread_list.append(t)
            print("Thread started")
            print("Waiting for connection...")

    except KeyboardInterrupt:
        print("Bye!")
        join_all_threads()

    print("Bye!")
    sys.exit(0)

if __name__ == "__main__":
    main()
