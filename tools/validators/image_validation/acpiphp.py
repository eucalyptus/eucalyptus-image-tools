import os
import sys
from image_validation import ImageAccess

def validator(trace=False):
    val = ImageAccess(trace)
    #import epdb ; epdb.st()
    modules = os.walk('%s/lib/modules/' % val.mountpoint)
    acpiphp = [x for x in modules if 'acpiphp.ko' in x[2]]

    del val

    if len(acpiphp):
        sys.exit(0)
    else:
        sys.exit(1)
