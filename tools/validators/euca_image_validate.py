#!/usr/bin/python

import sys
import os
import imp

import euca_image_validation

toCheck = []
retCode = 0

# FIXME: clean up the module-path searching/handling.
for root, dirs, files in os.walk(os.path.dirname(euca_image_validation.__file__)):
    toCheck += ['%s/%s' % (root, x) for x in files]

toSource = [os.path.splitext(x)[0] for x in toCheck if (x.endswith('.py') and not x.endswith('/__init__.py'))]

mods = []
for modLong in toSource:
    mod = '%s/%s' % ('euca_image_validation', os.path.basename(modLong))
    (f, fn, d) = imp.find_module(mod)
    mods.append((os.path.basename(modLong), imp.load_module(mod, f, fn, d)))

if len(mods):
    imageHandle = euca_image_validation.ImageAccess(trace=False)
else:
    sys.exit(0)

for mod in mods:
    success = mod[1].validator(imageHandle)

    if not success:
        imageHandle.vprint('Failed to validate: %s' % mod[0])
        retCode = 1

del imageHandle

sys.exit(retCode)
