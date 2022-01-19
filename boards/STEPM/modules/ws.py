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
# import htmlserver
# from uwebsocket import websocket
import web
import gc

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

##############################################
app = web.App(host='192.168.9.18', port=80)
logger.debug('WEB APP INIT OK')
##############################################
# WS_CLIENTS = set()
# /ws WebSocket route handler
@app.route('/ws')
async def ws_handler(r, w):
    # global WS_CLIENTS
    buf=''
    # upgrade connection to WebSocket
    ws = await web.WebSocket.upgrade(r, w)
    r.closed = False
    # add current client to set
    # WS_CLIENTS.add(ws)
    gc.collect()
    while ws.open and nic.isconnected():
        sendbuf=board.automaticSend()
        if sendbuf != None:
            # print(gc.mem_free())
            json=ujson.dumps(sendbuf)
            # print(json)
            try:
                await ws.send(json)
                # logger.debug("MCU-->PC : "+json)
            except:
                logger.debug("automaticSend error")
                break

        # handle ws events
        try:
            evt = await ws.recv()
        except:
            logger.debug("ws.recv error")
            continue

        if evt==None:
            continue

        # try:
        #     ujson.loads(evt, encoding='utf-8')
        # except ValueError:
        #     continue

        if evt['data']=='{"wsProtocol":"webClose"}':
            logger.debug("webClosed")
            break

        logger.debug(evt)
        if evt['type'] == 'close':
            logger.debug("ws close")
            ws.open = False
        elif evt['type'] == 'text':
            logger.debug("PC-->MCU : "+evt['data'])
            buf=buf+evt['data']
            if buf.find('}')!=-1:
                oneJson=buf[0:buf.find('}')]#获取最前面一条JSON数据
                buf=buf[buf.find('}')+1:]#截掉缓存中的这条数据
            else:
                continue

            try:
                data=ujson.loads(oneJson)
                IsJson=1
            except:
                IsJson=0
                await ws.send('JSON DATA ERROR')

            if IsJson==1:
                json=ujson.dumps(board.executionJson(data))
                await ws.send(json)
        else:
            pass
    # remove current client from set
    ws.open = False
    board.webRun = False
    del ws
    del buf
    gc.collect()
    # board.stopAll()
    # WS_CLIENTS.discard(ws)


try:
    loop.create_task(app.serve())
    loop.run_forever()
except KeyboardInterrupt:
    board.stopAll()
    logger.info("KeyboardInterrupt")
except:
    board.writeFramCR()
    board.TMC_EN.high()
    board.stopAll()
    board.bled.on()
