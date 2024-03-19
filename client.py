#!/usr/bin/env python3
# tftp.py (Piranha's TFTP client) 0.1
#
# Copyright (C) 2024 Erick Mattos <erick.mattos@gmail.com>
#
# This is the TFTP client code of Piranha software.
#
# Piranha is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Piranha is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# On Debian systems, the complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL-3'.

import argparse
import os
import sys
import tftp

def interactive_mode(port: int, server: str, serverip: str):
    """
    This is the interactive interface.
    """
    strCommand = ""
    while strCommand != "quit":
        strCommand = input( "tftp client> " )
        # Estou usando o servidor de TFTP para Windows Tftpd64, que
        # gera automaticamente um arquivo 'dir.txt' com o conteúdo do
        # diretório em 3 colunas: nome, data e tamanho.  Caso fosse
        # implementar um servidor, bastaria fazê-lo gravar neste
        # arquivo o resultado de um 'ls -Alh', no sistema Linux,
        # ou um 'dir' correspondente no Windows.
        if strCommand == "dir":
            receive( port, server, serverip, "dir.txt", ".dir.txt" )
            with open( ".dir.txt", "rt") as file:
                for line in file.readlines(): 
                    if line.split()[0] == "dir.txt":
                        continue
                    print( f"{line.split()[0]:<20} {line.split()[1]:<20} {line.split()[2]:>20}" )
                print()
            try:
                os.remove( os.path.join( os.getcwd(), ".dir.txt" ) )
            except Exception:
                # keep quit! Not important if the file is kept.
                pass
        elif strCommand.split()[0] == "get":
            if len( strCommand.split() ) > 1:
                origin      = strCommand.split()[1] 
                if len( strCommand.split() ) > 2:
                    destination = strCommand.split()[2] 
                else:
                    destination = origin
            else:
                print( "Usage: get remotefile [localfile]\n" )
                continue
            try:
                receive( port, server, serverip, origin, destination )
            except Exception as e:
                print( e )
                print()
        elif strCommand.split()[0] == "put":
            if len( strCommand.split() ) > 1:
                origin          = strCommand.split()[1] 
                if len( strCommand.split() ) > 2:
                    destination = strCommand.split()[2] 
                else:
                    destination = origin
            else:
                print( "Usage: put localfile [remotefile]" )
                continue
            if os.path.isfile( origin ) == False:
                print( f"File '{origin}' not found.\n" )
            else:
                try:
                    send( port, server, serverip, origin, destination )
                except Exception as e:
                    print( e )
                    print()
        elif strCommand == "help":
            print( """Commands:
  get remote_file [local_file] - get a file from server and save it as local_file
  put local_file [remote_file] - send a file to server and store it as remote_file
  dir                          - obtain a listing of remote files
  quit                         - exit TFTP client
""" )
        elif strCommand == "quit":
            pass
        else:
            print( f"Unknown command: '{strCommand.split()[0]}'.\n" )
#    print( f"tftp -p {port} {server}" )

def receive( port: int, server: str, serverip: str, origin: str, destination: str ):
    """
    This method prepares the get command.
    """
    if origin == destination:
        destination = os.path.split(destination)[1]
    tftp.get_file( port, server, serverip, origin, destination )

def send( port: int, server: str, serverip: str, origin: str, destination: str ):
    """
    This method prepares the put command.
    """
    if os.path.isfile( origin ) == False:
        print( f"File {origin} not found.\n" )
        sys.exit(1)
    if origin == destination:
        destination = os.path.split( destination )[1]
    tftp.put_file( port, server, serverip, origin, destination )

if __name__ == '__main__':

    parse = argparse.ArgumentParser(
        prog="client.py",
        description="Cliente TFTP Piranha.",
        epilog="Copyright (C) 2024 Erick Mattos <erick.mattos@gmail.com>" )
    parse.add_argument( "MODE", choices=["get", "put"], nargs="?", type=str.lower, help="Modo de operação." )
    parse.add_argument( "-p", "--port", default=69, help="Porta do servidor." )
    parse.add_argument( "SERVER", help="Servidor a contactar." )
    parse.add_argument( "ORIGIN", nargs="?", help="Arquivo de origem." )
    parse.add_argument( "DESTINATION", nargs="?", help="Arquivo de destino" )
    args = parse.parse_args()

    strServerIP = tftp.getIP( args.SERVER )
    if strServerIP is None:
        print( f"Unknown server: '{args.SERVER}'." )
        sys.exit(1)
    strServerIP = strServerIP.strip("'")
    if args.SERVER == strServerIP:
        args.SERVER = tftp.getHost(strServerIP)
        if args.SERVER is None:
            args.SERVER = 'Unnamed'
    args.SERVER = args.SERVER.strip("'")
    if args.DESTINATION is None:
        args.DESTINATION = args.ORIGIN

    if args.MODE is None:
        print( f"Exchanging files with server '{args.SERVER}' ({strServerIP}).\n" )
        interactive_mode(args.port, args.SERVER, strServerIP)
    elif args.MODE == "get":
        if args.ORIGIN: 
            receive(args.port, args.SERVER, strServerIP, args.ORIGIN, args.DESTINATION)
        else:
            print( "You have to designate the file to get from the server." )
            sys.exit(1)
    elif args.MODE == "put":
        if args.ORIGIN:
            send(args.port, args.SERVER, strServerIP, args.ORIGIN, args.DESTINATION)
        else:
            print( "You have to designate the file to put into the server." )
            sys.exit(1)
    else:
        print( "Unknown command." )
        sys.exit(1)
