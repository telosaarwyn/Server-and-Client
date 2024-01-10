import socket 
import os
from datetime import datetime
import threading
from tkinter import *
      
invalidError = "Error: Command parameters do not match or is not allowed."
notConnected = "Error: Client is not connected to a server. Use /join first"
clientHandle = "N/A"
discError = "Server Not Found"
access = False
join = 0
userCommand = "n/a"

def getTxtMsg():
    text = txtbox.get("1.0", END)
    txtbox.delete("1.0", END)
    return text


def print_msg(text):
    #fix newlines
    message = text.split("\n")
    for txt in message:
        displayMsg.insert(END, txt + "\n")


# upload file function
def upload_file(filename):
    try:
        filepath = os.path.join('client_files', filename)
        if os.path.exists(filepath):
            filesize = os.path.getsize(filepath)
            client_socket.sendall(f'/store {filename} {filesize} {clientHandle}'.encode()) # send command to server
            with open(filepath, 'rb') as f:         # read and sends the file contend 
                data = f.read(1024)
                while data:
                    client_socket.sendall(data)
                    data = f.read(1024)
            current_datetime = datetime.now()
            date_now = current_datetime.date()
            time_now = current_datetime.time().strftime("%H:%M:%S")
            print_msg(f"File {filename} uploaded on {date_now} at {time_now}")
        else:
            print_msg("File not found.")
    except:
        print_msg(discError)


# download file function
def download_file(filename):
    try:
        if not filename.startswith('0'):
            filesize_data = client_socket.recv(1024).decode()
            filesize = int(filesize_data.split('\n')[0])
            filepath = os.path.join('client_files', filename)
            with open(filepath, 'wb') as f:
                remaining = filesize
                while remaining > 0:
                    chunk_size = 1024 if remaining >= 1024 else remaining
                    data = client_socket.recv(chunk_size)
                    if not data: break
                    f.write(data)
                    remaining -= len(data)
            print_msg(f"File received from Server: {filename}")
        else:
            print_msg("File not found on server.")
    except:
        print_msg(discError)


# register user
def register_user(response):
    try:
        global clientHandle #to change clientHandle to handle
        alias = response.split()
        if len(alias) == 2:
            handle = alias[-1]
            clientHandle = handle[:-1] #remove exclamation mark
        print_msg(response)
    except:
        print_msg(discError)


# get commands from user
def send_cmd():
    try:
        global join, userCommand, access, commandEnt, client_socket

        command = ""

        user_input = commandEnt.get()

        if user_input:
            command = user_input

        #joining
        if command.startswith('/join'):
            userCommand = "n/a"
            checkCommand = command.split()
            if (len(checkCommand) != 3):
                print_msg(invalidError)
            else :
                _, serverIP, serverPort = checkCommand
                serverPort = int(serverPort)
                try: 
                    client_socket.connect((serverIP, serverPort))
                    print_msg("Connection to the File Exchange Server is successful!")
                    access = True
                    join = 1

                    receive_thread = threading.Thread(target=receive_msg)
                    receive_thread.start()
                except:
                    print_msg("Error: Connection to the Server has failed! Please check IP Address and Port Number.")

        #leaving
        elif command.startswith('/leave'):
            userCommand = "n/a"
            checkCommand = command.split()
            if (len(checkCommand) == 1):
                if access == True:
                    try: 
                        client_socket.sendall(f'/leave {clientHandle}'.encode()) 
                        print_msg("Connection closed. Thank you!")
                        access = False
                        join = 2
                        client_socket.close()
                        print_msg("Exiting in 3 seconds...")
                        ui.after(3000, ui.destroy)
                    except: 
                        print_msg(discError)
                else:
                    print_msg("Error: Disconnection failed. Please connect to the server first.")
            else:
                print_msg(invalidError)

        #storing/uploading file
        elif command.startswith('/store'):
            userCommand = "n/a"
            checkCommand = command.split()
            if (len(checkCommand) != 2):
                print_msg(invalidError)
            else:
                if (access):
                    _, filename = command.split()
                    upload_file(filename)
                else:
                    print_msg(notConnected)

        #getting/downloading file
        elif command.startswith('/get'):
            userCommand = "get"
            checkCommand = command.split()
            if (len(checkCommand) != 2):
                print_msg(invalidError)
            else:
                if (access):
                    _, filename = command.split()
                    client_socket.sendall(f'/get {filename} {clientHandle}'.encode())
                else:
                    print_msg(notConnected)

        #list of files
        elif command.startswith('/dir'):
            userCommand = "dir"
            checkCommand = command.split()
            if (len(checkCommand) != 1):
                print_msg(invalidError)
            else:
                if (access):
                    client_socket.sendall(f'/dir {clientHandle}'.encode())
                else: 
                    print_msg(notConnected)

        # register
        elif command.startswith('/register'):
            userCommand = "register"
            checkCommand = command.split()
            if len(checkCommand) != 2:
                print_msg(invalidError)
            else:
                if access:
                    client_socket.sendall(command.encode())
                else:
                    print_msg(notConnected)

        # list of commands
        elif command.startswith('/?'):
            userCommand = "n/a"
            print_msg("Command available:")
            print_msg("     /join <server_ip_add> <port_no> -- connect to the server")
            print_msg("     /leave                            -- disconnect to the server")
            print_msg("     /register <handle>     -- register a unique handle")
            print_msg("     /store <filename>      -- send file to the server")
            print_msg("     /get <filename>         -- fetch file from the server")
            print_msg("     /dir                                -- request directory file list from the server")
            print_msg("     /broadcast                   -- send a message to everyone")
            print_msg("     /unicast <handle>      -- private message someone (must be registered)")


        elif command.startswith('/broadcast'):
            userCommand = "broadcast"
            checkCommand = command.split()
            if len(checkCommand) != 1:
                print_msg(invalidError)
            else:
                if access:
                    txtFrm.pack(expand=YES, fill=BOTH, side=TOP)
                    txtFrm.wait_variable(messageBox) #wait for text to have message
                    command = getTxtMsg()
                    client_socket.sendall(f'/broadcast {command} {clientHandle}'.encode())
                else:
                    print_msg(notConnected)
            
            

        elif command.startswith('/unicast'):
            userCommand = "unicast"
            checkCommand = command.split()
            if len(checkCommand) != 2:
                print_msg(invalidError)
            elif checkCommand[1] == clientHandle:
                print_msg("Error: You can't message yourself.")
            else:
                if access:
                    txtFrm.pack(expand=YES, fill=BOTH, side=TOP)
                    txtFrm.wait_variable(messageBox) #wait for text to have message
                    command = getTxtMsg()
                    client_socket.sendall(f'/unicast {checkCommand[1]} {command} {clientHandle}'.encode())
                else:
                    print_msg(notConnected)

        elif command == "":
            pass

        else:
            print_msg("Error: Command not found.")

        txtFrm.forget()
        commandEnt.delete(0, END) #delete text
    except:
        if (join >= 1):
            print_msg(discError)



def receive_msg():
    while True and join != 2:
        try:
            global userCommand
            if not client_socket:
                break
            message = client_socket.recv(1024).decode()
            if not message:
                break

            #getting/downloading file
            if userCommand == "get":
                download_file(message)            

            #list of files
            elif userCommand == 'dir':
                try:
                    print_msg("Files on server:")
                    print_msg(message)  # print list of files
                except:
                    print_msg(discError)

            # register
            elif userCommand == "register":
                register_user(message)

            elif userCommand == "broadcast":
                print_msg(message)

            elif userCommand == "unicast":
                print_msg(message)

            if message.startswith("BROADCAST") or message.startswith("MESSAGE"):
                print_msg(message)

            userCommand = 'n/a' #revert to default so no echo or duplicates
        except:
            break #do nothing if nothing recevied

# UI
ui = Tk() 
ui.title("Client")  
ui.geometry("500x350")  
   

# frames
cmdFrm = Frame(master=ui, height=30)
txtFrm = Frame(master=ui)
displayFrm = Frame(master=ui, width=450, height=200, bd=1, relief="solid", highlightbackground="black")
displayFrm.pack_propagate(0)
extraFrm = Frame(master=ui, height=30)


# the label for the command function
commandLbl = Label(master = cmdFrm, text = "COMMAND:")
commandLbl.grid(row=0, column=0, padx=10)
commandEnt = Entry(master = cmdFrm, width=30)
commandEnt.grid(row=0, column=1, padx=10)
enterBtn = Button(master = cmdFrm, text = "ENTER", command=send_cmd)
enterBtn.grid(row=0, column=2, padx=10)

# optional: textbox for message in broadcast/unicast
doneBtn = Button(master=txtFrm, text = "Submit", command=lambda: messageBox.set(1))
doneBtn.pack(side=LEFT, padx=5)
messageLbl = Label(master=txtFrm, text = "Message:")
messageLbl.pack(side=LEFT, padx=5)
txtbox = Text(master=txtFrm, width=350, height=5)
txtbox.pack()

# display with scroll
scrollbar = Scrollbar(master = displayFrm)
scrollbar.pack(side = RIGHT, fill = Y)
displayMsg = Listbox(master = displayFrm, width=450, bg="white", yscrollcommand = scrollbar.set)
displayMsg.pack(expand=YES, fill=BOTH)

messageBox = IntVar()
messageBox.set(0)


cmdFrm.pack(side=TOP)
txtFrm.pack(side=TOP)
displayFrm.pack(side=TOP)
extraFrm.pack(side=TOP)
    
txtFrm.pack_forget()


# client-server code
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except KeyboardInterrupt:
    print_msg("Client is shutting down")
except Exception as e:
    print_msg("Unknown Error..." + e)

ui.mainloop() 

