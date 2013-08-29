#!/usr/bin/python

import sys
import os
import imp

import euca_image_validation

toCheck = []
retCode = 0

modDir = os.path.dirname(euca_image_validation.__file__)
sys.path.insert(0, modDir)

for root, dirs, files in os.walk(modDir):
    toCheck += ['%s/%s' % (root, x) for x in files]

toSource = [os.path.splitext(x)[0] for x in toCheck
            if (x.endswith('.py') and not x.endswith('/__init__.py'))]

mods = []

for modLong in toSource:
    mod = os.path.basename(modLong)
    (f, fn, d) = imp.find_module(mod)
    mods.append((os.path.basename(modLong), imp.load_module(mod, f, fn, d)))

if len(mods):
    imageHandle = euca_image_validation.ImageAccess(trace=False)
else:
    sys.exit(0)

for mod in mods:
    success = False
    # FIXME: Optionally spit out a success matrix?
    try:
        success = mod[1].validator(imageHandle)
    except Exception as e:
        imageHandle.vprint("Exception validating '%s' (%s): %s" % (mod[0],
                                                                   e.__doc__,
                                                                   e))
    if not success:
        imageHandle.vprint('Failed to validate: %s' % mod[0])
        retCode = 1

# Necessary to prevent stale/disconnected FUSE mount.
# See documentation for ImageAccess.__del__().
imageHandle.__del__()

sys.exit(retCode)
