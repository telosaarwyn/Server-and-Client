import socket
import threading
import os
import sys
from tkinter import *

thread_list = []

# directory
FILE_DIR = 'server_files'
if not os.path.exists(FILE_DIR):
    os.makedirs(FILE_DIR)

registered_users = set()
connected_clients = [] #stores all connected clients
is_running = True

def print_msg(text):
    #fix newlines
    message = text.split("\n")
    for txt in message:
        displayMsg.insert(END, txt + "\n")

# client handling
def handle_client(client_socket, client_address):
    print_msg(f"Handling client {client_address}")

    global connected_clients
    sockAddr = [client_socket, client_address, "N/A"] # "n/a is default name"
    connected_clients.append(sockAddr)

    while is_running:
        try:
            command = client_socket.recv(1024).decode() # receive command from client
        except:
            break
        
        if not command:
            break  

        addr = client_address
        words = command.split()
        if not words[-1] == 'N/A' and not words[0] == '/register':
            client_address = words[-1]
            
        if not words[0] == '/register':
            command = ' '.join(words[:-1])

        print_msg(f"Received command from {client_address}: {command}")

        if command.startswith('/dir'): # list files from the directory
            files = os.listdir(FILE_DIR)
            print_msg(f"List of files in the server_file directory sent to {client_address}")
            if not files:
                client_socket.sendall("    Empty Folder...".encode())
            else:
                files_list = '\n'.join(files)
                client_socket.sendall(files_list.encode())



        elif command.startswith('/register'):
            _, handle = command.split()
            if handle in registered_users:
                client_socket.sendall("Error: Registration failed. Handle or alias already exists".encode())
            else:
                registered_users.add(handle)
                client_socket.sendall(f"Welcome {handle}!".encode())
                print_msg(f'Changing {client_address} to "{handle}"')
                #updating the handle/alias of client_address in connected_clients
                for client in connected_clients:
                    if addr == client[1]: #check for client address
                        client[2] = handle #update name of that client address
                        break



        elif command.startswith('/store'):
            _, filename, file_size = command.split()
            file_size = int(file_size)
            filepath = os.path.join(FILE_DIR, filename)
            with open(filepath, 'wb') as f:
                received = 0
                while received < file_size:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
            print_msg(f"File {filename} received from {client_address}")




        elif command.startswith('/get'):  # handle client's download request
            _, filename = command.split()
            filepath = os.path.join(FILE_DIR, filename)
            if os.path.exists(filepath):
                client_socket.sendall(str(filename).encode()) #send file name
                filesize = os.path.getsize(filepath) #get file size
                client_socket.sendall(str(filesize).encode() + b'\n')
                with open(filepath, 'rb') as f:
                    try:
                        data = f.read(1024)
                        while data:
                            client_socket.sendall(data)
                            data = f.read(1024)
                    except Exception as e:
                        print_msg(f"Error during file sending: {e}")
                    finally:
                        f.close()
                print_msg(f"File {filename} sent to {client_address}")
            else:
                client_socket.sendall(b'0\n')
                print_msg(f"{filename} does not exist in server files")




        elif command.startswith('/broadcast'):
            temp = []
            temp = command.split()
            message = ' '.join(temp[1:])
            # set name of the broadcaster
            if isinstance(client_address, tuple):
                name = "Unregistered User"
            else: name = client_address
            #send message to each client
            with threading.Lock():
                for clients in connected_clients:
                    if (clients[1] == client_address or clients[2] == client_address):
                        try:
                            clients[0].sendall(f"Message broadcasted to everyone.".encode())
                            print_msg(f"Broadcasted message to everyone by {client_address}")
                        except:
                            clients[0].sendall(f"Server encountered a problem. Try again".encode())
                    else:
                        try:
                            clients[0].sendall(f"BROADCAST FROM {name}:\n>>{message}".encode())
                        except:
                            pass



        elif command.startswith('/unicast'):
            temp = command.split()
            #verify receiver name first
            """
            temp[0]  == command
            temp[1]  == receiver
            ##removed in temp == sender
            """
            receiver = "N/A"
            for clients in connected_clients: #client[2] is name, name should not be n/a
                if clients[2].startswith(temp[1]) and clients[2] != "N/A":
                    receiver = clients[2]
                    break
            if receiver.startswith("N/A"):
                client_socket.sendall(f"{temp[1]} does not exist!".encode())
                print_msg(f"Error in sending private message... (Name does not exist!)")
            else:
                message = ' '.join(temp[2:]) #remove accessories
                # set name of the sender
                if isinstance(client_address, tuple):
                    name = "Unregistered User"
                else: name = client_address
                #find the same receiver
                for clients in connected_clients:
                    if clients[1] == client_address or clients[2] == client_address:
                        try:
                            clients[0].sendall(f"Message sent to {receiver}.".encode())
                            print_msg(f"Message sent to {receiver}, {client_address}")
                        except:
                            clients[0].sendall(f"Server encountered a problem. Try again".encode())
                    elif clients[2].startswith(temp[1]):
                        try:
                            clients[0].sendall(f"MESSAGE FROM {name}:\n>>{message}".encode())
                        except:
                            pass

        elif command.startswith('/leave'):  # handle client disconnecting
            print_msg(f"Client {client_address} has disconnected")
            break
        
        if not is_running:
            break

    client_socket.close() # close the client socket


if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <host> <port>")
    sys.exit(1)

HOST, PORT = sys.argv[1:3]
PORT = int(PORT)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def main():
    global extraFrm, server_socket, thread_list

    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print_msg(f"Server listening on port {PORT}")
    
    try:
        while is_running:
            try:
                client_socket, client_address = server_socket.accept()
                print_msg(f"Accepted connection from {client_address}")
                client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
                client_handler.start()
                thread_list.append(client_handler) 
            except ConnectionAbortedError:
                pass
            except OSError as e:
                if not is_running:
                    break
                else:
                    print_msg(f"Unexpected error: {e}")
    except KeyboardInterrupt:
        print_msg("Server is shutting down")
    finally:
        server_socket.close()

def leave_server():
    global is_running, thread_list
    is_running = False

    # Close all existing client connections
    for client in connected_clients:
        client_socket = client[0]
        client_socket.close()
        
    for thread in thread_list:
        thread.join()

    print_msg("Exiting in 3 seconds...")
    ui.after(3000, ui.destroy)
    server_socket.close()
    
# UI
ui = Tk() 
ui.title("Server")  
ui.geometry("500x350")  
   
# frames
lblFrm = Frame(master=ui)
displayFrm = Frame(master=ui, width=600, height=300, bd=1, relief="solid", highlightbackground="black")
displayFrm.pack_propagate(0)
extraFrm = Frame(master=ui, height=30)

# label server host and port number
text = "HOST: " + HOST + " and PORT " + str(PORT)
w = Label(master=lblFrm, text=text, font = "20")  
w.pack() 

# display with scroll
scrollbar = Scrollbar(master = displayFrm)
scrollbar.pack(side = RIGHT, fill = Y)
displayMsg = Listbox(master = displayFrm, width=600, bg="white", yscrollcommand = scrollbar.set)
displayMsg.pack(expand=YES, fill=BOTH)

# exit server
exitBtn = Button(master = extraFrm, text = "EXIT SERVER", command=lambda : leave_server())
exitBtn.grid(row=0, column=1)

lblFrm.pack(side=TOP)
displayFrm.pack(side=TOP)
extraFrm.pack(side=TOP)

server_thread = threading.Thread(target=main)

server_thread.start()
ui.mainloop()
