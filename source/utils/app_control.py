import sys
import os
import subprocess
import logging

logger = logging.getLogger("Utils.AppControl")

def restart_application():
    
    logger.info("Initiating application restart...")
    
    try:
        python = sys.executable
        args = sys.argv[:]
        
        if not getattr(sys, 'frozen', False):
            cmd = [python] + args
        else:
            cmd = args

        logger.info(f"Restart command: {cmd}")
        
        subprocess.Popen(cmd)
        
        logger.info("Exiting current process...")
        os._exit(0)
        
    except Exception as e:
        logger.error(f"Failed to restart application: {e}")
        sys.exit(1)
