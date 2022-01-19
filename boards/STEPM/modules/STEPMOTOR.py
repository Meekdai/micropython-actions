import pyb
import machine
import time
import ujson
import gc
import logging
logger = logging.getLogger("--STEPMOTOR.py--")

import tmc5130
import uasyncio as asyncio
import fram_i2c
import struct

class BOARD():
    def __init__(self,loop):
        
        logger.info('INIT STEPMOTOR BOARD')
        self.loop=loop
        self.webRun=False
        self.sendBuf=ujson.loads('{"wsProtocol": "automaticSend"}')

        self.gtim = pyb.Timer(12) #选择LED 闪烁定时器
        self.gled = pyb.LED(2) # Web连接LED
        self.gled.on()
        time.sleep_ms(300) #LED 在开机时短亮
        self.gled.off()

        self.yled = pyb.LED(3) # FRAM报错
        self.yled.off()
        self.bled = pyb.LED(4) #程序运行出错
        self.bled.off()

        self.isTMCRun=0 # 协程标志位
        self.isTMCfindZ=0 # 找零标志位

        self.fram=fram_i2c.FRAM(machine.I2C(1))
        if self.fram[0]==10:
            logger.info('FRAM INIT OK WITH NEW')
            self.readFramAll()

        elif self.fram[0]==20:
            self.readFramAll()
            self.isTMCfindZ=2
            logger.info('FRAM INIT OK WITH OLD')
        else:
            logger.info('FRAM DATA ERROR')
            self.yled.on()
            self.sendBuf["CR"]=0
            self.sendBuf["CV"]=0
            self.sendBuf["TR"]=0
            self.sendBuf["TV"]=0
            self.ENCR=0

        # self.MOS1=pyb.Pin('X1', pyb.Pin.OUT_PP, pyb.Pin.PULL_DOWN)
        # self.MOS2=pyb.Pin('X2', pyb.Pin.OUT_PP, pyb.Pin.PULL_DOWN)
        # self.MOS1.low()
        # self.MOS2.low()

        # self.MAX_CS=pyb.Pin('X5', pyb.Pin.OUT_PP, pyb.Pin.PULL_UP)

        # self.TMC_CS=pyb.Pin('X11', pyb.Pin.OUT_PP, pyb.Pin.PULL_UP) #OCT
        self.TMC_CS=pyb.Pin('X4', pyb.Pin.OUT_PP, pyb.Pin.PULL_UP)

        # self.MAX_CS.high()
        self.TMC_CS.high()

        # self.TMC_EN=pyb.Pin('X5', pyb.Pin.OUT_PP, pyb.Pin.PULL_UP) #OCT
        self.TMC_EN=pyb.Pin('Y11', pyb.Pin.OUT_PP, pyb.Pin.PULL_UP)

        self.TMC_EN.low()

        self.TMC1=tmc5130.TMC5130(spi_num=1,cs_pin=self.TMC_CS,direction=0,iHold=1,iRun=15,iHoldDelay=4,amax=100,stealthChop=1,swL=0,swR=0,swValid=0,ppmm=200*16,microstep=16,ENC=1000*4) #出丝A
        self.TMC1.isHome=0
        # time.sleep_ms(100)
        # self.TMC1.positionMode(2,10)

        self.timeFlag=0
        self.adcall = pyb.ADCAll(12, 0x70000)

        # extint = pyb.ExtInt(pyb.Pin("X17"), pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_DOWN, self.ExtENCZ)
        extint = pyb.ExtInt(pyb.Pin("X5"), pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, self.ExtENCZ)

    def automaticSend(self):
        if self.timeFlag:
            self.timeFlag=0
            self.sendBuf["cpuTime"]=int(time.ticks_ms()/1000)
            self.sendBuf["cpuTemp"]=self.adcall.read_core_temp()
            # self.sendBuf["CR"]=self.TMC1.readPosition()
            self.sendBuf["CR"]=self.ENCR+abs(self.TMC1.readENCPosition())
            self.sendBuf["CV"]=self.TMC1.readVelocity()
            self.sendBuf["result"]="OK"
            return self.sendBuf

    def tick(self,timer):
        self.gled.toggle()
        self.timeFlag=1

    def executionJson(self,data):
        # self.automaticSend()
        if data["wsProtocol"]=="start" and self.webRun==False:
            self.webRun=True
            data["result"]="OK"
            data["board"]="STEPMOTOR"
            data["Version"]="1.1"
            data["Fstatus"]=self.fram[0]
            data["MCU"]="STM32F405RGT6"
            data["ID"]='%02x' %pyb.unique_id()[0] + '%02x-' %pyb.unique_id()[1] +'%02x' %pyb.unique_id()[2] + '%02x-' %pyb.unique_id()[3] +'%02x' %pyb.unique_id()[4] + '%02x-' %pyb.unique_id()[5] +'%02x' %pyb.unique_id()[6] + '%02x-' %pyb.unique_id()[7] +'%02x' %pyb.unique_id()[8] + '%02x-' %pyb.unique_id()[9] +'%02x' %pyb.unique_id()[10] + '%02x' %pyb.unique_id()[11]
            data["remarks"]="此单板为步进电机控制板"
            data["status"]=self.TMC1.getVelocityStatus()
            data["DIR"]=self.sendBuf["DIR"]
            self.gtim.init(freq=1) # 设置LED 以1HZ频率闪烁
            self.gtim.callback(self.tick)

            logger.info('WEB CONNECT SUCCESS')
            return data

        elif data["wsProtocol"]=="start" and self.webRun==True:
            data["result"]="ERROR"
            data["message"]="You should only send 'start' once in the initial connection."
            return data

        elif data["wsProtocol"]=="boot" and self.webRun==True:
            logger.info('BOOT STEPMOTOR BOARD')
            pyb.bootloader()

        elif data["wsProtocol"]=="ramUsage" and self.webRun==True:
            gc.collect()
            data["result"]="OK"
            data["ramFree"]=gc.mem_free()
            data["ramAlloc"]=gc.mem_alloc()
            data["percent"]="%.2f%%" % (data["ramAlloc"]/(data["ramFree"]+data["ramAlloc"])*100)
            return data

        elif data["wsProtocol"]=="getTimeStamp":
            data["result"]="OK"
            data["timeStamp"]=787986456465
            return data

        elif data["wsProtocol"]=="webClose":
            data["result"]="OK"
            logger.info('WEB CONNECT CLOSED')
            self.webRun=False
            self.gtim.deinit()
            self.gled.on()
            # self.stopAll()
            return data

        #设置TMC5130电机绝对位置移动参数
        elif data["wsProtocol"]=="TMCMoveParameter" and self.webRun==True:
            if data["num"]==1:
                self.sendBuf["TR"]=data["STR"]
                self.sendBuf["TV"]=data["STV"]
                # self.sendBuf["DIR"]=data["DIR"]
            else:
                data["result"]="ERROR"
                data["message"]="TMC num ERROR"
                return data
            data["result"]="OK"
            return data

        #设置TMC5130电机绝对位置移动
        elif data["wsProtocol"]=="TMCMove" and self.webRun==True:
            if data["num"]==1:
                # self.TMC1.positionMode(self.sendBuf["TV"],self.sendBuf["TR"])
                if self.isTMCRun==0:
                    self.loop.create_task(self.runPosition())
                else:
                    self.TMC1.setVelocity(self.sendBuf["TV"])

            else:
                data["result"]="ERROR"
                data["message"]="TMC num ERROR"
                return data
            data["result"]="OK"
            return data

        #设置TMC5130电机当前位置
        elif data["wsProtocol"]=="TMCSetPosition" and self.webRun==True:
            if data["num"]==1:
                self.TMC1.setPosition(data["SCR"])
            if data["SCR"]==0:
                self.sendBuf["DIR"]=data["DIR"]
                self.loop.create_task(self.findZ())
            data["result"]="OK"
            return data

        #获取TMC5130电机是否停止运动
        elif data["wsProtocol"]=="TMCStatus" and self.webRun==True:
            if data["num"]==1:
                data["status"]=self.TMC1.getVelocityStatus()
            data["result"]="OK"
            return data

        #停止TMC5130电机
        elif data["wsProtocol"]=="TMCStop" and self.webRun==True:
            if data["num"]==1:
                self.TMC1.stopMove()
                self.isTMCRun=0
            data["result"]="OK"
            return data

        #暂停TMC5130电机
        elif data["wsProtocol"]=="TMCPause" and self.webRun==True:
            if data["num"]==1:
                self.TMC1.stopMove()
            data["result"]="OK"
            return data

        else:
            data["result"]="ERROR"
            data["message"]="wsProtocol is not defined or 'start' is not run at once."
            return data

    def stopAll(self):
        if self.webRun==True:
            logger.info('STOP STEPMOTOR BOARD')
            self.gtim.deinit()
            self.gled.on()
            self.webRun=False

    def ExtENCZ(self,line):
        if self.isTMCRun:
            self.ENCR=self.ENCR+1
            # print(self.ENCR)
        elif self.isTMCfindZ==0:
            self.isTMCfindZ=1

    async def findZ(self):
        if self.sendBuf["DIR"]==0:
            self.TMC1.writeReg(0x00,(0<<0) | (0<<1) | (1<<2) | (1<<4))
        else:
            self.TMC1.writeReg(0x00,(0<<0) | (0<<1) | (1<<2) | (0<<4))

        self.TMC1.setPosition(0)
        self.TMC1.positionMode(0.2,1.5)
        self.isTMCfindZ=0
        while True:
            if self.isTMCfindZ==1:
                self.TMC1.stopMove()
                self.TMC1.setPosition(0)
                logger.info('Find Z Success')
                break
            if self.TMC1.readVelocity()==0:
                logger.error('Find No Z')
                return False

            await asyncio.sleep_ms(10)

        self.cleanFramAll()
        self.isTMCfindZ=2

    async def runPosition(self):
        if self.sendBuf["TR"]==0 or self.sendBuf["TV"]==0:
            logger.info('Please set TR and TV')
            return False

        # if self.isTMCfindZ!=2 or :
        #     logger.error('Please set zero')
        #     return False

        if self.sendBuf["DIR"]==0:
            self.TMC1.writeReg(0x00,(0<<0) | (0<<1) | (1<<2) | (1<<4))
        else:
            self.TMC1.writeReg(0x00,(0<<0) | (0<<1) | (1<<2) | (0<<4))

        self.writeFramTV() # 开始运行前，保存目标参数
        self.writeFramTR()

        onePlan=300000 # 一次写入TMC旋转的圈数
        self.isTMCRun=1
        self.fram[0]=20
        while self.isTMCRun:

            if self.sendBuf["TR"]==self.ENCR:
                logger.info('Run Plan is successed')
                self.fram[0]=10
                break

            if abs(self.sendBuf["TR"]-self.ENCR)<=onePlan:
                self.TMC1.setPosition(0)
                self.TMC1.positionMode(self.sendBuf["TV"],abs(self.sendBuf["TR"]-self.ENCR))
                while self.isTMCRun:
                    if self.ENCR!=struct.unpack('>I',self.fram[105:109])[0]:
                        self.writeFramCR()
                    
                    if self.sendBuf["TR"]==self.ENCR:
                        self.TMC1.stopMove()
                        break
                    
                    await asyncio.sleep_ms(10)

            else:
                self.TMC1.setPosition(0)
                self.TMC1.positionMode(self.sendBuf["TV"],onePlan)
                while self.isTMCRun:
                    if self.ENCR!=struct.unpack('>I',self.fram[105:109])[0]:
                        self.writeFramCR()

                    if self.TMC1.readPosition()==onePlan:
                        self.TMC1.stopMove()
                        break
                    else:
                        await asyncio.sleep_ms(10)
        
        self.TMC1.stopMove()
        self.writeFramCR()
        logger.info('runPosition asyncio end')
        self.isTMCRun=0

    def readFramAll(self):
        self.sendBuf["TV"]=self.fram[1]/10
        self.sendBuf["DIR"]=self.fram[2]

        self.sendBuf["TR"]=struct.unpack('>I',self.fram[100:104])[0]
        self.sendBuf["CR"]=struct.unpack('>I',self.fram[105:109])[0]
        self.ENCR=self.sendBuf["CR"]

    def writeFramTV(self):
        self.fram[1]=int(abs(self.sendBuf["TV"]*10)) # 1.4 (14)
        self.fram[2]=self.sendBuf["DIR"]

    def writeFramTR(self):
        self.fram[100:104]=struct.pack('>I',self.sendBuf["TR"]) # 42亿 4字节存储

    def writeFramCR(self):
        # logger.info('writeFramCR')
        self.fram[105:109]=struct.pack('>I',self.ENCR) # 42亿 4字节存储

    def cleanFramAll(self):
        self.fram[0]=10
        self.fram[1]=0
        self.fram[100:104]=struct.pack('>I',0)
        self.fram[105:109]=struct.pack('>I',0)
        self.sendBuf["CR"]=0
        self.sendBuf["CV"]=0
        self.sendBuf["TR"]=0
        self.sendBuf["TV"]=0
        self.ENCR=0
