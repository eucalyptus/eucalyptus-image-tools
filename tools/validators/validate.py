#!/usr/bin/python

import sys
import os
import imp

#sys.path.insert(0, 'validators.d')

toCheck = []

for root, dirs, files in os.walk('validation_modules'):
    toCheck += ['%s/%s' % (root, x) for x in files]

toSource = [os.path.splitext(x)[0] for x in toCheck if x.endswith('.py')]

#import epdb ; epdb.st()

mods = []
for mod in toSource:
    (f, fn, d) = imp.find_module(mod)
    mods.append(imp.load_module(mod, f, fn, d))

for mod in mods:
    mod.validator()
    
#(f, fn, d) = imp.find_module('eth_device')

#mod = imp.load_module('eth_device', f, fn, d)

import epdb ; epdb.st()
