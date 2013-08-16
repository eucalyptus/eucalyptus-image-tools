#!/usr/bin/python

import sys
import os
import imp

from image_validation import ImageAccess

toCheck = []
retCode = 0

for root, dirs, files in os.walk('validation_modules'):
    toCheck += ['%s/%s' % (root, x) for x in files]

toSource = [os.path.splitext(x)[0] for x in toCheck if x.endswith('.py')]

mods = []
for mod in toSource:
    (f, fn, d) = imp.find_module(mod)
    mods.append((os.path.basename(mod), imp.load_module(mod, f, fn, d)))

if len(mods):
    imageHandle = ImageAccess(trace=False)
else:
    sys.exit(0)

for mod in mods:
    success = mod[1].validator(imageHandle)

    if not success:
        imageHandle.vprint('Failed to validate: %s' % mod[0])
        retCode = 1

del imageHandle

#import epdb ; epdb.st()

sys.exit(retCode)
