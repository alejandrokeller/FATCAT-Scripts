import time, sys

def log_message(module, msg):
    """
    Logs a message with standard format
    """
    timestamp = time.strftime("%Y.%m.%d-%H:%M:%S ")
    log_message = "- [{0}] :: {1}"
    log_message = timestamp + log_message.format(module,msg)
    print >>sys.stderr,log_message
