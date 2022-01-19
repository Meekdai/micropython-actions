include("$(MPY_DIR)/extmod/uasyncio/manifest.py")
freeze("$(BOARD_DIR)/modules", ("logging.py", "bdevice.py", "tmc5130.py", "ws.py", "STEPMOTOR.py", "fram_i2c.py", "web.py"))
