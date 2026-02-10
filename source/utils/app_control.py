import sys
import os
import subprocess
import logging

logger = logging.getLogger("Utils.AppControl")

def restart_application():
    
    logger.info("Initiating application restart...")
    
    try:
        if getattr(sys, 'frozen', False):
            executable = sys.executable
            args = [executable] + sys.argv[1:]
        else:
            executable = sys.executable
            args = [executable] + sys.argv

        logger.info(f"Restarting with execv: {executable} {args}")
        
        os.execv(executable, args)
        
    except Exception as e:
        logger.error(f"Failed to restart application: {e}")
        sys.exit(1)
