#!/usr/bin/env python3
# tftp.py (Piranha's TFTP library) 0.1
#
# Copyright (C) 2024 Erick Mattos <erick.mattos@gmail.com>
#
# This is the main library of Piranha software.
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

import os
import socket
import string
import struct

if os.name == 'nt':
    import msvcrt
    import ctypes

    class _CursorInfo(ctypes.Structure):
        _fields_ = [("size", ctypes.c_int),
                    ("visible", ctypes.c_byte)]

###############################################################
##                                                           ##
##              PROTOCOL CONSTANTS AND TYPES                 ##
##                                                           ##     
###############################################################

MAX_ATTEMPTS        = 5               # bytes    
MAX_DATA_LEN        = 512             # bytes    
MAX_BLOCK_NUMBER    = 2**16 -1        # 0..65535
INACTIVITY_TIMEOUT  = 25.0            # segs
DEFAULT_MODE        = 'octet'
DEFAULT_BUFFER_SIZE = 8192            # bytes
INET4Address        = tuple[str, int] # TCP/UDP address => IPv4 and port


# TFTP message opcodes
RRQ = 1 # Read Request
WRQ = 2 # Write Request
DAT = 3 # Data Transfer
ACK = 4 # Acknowledge
ERR = 5 # Error packet: what the server responds if a read/write 
        # can't be processed, read and write errors during file 
        # transmission also cause this message to be sent, and 
        # transmission is then terminated. The error number gives a
        # numeric error code, followed by and ASCII error message that
        # might contain additional, operating system specific 
        # information.

ERR_NOT_DEFINED        = 0
ERR_FILE_NOT_FOUND     = 1 
ERR_ACCESS_VIOLATION   = 2
DISK_FULL_OR_ALLOC_EXC = 3
ILLEGAL_TFTP_OP        = 4
UNKOWN_TRANSF_ID       = 5
FILE_ALREADY_EXISTS    = 6
NO_SUCH_USER           = 7

ERROR_MESSAGES = {
    ERR_NOT_DEFINED: 'Not defined, see error message(if any).',
    ERR_FILE_NOT_FOUND: 'File not found',
    ERR_ACCESS_VIOLATION: 'Access violation',
    DISK_FULL_OR_ALLOC_EXC: 'Disk full or allocation exceeded.',
    ILLEGAL_TFTP_OP: 'Illegal TFTP operation',
    UNKOWN_TRANSF_ID: 'Unkown Transfer ID',
    FILE_ALREADY_EXISTS: 'File already exists',
    NO_SUCH_USER: 'No such user'
}

###############################################################
##                                                           ##
##                       MISCELANEOUS                        ##
##                                                           ##
###############################################################

def getIP(d):
    """
    This method takes a FQDN and translates it to the 
    first IP found.
    """
    try:
        data = socket.gethostbyname(d)
        ip = repr(data)
        return ip
    except Exception:
        # keep quiet!
        return None

def getHost(ip):
    """
    This method takes an IP and returns the Domain Name
    associated to it.
    """
    try:
        data = socket.gethostbyaddr(ip)
        host = repr(data[0])
        return host
    except Exception:
        # keep quiet!
        return None

def hide_cursor():
    if os.name == "nt":
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = False
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == "posix":
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

def is_ascii_printable(txt: str) -> bool:
    return set(txt).issubset(string.printable)

def logit(code: int, message: str, clean: bool):
    if not clean:
        print( "                                                            ",
              end="\r", flush=True)
    print( message, end="\r", flush=True)

def show_cursor():
    if os.name == "nt":
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = True
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == "posix":
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

###############################################################
##                                                           ##
##                 SEND AND RECEIVE FILES                    ##
##                                                           ##     
###############################################################

#def get_file(server_addr: INET4Address, filename: str):
#    print(f"Descarregar ficheiro a partir de {server_addr} ")
#   # 1. Criar um socket DGRAM para comunicar com servidor em server_addr
#   # 2. Abrir um ficheiro local com nome 'filename' para escrita binária
#   # 3. Enviar RRQ para o servidor em server_addr
#   # 4. Esperar por pacote enviado pelo servidor [1]
#   #         4.1 Extrair opcode do pacote recebido
#   #         4.2 Se opcode for DAT:
#   #             a) Obter block_number e data (ie, o bloco de dados) (UNPACK)
#   #             b) Se block_number não for next_block_number ou
#   #                next_block_number - 1 => ERRO de protocolo [2]
#   #             c) Se block_number == next_block_number [3], gravamos
#   #                bloco de dados no ficheiro e incrementamos next_block_number
#   #             d) Enviar ACK reconhecendo o último pacote recebido
#   #             e) Se bloco de dados < 512, terminar o RRQ
#   #          4.3 Se pacote for ERR: assinalar o erro lançando a excepção apropriada
#   #          4.4 Se for outro tipo de pacote: assinalar ERRO de protocolo
#   #          4.5 Voltar a 4
#   #
#   # [1] Terminar quando dimensão do bloco de dados do pacote
#   #     DAT for < 512 bytes (ou se ocorrer um erro)
#   # [2] next_block_number indica o próximo block_number, contador
#   #     inicializado a 1 antes do passo 4.
#   # [3] Isto quer dizer que recebemos um novo DAT.
#
#def put_file(server_addr: INET4Address, filename: str):
#    print(f"Enviar ficheiro para {server_addr} ")
    
def get_file( port: int, server: str, serverip: str, origin: str, destination: str ):
    """
    This method is responsible for downloading the selected file from server.
    """
    plug = ( serverip, port )
    sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
#    sock.settimeout( INACTIVITY_TIMEOUT )
    sock.settimeout( int( INACTIVITY_TIMEOUT / MAX_ATTEMPTS ) )
    msg = pack_rrq( origin )
    intAttempt = 1
    intBlock = 0
    intFileSize = 0
    intStatusCode = 3
    hide_cursor()
    try:
        with open( destination, "wb") as file:
            while True:
                try:
                    sock.sendto( msg, plug )
                    packet, plug = sock.recvfrom( DEFAULT_BUFFER_SIZE )
                    if unpack_opcode( packet ) == DAT:
                        intBlockDat, data = unpack_dat( packet )
                        if intBlockDat == intBlock + 1:
                            intFileSize += len( data )
                            if origin != "dir.txt":
                                logit( 4, f"Receiving...{intFileSize} bytes.", intStatusCode == 4 )
                                intStatusCode = 4
                            intAttempt = 1
                            intBlock += 1
                            msg = pack_ack( intBlock )
                            file.write( data )
                            if len( data ) < MAX_DATA_LEN:
                                break
                        else:
                            err_msg = f"Bad transfer: block {intBlockDat} instead of {intBlock + 1}."
                            raise TFTPGeneralError(err_msg)
                    elif unpack_opcode( packet ) == ERR:
                        error_code, error_msg = unpack_err( packet )
                        err_msg = f"\n\nError {error_code}: {error_msg}"
                        raise TFTPGeneralError(err_msg)
                except TimeoutError:
                    if intStatusCode == 3:
                        err_msg = f"Could not establish connection to {plug[0]}:{plug[1]}."
                        raise TimeoutError( err_msg )
                    else:
                        if intAttempt >= MAX_ATTEMPTS:
                            err_msg = f"Block {intBlock} lost. Maximum retry attempts reached."
                            raise TimeoutError( err_msg )
                        logit( 5, f"Block {intBlock} lost. Retransmitting...{intAttempt}",
                              intStatusCode == 5 )
                        intStatusCode = 5
                        intAttempt += 1
    except:
        if os.path.isfile( destination ) == True:
            os.remove( destination )
        raise
    sock.close()
    if intFileSize == ( intBlock - 1 ) * MAX_DATA_LEN + len(data):
        if origin != "dir.txt":
            print( f"\rReceived file '{origin}' {intFileSize} bytes.\n", flush=True )
    else:
        err_msg = f"Size mismatch: bad transfer. Try again"
        raise TFTPGeneralError(err_msg)
    show_cursor()
#    print( f"tftp get -p {port} {serverip} {origin} {destination}" )

def put_file( port: int, server: str, serverip: str, origin: str, destination: str ):
    """
    This method is responsible for uploading the selected file to server.
    """
    plug = ( serverip, port )
    sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
#    sock.settimeout( INACTIVITY_TIMEOUT )
    sock.settimeout( int( INACTIVITY_TIMEOUT / MAX_ATTEMPTS ) )
    intFileSize = os.path.getsize( origin )
    msg = pack_wrq( destination )
    intAttempt = 1
    intBlock = 0
    intStatusCode = 0
    hide_cursor()
    with open( origin, "rb") as file:
        while True:
            try:
                sock.sendto( msg, plug )
                packet, plug = sock.recvfrom( DEFAULT_BUFFER_SIZE )
                if unpack_opcode( packet ) == ACK:
                    intBlockAck = unpack_ack( packet )
                    if intBlockAck == intBlock:
                        floDone = file.tell() / intFileSize
                        logit( 1, f"Sending...{int( floDone * 100 )}%", intStatusCode == 1 )
                        intStatusCode = 1
                        intAttempt = 1
                        intBlock += 1
                        binData = file.read(MAX_DATA_LEN)
                        if not binData:
                            if len( msg ) == MAX_DATA_LEN + 4:
                                msg = pack_dat( intBlock, b"" )
                            else:
                                break
                        else:
                            msg = pack_dat( intBlock, binData )
                    elif intBlockAck == intBlock - 1:
                        continue
                    else:
                        err_msg = f"Bad transfer: block {intBlockAck} instead of {intBlock}."
                        raise TFTPGeneralError(err_msg)
                    if len( msg ) < MAX_DATA_LEN + 4:
                        sock.sendto( msg, plug )
                        break
                elif unpack_opcode( packet ) == ERR:
                    error_code, error_msg = unpack_err( packet )
                    err_msg = f"\n\nError {error_code}: {error_msg}"
                    raise TFTPGeneralError(err_msg)
            except TimeoutError:
                if intStatusCode == 0:
                    err_msg = f"Could not establish connection to {plug[0]}:{plug[1]}."
                    raise TimeoutError( err_msg )
                else:
                    if intAttempt >= MAX_ATTEMPTS:
                        err_msg = f"Block {intBlock} lost. Maximum retry attempts reached."
                        raise TimeoutError( err_msg )
                    logit( 2, f"Block {intBlock} lost. Retransmitting...{intAttempt}",
                          intStatusCode == 2 )
                    intStatusCode = 2
                    intAttempt += 1
    sock.close()
    if intFileSize == ( intBlock - 1 ) * MAX_DATA_LEN + len( binData ):
        print( f"Sent file '{origin}' {intFileSize} bytes.\n" )
    else:
        err_msg = "Size mismatch: bad transfer. Try again"
        raise TFTPGeneralError(err_msg)
    show_cursor()
#    print( f"tftp put -p {port} {serverip} {origin} {destination}" )

##############################################################
##                                                          ## 
##              PACKET PACKING AND UNPACKING                ##
##                                                          ##
############################################################## 

def pack_rrq(filename: str, mode: str = DEFAULT_MODE) -> bytes:
    return _pack_rrq_wrq(RRQ, filename, mode)

def pack_wrq(filename: str, mode: str = DEFAULT_MODE) -> bytes:
    return _pack_rrq_wrq(WRQ, filename, mode)

def _pack_rrq_wrq(opcode: int, filename: str, mode: str = DEFAULT_MODE) -> bytes:
    if not is_ascii_printable(filename):
        raise TFTPValueError(f"Invalid filename: {filename}. Not ASCII printable")
    filename_bytes = filename.encode() + b'\x00'
    mode_bytes = mode.encode() + b'\x00'
    fmt = f'!H{len(filename_bytes)}s{len(mode_bytes)}s'
    return struct.pack(fmt, opcode, filename_bytes, mode_bytes)

def unpack_rrq(packet: bytes) -> tuple[str, str]:
    return _unpack_rrq_wrq(RRQ, packet)

def unpack_wrq(packet: bytes) -> tuple[str, str]:
    return _unpack_rrq_wrq(WRQ, packet)

def _unpack_rrq_wrq(opcode: int, packet: bytes) -> tuple[str, str]:
    received_opcode = unpack_opcode(packet)
    if opcode != received_opcode:
        raise TFTPValueError(f'Invalid opcode: {received_opcode}. Expected opcode: {opcode}')
    delim_pos = packet.index(b'\x00', 2)
    filename = packet[2: delim_pos].decode()
    mode = packet[delim_pos + 1:-1].decode()
    return filename, mode

def pack_dat(block_number:int, data: bytes) -> bytes:
    if not 0 <= block_number <= MAX_BLOCK_NUMBER:
        err_msg = f'Block number {block_number} larger than allowed ({MAX_BLOCK_NUMBER})'
        raise TFTPValueError(err_msg)
    if len(data) > MAX_DATA_LEN:
        err_msg = f'Data size {block_number} larger than allowed ({MAX_DATA_LEN})'
        raise TFTPValueError(err_msg)
    
    fmt = f'!HH{len(data)}s'
    return struct.pack(fmt, DAT, block_number, data)

def unpack_dat(packet: bytes) -> tuple[int, bytes]:
    opcode, block_number = struct.unpack('!HH', packet[:4])
    if opcode != DAT:
        raise TFTPValueError(f'Invalid opcode {opcode}. Expecting {DAT=}.')
    return block_number, packet[4:]

def pack_ack(block_number: int) -> bytes:
    if not 0 <= block_number <= MAX_BLOCK_NUMBER:
        err_msg = f'Block number {block_number} larger than allowed ({MAX_BLOCK_NUMBER})'
        raise TFTPValueError(err_msg)
    
    return struct.pack(f'!HH', ACK, block_number)

def unpack_ack(packet: bytes) -> int:
    opcode, block_number = struct.unpack('!HH', packet)
    if opcode != ACK:
        raise TFTPValueError(f'Invalid opcode {opcode}. Expecting {DAT=}.')
    return block_number

def pack_err(error_code: int, error_msg: str | None = None) -> bytes:
    if error_code not in ERROR_MESSAGES:
        raise TFTPValueError(f'Invalid error code {error_code}')
    if error_msg is None:
        error_msg = ERROR_MESSAGES[error_code]
    error_msg_bytes = error_msg.encode() + b'\x00'
    fmt = f'!HH{len(error_msg_bytes)}s'
    return struct.pack(fmt, ERR, error_code, error_msg_bytes)

def unpack_err(packet: bytes) -> tuple[int, str]:
    opcode, error_code = struct.unpack('!HH', packet[:4])
    if opcode != ERR:
        raise TFTPValueError(f'Invalid opcode: {opcode}. Expected opcode: {ERR=}')
    return error_code, packet[4:-1].decode()

def unpack_opcode(packet: bytes) -> int:
    opcode, *_ = struct.unpack('!H', packet[:2])
    if opcode not in (RRQ, WRQ, DAT, ACK, ERR):
        raise TFTPValueError(f'Invalid opcode {opcode}')
    return opcode


###############################################################
##                                                           ##
##                  ERRORS AND EXCEPTIONS                    ##
##                                                           ##     
###############################################################

class TFTPValueError(ValueError):
    '''
    Protocol code errors.
    '''

class TFTPGeneralError(ValueError):
    """
    General transmission errors.
    """

###############################################################
##                                                           ##
##                     COMMON UTILITIES                      ##
##              Mostly related to network tasks              ##
##                                                           ##     
###############################################################
