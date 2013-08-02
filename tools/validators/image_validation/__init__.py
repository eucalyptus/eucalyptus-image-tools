import atexit
import sys
import getopt
import guestfs
import time
from multiprocessing import Process

def _usage():
    """Print validator usage and then exit."""
    print '\nUsage:'
    print '%s [--check-dependencies] [--trace] [--fuse] [-q] [-v] [-a image] mountpoint\n' % sys.argv[0]
    sys.exit(0)                         # By spec, exit 0 unless bad validation.

def _mount_local_run(self):
    """Called in thread to process activity on fuse-mounted filesystem.
    Blocks until filesystem is unmounted.
    """
    self.vprint('calling guestfs.mount_local_run()')
    self.guest.mount_local_run()
    self.vprint('guestfs.mount_local_run() returned')

def _lightOff(self, trace=False):
    """Initiaizes guestfs for an image."""
    guest = guestfs.GuestFS()

    if trace:
        guest.set_trace(1)

    guest.add_drive_opts(self.image, readonly=1)
    guest.launch()
    roots = guest.inspect_os()
    if len(roots) == 0:
        raise (Error ('inspect_os: no operating systems found'))
    for root in roots:
        self.vprint('Root device: %s' % root)
        
        mps = guest.inspect_get_mountpoints (root)
        def compare (a, b): return len(a) - len(b)
        for devtup in sorted (mps, compare):
            try:
                guest.mount_ro (devtup[1], devtup[0])
            except RuntimeError as msg:
                self.vprint('%s (ignored)' % msg)

    return guest

def _mountFUSE(self, mountpoint):
    """Mounts FUSE filesystem at specified mountpoint.

    GuestFS must already have been initialized.
    """
    # FIXME: Create this mount point if it doesn't already exist.
    self.guest.mount_local (mountpoint)

    # FIXME: Add conditional to ensure root is mounted?
    runThread = Process(target=_mount_local_run, args=(self,))
    runThread.daemon = True
    runThread.start()

class ImageAccess():

    """Class for accessing images, either directly via FUSE or using a previous (external) mount to the filesystem."""

    def qprint(self, msg):
        if not self._quiet:
            print msg

    def vprint(self, msg):
        if self._verbose:
            print msg

    def __init__(self, trace=False):
        """Handles command-line aruguments and sets up image access."""
        self.fuse = False
        self.fuse_mounted = False
        self.image = None
        self.check_dependencies = False
        self.mounted = False
        self._quiet = False
        self._verbose = False
        self._trace = trace
        
        try:
            optlist, arglist = getopt.getopt(sys.argv[1:], 'a:qv',
                                          ['check-dependencies', 'trace',
                                           'fuse'])
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
                self._verbose = True
            elif o == '-q':
                if not self._trace and not self._verbose:
                    self._quiet = True
            elif o == '-v':
                self._verbose = True
            elif o == '--fuse':
                self.fuse = True
            else:
                _usage()

        # Doesn't necessarily imply FUSE.

        if self.image:
            self.guest = _lightOff(self, trace=self._trace)
            if self.fuse:
                self.mountpoint = arglist[0]
                _mountFUSE(self, self.mountpoint)
                self.fuse_mounted = True
                self.mounted = True
            else:
                # FIXME: Need to short-circuit this test; takes too long to
                # exit when this condition is met. Should be instant.
                print '\n%s: Using an image without FUSE.\n' % sys.argv[0]
                #sys.exit(0)
        else:
            self.mountpoint = arglist[0]
            self.vprint('\n%s: Using direct filesystem access, without an image.\n' % sys.argv[0])
            self.mounted = True         # Leap of faith.
            #sys.exit(0)

    def __del__(self):
        """Ensures FUSE filesystem is unmounted before exiting.

        (This prevents 'Transport endpoint is not connected' errors.)
        """
        if self.fuse_mounted:
            self.vprint('calling guestfs.umount_local()')
            self.guest.umount_local()
        elif self.fuse:
            self.vprint('skipping guestfs.umount_local() call -- nothing mounted')
            
