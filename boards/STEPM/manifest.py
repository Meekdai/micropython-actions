include("$(MPY_DIR)/extmod/uasyncio/manifest.py")
freeze("$(BOARD_DIR)/modules", ("logging.py", "htmlserver.py", "tmc5130.py", "ws.py", "STEPMOTOR.py"))
