import glob
import os
import sys

redhat_dirname = '/etc/sysconfig/network-scripts'
redhat_file_prefix = 'ifcfg-eth'

ubuntu_dirname = '/etc/network'
ubuntu_filename = 'interfaces'

def _check_redhat(val):
    retval = False
    files_contents = {}

    if_files = val.find_files(redhat_dirname, '%s*' % redhat_file_prefix, glob=True)

    for if_file in if_files:
        try:
            file_contents = val.read_file(if_file)
            if not len(file_contents):
                continue
            files_contents[if_file] = {}

            for line in file_contents:
                line_tup = tuple(line.strip().split('='))
                files_contents[if_file][line_tup[0]] = line_tup[1]

            # FIXME: handle pathological case of interface file with no DEVICE
            # and/or ONBOOT line(s).
            val.vprint('Checking interface: %s' % files_contents[if_file]['DEVICE'])
            if files_contents[if_file]['ONBOOT'].count('yes') or files_contents[if_file]['ONBOOT'].count('on'):
                val.qprint('Found active interface: %s' % files_contents[if_file]['DEVICE'])
                retval = True
        except Exception as e:
            val.qprint("Cannot analyze file '%s': %s" % (if_file, e))

    return retval

def _check_ubuntu(val):
    path_list = val.find_files(ubuntu_dirname, ubuntu_filename)

    if len(path_list):
        full_path = path_list[0]
    else:
        return False

    try:
        file_contents = val.read_file(full_path)
    except Exception as e:
        val.qprint("Cannot analyze file '%s': %s" % (full_path, e))
        return False

    interfaces = [x.strip() for x in file_contents if x.strip().startswith('auto eth')]

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
