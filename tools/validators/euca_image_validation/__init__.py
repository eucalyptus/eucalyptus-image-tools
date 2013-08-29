import os
import sys
import getopt
import time
from multiprocessing import Process

def _usage():
    """Print usage and then exit."""
    print '\nUsage:'
    print '%s [--check-dependencies] [--trace] [-q] [-v] mountpoint' % sys.argv[0]
    print '%s [--check-dependencies] [--trace] [-q] [-v] -a image' % sys.argv[0]
    print '%s [--check-dependencies] [--trace] [-q] [-v] --fuse -a image mountpoint' % sys.argv[0]
    print
    print '(Mounting of images with -a is currently unsupported on non-Linux platforms.)'
    print
    sys.exit(0)                         # By spec, exit 0 unless bad validation.

# FIXME: move into class?
def _mount_local_run(self):
    """Called in thread to process activity on fuse-mounted filesystem.
    Blocks until filesystem is unmounted.
    """
    self.vprint('calling guestfs.mount_local_run()')
    self.guest.mount_local_run()
    self.vprint('guestfs.mount_local_run() returned')

class ImageAccess():

    """Class for accessing images, either directly via FUSE or using a previous (external) mount to the filesystem."""

    def qprint(self, msg):
        """Prints to stdout unless -q (quiet mode) specified."""
        if not self._quiet:
            print msg

    def vprint(self, msg):
        """Prints to stdout if -v (verbose mode) specified.
        (Note: --trace implies -v.)"""
        if self._verbose:
            print msg

    def is_mounted(self):
        """Returns True if image mounted by internal mechanism, False if not."""
        return self.mounted

    def get_mountpoint(self):
        """Returns the internal mountpoint of an image (or None if unmounted)."""
        return self.mountpoint

    def _lightOff(self):
        """Initiaizes guestfs for an image."""
        guest = self.guestfs.GuestFS()
    
        if self._trace:
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

    def _mountFUSE(self):
        """Mounts FUSE filesystem at specified mountpoint.
    
        GuestFS must already have been initialized.
        """
        # FIXME: Create this mount point if it doesn't already exist.
        self.guest.mount_local(self.mountpoint)
    
        # FIXME: Add conditional to ensure root is mounted?
        runThread = Process(target=_mount_local_run, args=(self,))
        runThread.daemon = True
        runThread.start()

    def find_files(self, pathName, fileName, glob=False, omitMountpoint=True):
        """Finds filename 'file' under path 'path'.

        Returns a list of matching paths, optionally globbing the filename
        and omitting (trimming away) the any leading mount-point path.

        If 'file' is None, all filenames are returned.

        This provides an abstraction layer so that validators do not need to
        worry about whether an image is mounted or is being accessed via the
        libguestfs API."""
        
        found = []

        if fileName == None and glob == True:
            # FIXME: Doesn't make sense--raise exception?
            return found

        if self.mounted:
            # Using filesystem.
            fileList = os.walk('%s%s' % (self.mountpoint, pathName))
            foundList = [x for x in fileList if fileName in x[2]]

            for x in foundList:
                for y in x[2]:
                    fullPath = '%s/%s' % (x[0], y)

                    if omitMountpoint and fullPath.startswith(self.mountpoint):
                        found.append(fullPath[len(self.mountpoint):])
                    else:
                        found.append(fullPath)
        else:
            # Using libguestfs API.
            fileList = self.guest.find(pathName)
            found = ['%s%s' % (pathName, x) for x in fileList if fileName in x]

        return found

    ### FIXME: Need a method to consolidate walking/looking for files
    ### in a directory hierarchy and returning them. This will eliminate
    ### the need for validation scripts to worry about whether filesystem
    ### is mounted.

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
        self.mountpoint = None
        
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
                self.vprint('--check-dependencies not yet implemented.')
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

        try:
            import guestfs
            self.guestfs = guestfs
        except Exception as e:
            if self.image:
                print
                print 'No libguestfs functionality available: %s' % e
                _usage()

        if self.fuse and not self.image:
            # Must specify an image with -a for --fuse.
            _usage()

        # Doesn't necessarily imply FUSE.
        if self.image:
            self.guest = self._lightOff()
            if self.fuse:
                if len(arglist):
                    self.mountpoint = arglist[0]
                    self._mountFUSE()
                    self.fuse_mounted = True
                    self.mounted = True
                else:
                    _usage()
            else:
                # FIXME: Need to short-circuit this test; takes too long to
                # exit when this condition is met. Should be instant.
                self.vprint('\nNote: %s: Using an image without FUSE.\n' % sys.argv[0])
        else:
            if len(arglist):
                self.mountpoint = arglist[0]
                self.vprint('\nNote: %s: Using direct filesystem access, without an image.\n' % sys.argv[0])
                self.mounted = True         # Leap of faith.
            else:
                _usage()

    def __del__(self):
        """Ensures FUSE filesystem is unmounted before exiting.

        (This prevents 'Transport endpoint is not connected' errors.)

        Note that this is called explicitly in euca_image_validate.py.
        If it's not called explicitly and instead is called implicitly
        during program exit, the unmount will likely block/fail and leave
        the mount stale/disconnected.
        """
        if self.fuse_mounted:
            self.vprint('calling guestfs.umount_local()')

            for i in range(0, 10):
                try:
                    self.guest.umount_local()
                except RuntimeError as e:
                    print 'guestfs.umount_local(%d): %s' % (i, e)
                    time.sleep(1)
                else:
                    self.fuse_mounted = False
                    break
                finally:
                    if i == 9:
                        print 'guestfs.umount_local: giving up...'
        elif self.fuse:
            self.vprint('skipping guestfs.umount_local() call -- nothing mounted')
