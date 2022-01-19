import pyb
import time
import uasyncio as asyncio
import math

_GCONF				=const(0x00) 	#Global configuration flags
_X_COMPARE 			=const(0x05)	#Position  comparison  register
_IHOLD_IRUN			=const(0x10)	#Driver current control
_TPOWERDOWN         =const(0x11)
_TSTEP              =const(0x12)
_TPWMTHRS           =const(0x13)
_TCOOLTHRS			=const(0x14)	#This is the lower threshold velocity for switching on smart energy coolStep and stallGuard feature.
_THIGH              =const(0x15)
_RAMPMODE			=const(0x20)	#Driving mode (Velocity, Positioning, Hold)
_XACTUAL		    =const(0x21)	#Actual motor position
_VACTUAL 			=const(0x22)	#Actual  motor  velocity  from  ramp  generator
_VSTART				=const(0x23)	#Motor start velocity
_A_1				=const(0x24)	#First  acceleration  between  VSTART  and  V1
_V_1				=const(0x25)	#First  acceleration  /  deceleration  phase  target velocity
_AMAX				=const(0x26)	#Second  acceleration  between  V1  and  VMAX
_VMAX 				=const(0x27)	#This is the target velocity in velocity mode. It can be changed any time during a motion.
_DMAX				=const(0x28)	#Deceleration between VMAX and V1
_D_1				=const(0x2A) 	#Deceleration  between  V1  and  VSTOP
_VSTOP				=const(0x2B)	#Motor stop velocity (unsigned)
_TZEROWAIT			=const(0x2C)	#Defines  the  waiting  time  after  ramping  down
_XTARGET			=const(0x2D)	#Target position for ramp mode
_VDCMIN             =const(0x33)
_SW_MODE 			=const(0x34)	#Switch mode configuration
_RAMP_STAT			=const(0x35)	#Ramp status and switch event status
_XLATCH				=const(0x36)	#Latches  XACTUAL  upon  a programmable switch event
_ENCMODE            =const(0x38)    #编码器配置
_X_ENC              =const(0x39)    #获取编码器位置
_ENC_CONST          =const(0x3A)    #设置编码器因子 因子=200*256/编码器一圈脉冲数
_CHOPCONF			=const(0x6C)	#Chopper and driver configuration
_COOLCONF			=const(0x6D)	#coolStep smart current control register and stallGuard2 configuration
_DCCTRL             =const(0x6E)
_DRV_STATUS 		=const(0x6F)	#stallGuard2 value and driver error flags
_PWMCONF            =const(0x70)
_VZERO				=const(0x400)		# flag in RAMP_STAT, 1: signals that the actual velocity is 0.

class TMC5130():
    def __init__(self,spi_num=1,cs_pin=None,direction=0,iHold=4,iRun=15,iHoldDelay=6,amax=65535,stealthChop=1,swL=0,swR=0,swValid=0,ppmm=200*256,microstep=256,ENC=0):
        self.spi = pyb.SPI(spi_num, pyb.SPI.MASTER,prescaler=256,phase=1,polarity=1)
        self.tmc_cs=cs_pin
        
        self.tmc_cs.high()
        self.reg_status=0
        self.isHome=2 # 0为电机停止，1为电机正在运行， 2为电机没有回零

        self.posSpeed=50 # mm/s
        self.negSpeed=-50
        self.posTime=30 #ms
        self.negTime=30
        self.extrusionSpeed=0
        self.isExtrusion=0
        self.ppmm=ppmm
        # microstep=int(ppmm/200)

        #                     开启左限位    开启右限位   左限位极性     右限位极性
        self.writeReg(_SW_MODE, ((swL<<0) | (swR<<1) | (swValid<<2) | (swValid<<3))) 
        self.writeReg(_IHOLD_IRUN, (iHold<<0) | (iRun<<8) | (iHoldDelay<<16))
        #                    电流扫描  内部电阻    开启静音驱动        电机方向
        self.writeReg(_GCONF,(0<<0) | (0<<1) | (stealthChop<<2) | (direction<<4))

        # stealthChop电压PWM模式的上限速度
        self.writeReg(_TPWMTHRS, 30)
        #                        PWM_AMPL  PWM_GRAD  pwm_freq  pwm_autoscale
        self.writeReg(_PWMCONF, ((200<<0) | (1<<8) | (1<<16) | (1<<18)))

        if microstep==256:
            #                        TOFF     HSTART    HEND     disfdcc   rndtf      chm       TBL       vsense   高速斩波     细分
            self.writeReg(_CHOPCONF, ((3<<0) | (4<<4) | (1<<7) | (0<<12) | (0<<13) | (1<<14) | (1<<15) | (0<<17) | (0<<19) | (1<<28)))
        elif microstep==128:
            self.writeReg(_CHOPCONF, ((3<<0) | (4<<4) | (1<<7) | (0<<12) | (0<<13) | (1<<14) | (1<<15) | (0<<17) | (0<<19) | (1<<24)))
        elif microstep==64:
            self.writeReg(_CHOPCONF, ((3<<0) | (4<<4) | (1<<7) | (0<<12) | (0<<13) | (1<<14) | (1<<15) | (0<<17) | (0<<19) | (2<<24)))
        elif microstep==32:
            self.writeReg(_CHOPCONF, ((3<<0) | (4<<4) | (1<<7) | (0<<12) | (0<<13) | (1<<14) | (1<<15) | (0<<17) | (0<<19) | (3<<24)))
        elif microstep==16:
            self.writeReg(_CHOPCONF, ((3<<0) | (4<<4) | (1<<7) | (0<<12) | (0<<13) | (1<<14) | (1<<15) | (0<<17) | (0<<19) | (4<<24)))
        elif microstep==8:
            self.writeReg(_CHOPCONF, ((3<<0) | (4<<4) | (1<<7) | (0<<12) | (0<<13) | (1<<14) | (1<<15) | (0<<17) | (0<<19) | (5<<24)))
        elif microstep==4:
            self.writeReg(_CHOPCONF, ((3<<0) | (4<<4) | (1<<7) | (0<<12) | (0<<13) | (1<<14) | (1<<15) | (0<<17) | (0<<19) | (6<<24)))
        elif microstep==2:
            self.writeReg(_CHOPCONF, ((3<<0) | (4<<4) | (1<<7) | (0<<12) | (0<<13) | (1<<14) | (1<<15) | (0<<17) | (0<<19) | (7<<24)))
        elif microstep==1:
            self.writeReg(_CHOPCONF, ((3<<0) | (4<<4) | (1<<7) | (0<<12) | (0<<13) | (1<<14) | (1<<15) | (0<<17) | (0<<19) | (8<<24)))

        self.writeReg(_AMAX, amax)
        self.writeReg(_DMAX, amax) # DMAX = 50000 Deceleration above V1
        self.writeReg(_A_1, amax)
        self.writeReg(_V_1, 0)
        self.writeReg(_D_1, amax)
        self.writeReg(_VSTOP, 10) # VSTOP = 10 Stop velocity (Near to zero)
        self.writeReg(_VSTART, 0)

        self.enc=ENC # 编码器一圈脉冲数*倍频数（4）
        if self.enc!=0:
            self.writeReg(_ENCMODE, 0x558) # 配置因子小数点为10进制模式(ABZ极性配置也在这里)
            # self.writeReg(_ENC_CONST, (21<<16)+3333) # 配置因子 600*4
            a=math.modf(microstep*200/self.enc)
            self.writeReg(_ENC_CONST, (int(a[1])<<16) + int(a[0]*10000) ) # 配置因子
            self.writeReg(_X_ENC, 0) # 编码器位置清零


    def writeReg(self,regaddr,data):
        self.tmc_cs.low()
        # ba=bytes([regaddr|0x80,0xFF&(data>>24),0xFF&(data>>16),0xFF&(data>>8),0xFF&data])
        # reg_val=self.spi.send_recv(ba)
        reg_val=self.spi.send_recv(regaddr|0x80)
        reg_val=self.spi.send_recv(0xFF&(data>>24))
        reg_val=self.spi.send_recv(0xFF&(data>>16))
        reg_val=self.spi.send_recv(0xFF&(data>>8))
        reg_val=self.spi.send_recv(0xFF&data)
        self.tmc_cs.high()
        self.reg_status=reg_val[0]

    def readReg(self,regaddr):
        self.tmc_cs.low()
        # ba=bytes([regaddr,0,0,0,0])
        # self.reg_status=self.spi.send_recv(ba)
        self.reg_status=self.spi.send_recv(regaddr)
        self.reg_status=self.spi.send_recv(0)
        self.reg_status=self.spi.send_recv(0)
        self.reg_status=self.spi.send_recv(0)
        self.reg_status=self.spi.send_recv(0)

        self.tmc_cs.high()
        time.sleep_us(30)
        self.tmc_cs.low()
        # reg_val=self.spi.send_recv(ba)
        reg_val=[0,0,0,0,0]
        reg_val[0]=self.spi.send_recv(regaddr)
        reg_val[1]=self.spi.send_recv(0)
        reg_val[2]=self.spi.send_recv(0)
        reg_val[3]=self.spi.send_recv(0)
        reg_val[4]=self.spi.send_recv(0)
        
        self.tmc_cs.high()
        self.reg_status=reg_val[0]
        return ord(reg_val[1])<<24 | ord(reg_val[2])<<16 | ord(reg_val[3])<<8 | ord(reg_val[4])

    def to32bit(self, num):
        if num < 0:
            num = num + 2**32
        return num

    def positionMode(self,velocity,position):
        self.setVelocity(velocity)
        # self.writeReg(_A_1, 50000)
        # self.writeReg(_D_1, 50000)
        self.writeReg(_V_1, int(velocity*self.ppmm))
        position=self.to32bit(int(position*self.ppmm))
        self.writeReg(_RAMPMODE, 0) # RAMPMODE = 0 (Target position move)
        self.writeReg(_XTARGET, int(position))
        # print(self.readReg(XACTUAL)/self.ppmm)

    def velocityMode(self,velocity):
        self.setVelocity(velocity)
        if velocity<0:
            self.writeReg(_RAMPMODE, 2) # RAMPMODE = 2 (Target velocity move)
        else:
            self.writeReg(_RAMPMODE, 1) # RAMPMODE = 1 (Target velocity move)

    def setVelocity(self,velocity):
        # velocityPP=int(abs(velocity)*self.ppmm)
        if velocity==0:
            velocityPP=0
        else:
            velocityPP=int(abs(velocity)*self.ppmm/(16000000/2/(1<<23))) # 51200/(16000000/2/(1<<23))
        self.writeReg(_VMAX, velocityPP) # VMAX

    def getVelocityStatus(self):
        if self.isHome==2:
            return 2 # 电机没有执行回零
        
        elif self.isHome==1: #电机正在回零
            if self.readSWL()==1: #触发光电门
                self.writeReg(_XACTUAL,0) # 设置电机实际为0
                self.setVelocity(0)
                self.isHome=0
            return 1

        elif self.isHome==0: #电机回零成功
            if self.isExtrusion==1 or self.isExtrusion==3:
                return 3
            if (self.readReg(_RAMP_STAT) & _VZERO)>>10 ==0:
                return 1 # 电机正在运行
            else:
                return 0

    def readSWL(self):
        return self.readReg(_RAMP_STAT)&0x01

    def readSWR(self):
        return (self.readReg(_RAMP_STAT)&0x02)>>1

    def readPosition(self):
        return self.readReg(_XACTUAL)/self.ppmm
        # return self.to32bit(self.readReg(_XACTUAL))/self.ppmm

    def readENCPosition(self):
        data=self.readReg(_X_ENC)
        if data>(2**31-1):
            return (-((2**31-1)*2-data+2))/self.ppmm
        else:
            return data/self.ppmm

    def readVelocity(self):
        return self.readReg(_VACTUAL)/self.ppmm*(16000000/2/(1<<23))

    def home(self,velocity):
        self.isHome=1
        self.velocity=velocity
        self.readSWL() # 初次读取寄存器值，刷新
        self.setVelocity(velocity)
        self.writeReg(_RAMPMODE, 2)
        # print("HOME START")

    async def extrusionExec(self,isExtrusion):
        self.isExtrusion=isExtrusion # 预压
        self.velocityMode(self.posSpeed)
        # time.sleep_ms(int(self.posTime))
        await asyncio.sleep_ms(int(self.posTime))
        self.setVelocity(self.extrusionSpeed)
        self.isExtrusion=2 #正常出丝

    async def extrusionStop(self,isExtrusion):
        self.isExtrusion=isExtrusion #卸压
        self.velocityMode(self.negSpeed)
        # time.sleep_ms(int(self.negTime))
        await asyncio.sleep_ms(int(self.negTime))
        self.setVelocity(0)
        self.isExtrusion=0 #停止

    def stopMove(self):
        self.setVelocity(0)
        self.isExtrusion=0

    def stallGuardHome(self,velocity,tcool=300,sgt=0,sfilt=0):
        self.isHome=1
        self.velocity=velocity

        # 设置无传感回零的速度下限值，大于这个速度才生效，即小于这个时间值。
        self.writeReg(_TCOOLTHRS, tcool)
        
        # 设置SGT灵敏度(-64 ~ 63)，值越小灵敏度越高，sfilt 是否启动过滤器
        self.writeReg(_COOLCONF, ((sgt<<16) | (sfilt<<24)))

        # 开启sg_stop功能
        self.writeReg(_SW_MODE, ( (self.readReg(_SW_MODE)) | (1<<10))) 

        self.readSWL() # 初次读取寄存器值，刷新
        self.setVelocity(velocity)
        self.writeReg(_RAMPMODE, 2)

    def stallGuardStatus(self):
        if self.isHome==2:
            return 2 # 电机没有执行回零
        
        elif self.isHome==1: #电机正在回零
            if (self.readReg(_RAMP_STAT)>>6)&0x01 ==1: #触发无传感回零电流
                self.writeReg(_XACTUAL,0) # 设置电机实际为0
                self.setVelocity(0)
                self.writeReg(_SW_MODE, ( (self.readReg(_SW_MODE)) & 0xBFF)) # 关闭sg_stop功能
                self.isHome=0
                self.writeReg(_XACTUAL,0) # 设置电机实际为0
            return 1

        elif self.isHome==0: #电机回零成功
            if self.isExtrusion==1 or self.isExtrusion==3:
                return 3
            if (self.readReg(_RAMP_STAT) & _VZERO)>>10 ==0:
                return 1 # 电机正在运行
            else:
                return 0

    # 读取电机运行时的频率时间
    def readTSTEP(self):
        return self.readReg(_TSTEP)

    def readSG_RESULT(self):
        return self.readReg(_DRV_STATUS)&0x3FF

    def setPosition(self,position):
        position=self.to32bit(int(position*self.ppmm))
        self.writeReg(_XACTUAL,int(position)) # 设置电机位置
        self.setVelocity(0)
