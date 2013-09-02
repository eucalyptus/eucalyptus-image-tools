module_name = 'acpiphp.ko'
module_base = '/lib/modules'

def validator(val):
    found_files = val.find_files(module_base, module_name, omit_mountpoint=True)

    if len(found_files):
        for found_file in found_files:
            val.qprint('Found module: %s' % found_file)
        return True
    else:
        val.qprint('Did not find module: %s' % module_name)

    return False
