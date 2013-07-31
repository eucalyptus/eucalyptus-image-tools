import sys
import getopt
import guestfs
import threading

def _usage():
    print '\nUsage:'
    print '%s [-a image] [--check-dependencies] mountpoint\n' % sys.argv[0]
    sys.exit(0)                         # By spec, exit 0 unless bad validation.
    
def _mount_local_run(guest):
    print "calling guestfs.mount_local_run()"
    guest.mount_local_run()
    print "guestfs.mount_local_run() returned"
    
def _mountFUSE(image, mountpoint, trace=False):
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

    # FIXME: Create this mount point if it doesn't already exist.
    guest.mount_local (mountpoint)

    # FIXME: Add conditional to ensure root is mounted?
    runThread = threading.Thread(target=_mount_local_run, args=(guest,))
    runThread.daemon = True
    runThread.start()

    import epdb ; epdb.set_trace()

    return guest
    
def _mountRaw(image):
    pass

class ImageAccess():
    def __init__(self, trace=False):
        self.image = None
        self._trace = trace
        
        try:
            optlist, arglist = getopt.getopt(sys.argv[1:], 'a:',
                                          ['check-dependencies', 'trace'])
        except getopt.GetoptError as e:
            print '\n%s: %s' % (sys.argv[0], e)
            _usage()

        for o, a in optlist:
            if o == '--check-dependencies':
                self.check_dependencies = True
            elif o == '-a':
                self.image = a
            elif o == '--trace':
                self._trace = True
            else:
                _usage()

        if self.image:
            self.mountpoint = arglist[0]
            import epdb ; epdb.set_trace()
            self.guest = _mountFUSE(self.image, self.mountpoint,
                                    trace=self._trace)
        else:
            print '\n%s: Usage without images not yet supported.\n' % sys.argv[0]
            sys.exit(0)

        import epdb ; epdb.set_trace()
