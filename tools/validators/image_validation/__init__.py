import atexit
import sys
import getopt
import guestfs
import time
from multiprocessing import Process

def _usage():
    """Print validator usage and then exit."""
    print '\nUsage:'
    print '%s [-a image] [--check-dependencies] mountpoint\n' % sys.argv[0]
    sys.exit(0)                         # By spec, exit 0 unless bad validation.

def _mount_local_run(guest):
    """Called in thread to process activity on fuse-mounted filesystem.
    Blocks until filesystem is unmounted.
    """
    print "calling guestfs.mount_local_run()"
    guest.mount_local_run()
    print "guestfs.mount_local_run() returned"

def _lightFUSE(image, trace=False):
    """Initiaizes guestfs for an image."""
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

    return guest

def _mountFUSE(guest, mountpoint):
    """Mounts FUSE filesystem at specified mountpoint.

    GuestFS must already have been initialized.
    """
    # FIXME: Create this mount point if it doesn't already exist.
    guest.mount_local (mountpoint)

    # FIXME: Add conditional to ensure root is mounted?
    runThread = Process(target=_mount_local_run, args=(guest,))
    runThread.daemon = True
    runThread.start()

class ImageAccess():

    """Class for accessing images, either directly via FUSE or using a previous (external) mount to the filesystem."""

    def __init__(self, trace=False):
        """Handles command-line aruguments and sets up image access.>"""
        self.image = None
        self._trace = trace
        
        try:
            optlist, arglist = getopt.getopt(sys.argv[1:], 'a:qv',
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
            elif o == '-q':
                self._quiet = True
            elif o == '-v':
                self._verbose = True
            else:
                _usage()

        self.mountpoint = arglist[0]

        if self.image:
            self.guest = _lightFUSE(self.image, trace=self._trace)
            _mountFUSE(self.guest, self.mountpoint)
            # FIXME: There's a race here with guestfs.mount_local_run().
            #time.sleep(2)
        else:
            print '\n%s: Usage without images not yet supported.\n' % sys.argv[0]
            sys.exit(0)

    def __del__(self):
        """Ensures FUSE filesystem is unmounted before exiting.

        (This prevents 'Transport endpoint is not connected' errors.)
        """
        if self.image:
            print "calling guestfs.umount_local()"
            self.guest.umount_local()
