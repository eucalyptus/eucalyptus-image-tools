#!/usr/bin/python

import sys
import os
import imp

import euca_image_validation

to_check = []
ret_code = 0

mod_dir = os.path.dirname(euca_image_validation.__file__)
sys.path.insert(0, mod_dir)

for root, dirs, files in os.walk(mod_dir):
    to_check += ['%s/%s' % (root, x) for x in files]

to_source = [os.path.splitext(x)[0] for x in to_check
            if (x.endswith('.py') and not x.endswith('/__init__.py'))]

mods = []

for mod_long in to_source:
    mod = os.path.basename(mod_long)
    if mod.startswith('.#'):
        # Silently skip Emacs auto-save files.
        continue
    (f, fn, d) = imp.find_module(mod)
    mods.append((os.path.basename(mod_long), imp.load_module(mod, f, fn, d)))

if len(mods):
    image_handle = euca_image_validation.ImageAccess(trace=False)
else:
    sys.exit(0)

for mod in mods:
    success = False
    # FIXME: Optionally spit out a success matrix?
    try:
        success = mod[1].validator(image_handle)
    except Exception as e:
        image_handle.qprint("Exception validating '%s' (%s): %s" % (mod[0],
                                                                   e.__doc__,
                                                                   e))
    if not success:
        image_handle.vprint('Failed to validate: %s' % mod[0])
        ret_code = 1

# Necessary to prevent stale/disconnected FUSE mount.
# See documentation for ImageAccess.__del__().
image_handle.__del__()

sys.exit(ret_code)
