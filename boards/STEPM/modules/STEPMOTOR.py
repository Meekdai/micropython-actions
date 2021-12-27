import pyb
import time
import ujson
import gc
import logging
logger = logging.getLogger("--STEPMOTOR.py--")

import tmc5130
import uasyncio as asyncio

class BOARD():
    def __init__(self,loop):
        
        logger.info('INIT STEPMOTOR BOARD')
        self.loop=loop
        self.webRun=False
        self.sendBuf=ujson.loads('{"wsProtocol": "automaticSend"}')
        
        self.gtim = pyb.Timer(12) #选择LED 闪烁定时器
        self.gled = pyb.LED(2)
        self.gled.on()
        time.sleep_ms(300) #LED 在开机时短亮
        self.gled.off()

        self.MOS1=pyb.Pin('X1', pyb.Pin.OUT_PP, pyb.Pin.PULL_DOWN)
        self.MOS2=pyb.Pin('X2', pyb.Pin.OUT_PP, pyb.Pin.PULL_DOWN)
        self.MOS1.low()
        self.MOS2.low()

        self.MAX_CS=pyb.Pin('X5', pyb.Pin.OUT_PP, pyb.Pin.PULL_UP)
        self.TMC_CS=pyb.Pin('X4', pyb.Pin.OUT_PP, pyb.Pin.PULL_UP)
        self.MAX_CS.high()
        self.TMC_CS.high()

        self.TMC_EN=pyb.Pin('Y11', pyb.Pin.OUT_PP, pyb.Pin.PULL_UP)
        self.TMC_EN.low()

        self.TMC1=tmc5130.TMC5130(spi_num=1,cs_pin=self.TMC_CS,direction=0,iHold=1,iRun=8,iHoldDelay=4,stealthChop=1,swL=0,swR=0,swValid=0,ppmm=200*32,microstep=16) #出丝A
        self.TMC1.isHome=0
        # time.sleep_ms(100)
        # self.TMC1.positionMode(2,10)

        self.timeFlag=0
        self.adcall = pyb.ADCAll(12, 0x70000)
        self.sendBuf["CR"]=0
        self.sendBuf["CV"]=0
        self.sendBuf["TR"]=0
        self.sendBuf["TV"]=0

        self.cycle=0 # 每30万圈加1
        self.isTMCRun=0 # 协程标志位

    def automaticSend(self):
        if self.timeFlag:
            self.timeFlag=0
            self.sendBuf["cpuTime"]=int(time.ticks_ms()/1000)
            self.sendBuf["cpuTemp"]=self.adcall.read_core_temp()
            self.sendBuf["CR"]=self.TMC1.readPosition()
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
            data["hardwareVersion"]="VERA"
            data["softwareVersion"]="1.0"
            data["MCU"]="STM32F405RGT6"   
            data["ID"]='%02x' %pyb.unique_id()[0] + '%02x-' %pyb.unique_id()[1] +'%02x' %pyb.unique_id()[2] + '%02x-' %pyb.unique_id()[3] +'%02x' %pyb.unique_id()[4] + '%02x-' %pyb.unique_id()[5] +'%02x' %pyb.unique_id()[6] + '%02x-' %pyb.unique_id()[7] +'%02x' %pyb.unique_id()[8] + '%02x-' %pyb.unique_id()[9] +'%02x' %pyb.unique_id()[10] + '%02x' %pyb.unique_id()[11]
            data["remarks"]="此单板为步进电机控制板"
            data["status"]=self.TMC1.getVelocityStatus()
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

        #获取TMC5130电机当前位置
        elif data["wsProtocol"]=="TMCReadPosition" and self.webRun==True:
            if data["num"]==1:
                data["mm"]=self.TMC1.readPosition()+self.cycle*300000
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
                self.cycle=0
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

    async def runPosition(self):
        if self.sendBuf["TR"]==0 or self.sendBuf["TV"]==0:
            logger.info('Please set TR and TV')
            return False

        TR=self.sendBuf["TR"]
        self.isTMCRun=1

        while self.isTMCRun:
            if TR<=300000:
                self.TMC1.positionMode(self.sendBuf["TV"],self.sendBuf["TR"])
                break
            else:
                self.TMC1.positionMode(self.sendBuf["TV"],300000)
                TR=TR-300000
                while self.isTMCRun:
                    if self.TMC1.readPosition()==300000:
                        self.TMC1.setVelocity(0)
                        self.TMC1.setPosition(0)
                        self.cycle=self.cycle+1
                        break
                    else:
                        await asyncio.sleep_ms(50)
        
        logger.info('runPosition OK')
        self.isTMCRun=0


            