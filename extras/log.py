import time, sys, os
from inspect import stack

def log_message(msg):
    """
    Logs a message with standard format
    """
    caller_frame = stack()[1]
    module = os.path.basename(caller_frame[0].f_globals.get('__file__', None))
    timestamp = time.strftime("%Y.%m.%d-%H:%M:%S ")
    log_message = "- [{0}] :: {1}"
    log_message = timestamp + log_message.format(module,msg)
    print (log_message, file=sys.stderr)
