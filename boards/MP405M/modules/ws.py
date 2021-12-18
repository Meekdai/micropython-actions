import pyb
import time
import network
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("--ws.py--")

nic=network.WIZNET5K(pyb.SPI(2), pyb.Pin.board.Y5, pyb.Pin.board.Y1)

nic.ifconfig(('192.168.9.18', '255.255.255.0','192.168.9.12', '8.8.8.8'))

try:
    nic.active(0)
    nic.active(1)
except:
    pass

nic.ifconfig(('192.168.9.18', '255.255.255.0','192.168.9.12', '8.8.8.8'))
logger.debug('IP is being configured, please wait...')

####################################################################################################
# W5500复位后的初始化时间可以和以下代码导入时间并行
# import utelnetserver
# utelnetserver.start(nic)  # 启动Telnet服务器

# import uftpd
# uftpd.start(nic) # 启动FTP服务器

import ujson
import socket
import hashlib
import binascii
import htmlserver
from uwebsocket import websocket

import uasyncio as asyncio
loop = asyncio.get_event_loop(runq_len=20, waitq_len=20)

import STEPMOTOR
board=STEPMOTOR.BOARD(loop) #导入单板资源
####################################################################################################

while nic.ifconfig()[0]=='0.0.0.0':
    time.sleep_ms(100)
logger.debug('ifconfig OK')

logger.debug('Checking if the network cable connection is normal, please wait...')

nic.isconnected()
while nic.isconnected()==False:
    time.sleep_ms(100)
    logger.error('RJ45 Connected ERROR')

logger.debug('RJ45 Connected OK')

class WebSocketServer:
    def __init__(self, index_page, nic):
        self.nic = nic
        self._listen_s = None
        self._need_check = False
        self.client_close = False
        self._page = index_page
        self.htmlserver=htmlserver.htmlserver(index_page,nic)

    def notify(self, s):
        self._need_check = True

    def close(self):
        logger.debug("websocket closing client connection --- %s" % str(self.remote_addr))
        self.cl.setsockopt(socket.SOL_SOCKET, 20, None)
        self.cl.close()
        self.cl = None
        self.ws = None
        self.client_alive=0
        self._need_check = False
        self.client_close = False

    def read(self):
        if self._need_check:
            self._check_socket_state()
        msg_bytes = None
        try:
            msg_bytes = self.ws.read()
        except OSError:
            logger.error("websocket read error")
            self.client_close = True
        if not msg_bytes and self.client_close:
            self.close()
        return msg_bytes

    def write(self, msg):
        try:
            self.ws.write(msg)
        except OSError:
            logger.error("websocket write error")
            self.client_close = True

    def _check_socket_state(self):
        self._need_check = False
        sock_str = str(self.cl)
        state_str = sock_str.split(" ")[1]
        state = int(state_str.split("=")[1])
        if state == 4:
            self.client_close = True

    def _check_connected(self,check_time_us):
        if self.nic.isconnected():
            return True
        else:
            time.sleep_us(check_time_us)
            if self.nic.isconnected():
                return True
            else:
                logger.error("RJ45 connect error check %d us" % check_time_us)
                return False                

    def server_handshake(self,sock,data):
        for i in range(0,len(data.split("\r\n"))):
            if 'Sec-WebSocket-Key:' in data.split("\r\n")[i]:
                Sec_WebSocket_Key = data.split("\r\n")[i][19:]
                logger.debug("Sec_WebSocket_Key="+str(Sec_WebSocket_Key))
                break
        
        if not Sec_WebSocket_Key:
            raise OSError("Not a websocket request")

        d = hashlib.sha1(Sec_WebSocket_Key)
        d.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
        respkey = d.digest()
        respkey = binascii.b2a_base64(respkey)[:-1]
        logger.debug("respkey="+str(respkey))
        sock.send(b"HTTP/1.1 101 Switching Protocols\r")
        sock.send(b"Upgrade: websocket\r")
        sock.send(b"Connection: Upgrade\r")
        sock.send(b"Sec-WebSocket-Accept: ")
        sock.send(respkey)
        sock.send("\r\n\r\n")


    async def run(self,port):
        self._listen_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        addr = socket.getaddrinfo("0.0.0.0", port)[0][4]
        self._listen_s.bind(addr)
        self._listen_s.listen(5)
        board.gled.on()
        board.stopAll()
        while True:
            
            if self.nic.active():
                logger.debug("WebSocketServer started on ws://%s:%d" % (self.nic.ifconfig()[0], port))

            self.cl=None
            self.remote_addr=None

            self.cl, self.remote_addr = self._listen_s.accept()
            logger.debug("HTTP connection from: %s" % str(self.remote_addr))
            requested_file = None

            self.cl.settimeout(2)
            try:
                data = self.cl.recv(1024).decode()
                # logger.debug(data)
            except:
                logger.error("data recv error")
                continue

            if data and "Upgrade: websocket" in data.split("\r\n"): # 协议为websocket
                self.server_handshake(self.cl,data)
             
            elif data and "GET" == data.split(" ")[0]: # 协议为 HTTP GET
                requested_file = data.split(" ")[1].split("?")[0]
                requested_file = self._page if requested_file in [None, "/"] else requested_file
                logger.debug('GET requested_file= %s' % str(requested_file))
                if requested_file and requested_file.endswith(b'/')==False and '.' in requested_file:
                    self.cl.setblocking(True)
                    self.htmlserver._serve_file(requested_file, self.cl)
                elif requested_file and requested_file.endswith(b'/')==True:
                    self.cl.setblocking(True)
                    self.htmlserver._serve_dir(requested_file, self.cl)
                else:
                    self.htmlserver._generate_static_page(self.cl, 500, "500 Internal Server Error [2]")
                continue
            
            elif data and ("PUT" == data.split(" ")[0] or "POST" == data.split(" ")[0]): # 协议为 HTTP PUT POST
                content_length = 0
                requested_file = data.split(" ")[1].split("?")[0]
                requested_file = self._page if requested_file in [None, "/"] else requested_file
                logger.debug('PUT requested_file= %s' % str(requested_file))

                for i in range(0,len(data.split("\r\n"))):
                    if 'Content-Length:' in data.split("\r\n")[i]:
                        content_length = int(data.split("\r\n")[i][16:])
                        # logger.debug(content_length)
                        break

                if content_length!=0:
                    self.cl.setblocking(True)
                    self.htmlserver._save_put_request(self.cl,content_length)
                continue
            
            else:
                logger.debug('error request')
                logger.debug('data='+str(data))
                continue

            self._need_check = False
            self.cl.setblocking(False)
            self.cl.setsockopt(socket.SOL_SOCKET, 20, self.notify)
            self.ws = websocket(self.cl)

            self.buf=''
            self.IsJson=0
            self.client_alive=1
            logger.debug("WebSocket connecting on ws://%s:%d -- %d" % (self.remote_addr[0], port,self.remote_addr[1]))

    
    # async def clientRun(self):
            while self.client_alive and self._check_connected(500):
                await asyncio.sleep_ms(10)
                # try:
                sendbuf=board.automaticSend()
                if sendbuf != None:
                    json=ujson.dumps(sendbuf)
                    self.write(json)

                msg=self.read()
                if msg==b'{"wsProtocol":"webClose"}':
                    self.client_alive=0

                if msg:
                    logger.debug(msg)
                    self.buf=self.buf+msg.decode("utf-8")
                if self.buf.find('}')!=-1:
                    oneJson=self.buf[0:self.buf.find('}')]#获取最前面一条JSON数据
                    self.buf=self.buf[self.buf.find('}')+1:]#截掉缓存中的这条数据
                else:
                    continue
                try:
                    data=ujson.loads(oneJson)
                    self.IsJson=1
                except:
                    self.IsJson=0
                    self.write('JSON DATA ERROR')

                if self.IsJson==1:
                    json=ujson.dumps(board.executionJson(data))
                    self.write(json)

                # except:
                #     logger.error("websocket client process error")
                #     self.close()

            try:
                self.ws.close()
                self.ws=None
            except:
                logger.error("websocket close error")

server=WebSocketServer('/flash/index.html',nic)

try:
    loop.create_task(server.run(80))
    loop.run_forever()
except KeyboardInterrupt:
    board.stopAll()
    logger.info("KeyboardInterrupt")


