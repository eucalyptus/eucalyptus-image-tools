import sys
import getopt
import guestfs
import threading

def _mountFUSE(image, trace=False):
    guest = guestfs.GuestFS()

    if trace:
        guest.set_trace(1)

    guest.add_drive_opts(image, readonly=1)
    guest.launch()
    roots = guest.inspect_os()
    if len(roots) == 0:
        raise (Error ('inspect_os: no operating systems found'))
    for root in roots:
        print 'Root device: %s' % root
        
        mps = guest.inspect_get_mountpoints (root)
        def compare (a, b): return len(a) - len(b)
        for devtup in sorted (mps, compare):
            try:
                guest.mount_ro (devtup[1], devtup[0])
            except RuntimeError as msg:
                print "%s (ignored)" % msg

    guest.mount_local ('mnt')
    # FIXME: Add conditional to ensure root is mounted.
    runThread = threading.Thread(target=guest.mount_local_run)
    runThread.daemon = False
    runThread.start()
    
    import epdb ; epdb.set_trace()

    return guest
    
def _mountRaw(image):
    pass

class ImageAccess():
    def __init__(self, image=None, libguestfs=False, fuse=False, trace=False):
        try:
            optlist, args = getopt.getopt(sys.argv[1:], None,
                                          ['check-dependencies'])
        except getopt.GetoptError as e:
            print '\n%s: %s\n' % (sys.argv[0], e)
            exit                        # By spec, exit 0 unless bad validation.

        #print 'optlist: ', optlist
        #print 'args: ', args

        for o, a in optlist:
            if o == '--check-dependencies':
                self.check_dependencies = True

        if not image:
            self.image = args[0]
        else:
            self.image = image

        if fuse:
            libguestfs = True
            self.guest = _mountFUSE(self.image, trace=trace)

        import epdb ; epdb.set_trace()
