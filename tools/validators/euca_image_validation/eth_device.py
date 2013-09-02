import glob
import os
import sys

# FIXME: clean this up.
redhatDirName = '/etc/sysconfig/network-scripts'
redhatFileStub = 'ifcfg-eth'
redhatFilePrefix = '%s/%s' % (redhatDirName, redhatFileStub)

ubuntuFileName = 'interfaces'
ubuntuDirName = '/etc/network'

def _check_redhat(val):
    retVal = False
    filesContents = {}
    ifFiles = val.find_files(redhatDirName, '%s*' % redhatFileStub, glob=True, omit_mountpoint=False)

    for ifFile in ifFiles:
        try:
            fileContents = val.read_file(ifFile)
            if not len(fileContents):
                continue
            filesContents[ifFile] = {}

            for line in fileContents:
                lineTup = tuple(line.strip().split('='))
                filesContents[ifFile][lineTup[0]] = lineTup[1]

            val.vprint('Checking interface: %s' % filesContents[ifFile]['DEVICE'])
            if filesContents[ifFile]['ONBOOT'].count('yes') or filesContents[ifFile]['ONBOOT'].count('on'):
                val.qprint('Found interface: %s' % filesContents[ifFile]['DEVICE'])
                retVal = True
        except Exception as e:
            val.qprint("Cannot analyze file '%s': %s" % (ifFile, e))

    return retVal

def _check_ubuntu(val):
    pathList = val.find_files(ubuntuDirName, ubuntuFileName, omit_mountpoint=False)
    if len(pathList):
        fullPath = pathList[0]
    else:
        return False

    try:
        fileContents = val.read_file(fullPath)
    except Exception as e:
        val.qprint("Cannot analyze file '%s': %s" % (fullPath, e))
        return False

    interfaces = [x.strip() for x in fileContents if x.strip().startswith('auto eth')]

    for interface in interfaces:
        val.qprint('Found interface: %s' % interface)

    if len(interfaces):
        return True
    else:
        val.qprint('Did not find any automatically enabled Ethernet interfaces.')
        return False

def validator(val):
    if _check_redhat(val):
        return True
    elif _check_ubuntu(val):
        return True
    else:
        return False
