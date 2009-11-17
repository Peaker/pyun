import time
import sys

def debug_log(x):
    print time.time(), x
    sys.stdout.flush()

def warning(x):
    print >>sys.stderr, "Warning:", x
    sys.stderr.flush()
