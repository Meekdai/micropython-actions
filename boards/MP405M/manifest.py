include("$(PORT_DIR)/boards/manifest.py")
freeze("$(PORT_DIR)/boards/MP405M/moudles", ("htmlserver.py", "logging.py", "tmc5130.py", "ws.py"))
