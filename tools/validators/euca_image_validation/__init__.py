import fnmatch
import os
import sys
import getopt
import time
from multiprocessing import Process


def _usage():
    """Print usage and then exit."""
    print '\nUsage:'
    print '%s [--check-dependencies] [--trace] [-q] [-v] [-d] mountpoint' % sys.argv[0]
    print '%s [--check-dependencies] [--trace] [-q] [-v] [-d] -a image' % sys.argv[0]
    print '%s [--check-dependencies] [--trace] [-q] [-v] [-d] --fuse -a image mountpoint' % sys.argv[0]
    print
    print '(Mounting of images with -a is currently unsupported on non-Linux platforms.)'
    print
    sys.exit(0)                         # By spec, exit 0 unless bad validation.


def _mount_local_run(self):
    """Called in thread to process activity on fuse-mounted filesystem.

    Blocks until filesystem is unmounted.

    """
    # FIXME: move into class?
    self.dprint('calling guestfs.mount_local_run()')
    self.guest.mount_local_run()
    self.dprint('guestfs.mount_local_run() returned')


class ImageAccess():
    """Class for accessing images.

    Can access iamges either directly via FUSE or using a previous (external) mount to the filesystem.

    """

    def qprint(self, msg):
        """Prints to stdout unless -q (quiet mode) specified."""
        if not self._quiet:
            print msg

    def vprint(self, msg):
        """Prints to stdout if -v (verbose mode) specified.

        (Note: --trace or -d implies -v.)

        """
        if self._verbose:
            print msg

    def dprint(self, msg):
        """Prints to stdout if -d (debug mode) specified.

        (Note: --trace implies -d.)

        """
        if self._debug:
            print msg

    def is_mounted(self):
        """Returns True if image mounted by internal mechanism, False if not."""
        return self.mounted

    def get_mountpoint(self):
        """Returns the internal mountpoint of an image (or None if unmounted)."""
        return self.mountpoint

    def _light_off(self):
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
            self.dprint('Root device: %s' % root)
            mps = guest.inspect_get_mountpoints (root)

            def _compare (a, b): return len(a) - len(b)
    
            for devtup in sorted(mps, _compare):
                try:
                    guest.mount_ro(devtup[1], devtup[0])
                except RuntimeError as msg:
                    self.dprint('%s (ignored)' % msg)
    
        return guest

    def _mount_fuse(self):
        """Mounts FUSE filesystem at specified mountpoint.
    
        GuestFS must already have been initialized.

        """
        # FIXME: Create this mount point if it doesn't already exist.
        self.guest.mount_local(self.mountpoint)
        # FIXME: Add conditional to ensure root is mounted?
        run_process = Process(target=_mount_local_run, args=(self,))
        run_process.daemon = True
        run_process.start()

    # Perhaps change default value of omit_mountpoint to False?
    def find_files(self, pathname, filename, glob=False, omit_mountpoint=True):
        """Finds file 'filename' under path 'pathname'.

        Returns a list of matching paths, optionally globbing the filename
        and omitting (trimming away) the any leading mount-point path
        ('omit_mountpoint'). Note that 'omit_mountpoint' has no effect when
        using unmounted images through the libguestfs API.

        If 'filename' is None, all filenames are returned.

        This provides an abstraction layer so that validators do not need to
        worry about whether an image is mounted or is being accessed via the
        libguestfs API.

        """

        # FIXME: Need to make note about "'filename' is None" above true!
        
        found = []

        if filename is None and glob is True:
            # Doesn't make sense--raise exception?
            return []

        if self.mounted:
            # Using filesystem.
            for root, dirs, files in os.walk('%s%s' % (self.mountpoint,
                                                       pathname)):
                if len(files):
                    if glob:
                        match_files = [x for x in files if fnmatch.fnmatch(x, filename)]
                    else:
                        match_files = [x for x in files if filename == x]

                    if len(match_files):
                        for x in match_files:
                            if omit_mountpoint and root.startswith(self.mountpoint):
                                found.append('%s/%s' % (root[len(self.mountpoint):], x))
                            else:
                                found.append('%s/%s' % (root, x))
        else:
            # Using libguestfs API.
            try:
                files = self.guest.find(pathname)
            except RuntimeError as e:
                # In all likelihood, this directory doesn't exist.
                self.dprint("Ignoring RuntimeError inspecting '%s' (%s), returning empty list." % (pathname, e))
                return []

            if glob:
                found = ['%s%s' % (pathname, x) for x in files if fnmatch.fnmatch(os.path.basename(x), filename) and self.guest.is_file('%s%s' % (pathname, x))]
            else:
                found = ['%s%s' % (pathname, x) for x in files if filename == os.path.basename(x) and self.guest.is_file('%s%s' % (pathname, x))]

        return found

    def read_file(self, filename):
        """Returns the contents of file 'filename'.

        This provides an abstraction layer so that validators do not need to
        worry about whether an image is mounted or is being accessed via the
        libguestfs API.

        """
        if self.mounted:
            # Using filesystem.
            try:
                f = open(filename, 'r')
                contents = f.readlines()
                f.close()
                return contents
            except Exception as e:
                self.dprint("Cannot open/read file '%s': %s" % (filename, e))
                return []
        else:
            try:
                contents = self.guest.read_lines(filename)
                return contents
            except Exception as e:
                self.dprint("Cannot read file '%s': %s" % (filename, e))
                return []
        
    def __init__(self, trace=False):
        """Handles command-line aruguments and sets up image access."""
        self.fuse = False
        self._fuse_mounted = False
        self.image = None
        self.check_dependencies = False
        self.mounted = False
        self._quiet = False
        self._verbose = False
        self._debug = False
        self._trace = trace
        self.mountpoint = None
        
        try:
            optlist, arglist = getopt.getopt(sys.argv[1:], 'a:qvd',
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
                self._debug = True
                self._quiet = False
            elif o == '-q':
                # This check should be moved into the qprint function;
                # otherwise, it's dependent upon the order of the arguments.
                if not self._trace and not self._verbose and not self._debug:
                    self._quiet = True
            elif o == '-v':
                self._verbose = True
                self._quiet = False
            elif o == '-d':
                self._debug = True
                self._verbose = True
                self._quiet = False
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
            self.guest = self._light_off()
            if self.fuse:
                if len(arglist):
                    self.mountpoint = arglist[0]
                    self._mount_fuse()
                    self._fuse_mounted = True
                    self.mounted = True
                else:
                    _usage()
            else:
                # FIXME: Need to short-circuit this test; takes too long to
                # exit when this condition is met. Should be instant.
                self.dprint('\nNote: %s: Using an image without FUSE.\n' % sys.argv[0])
        else:
            if len(arglist):
                self.mountpoint = arglist[0]
                self.dprint('\nNote: %s: Using direct filesystem access, without an image.\n' % sys.argv[0])
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
        if self._fuse_mounted:
            self.dprint('calling guestfs.umount_local()')

            for i in range(0, 10):
                try:
                    self.guest.umount_local()
                except RuntimeError as e:
                    print 'guestfs.umount_local(%d): %s' % (i, e)
                    time.sleep(1)
                else:
                    self._fuse_mounted = False
                    break
                finally:
                    if i == 9:
                        print 'guestfs.umount_local: giving up...'
        elif self.fuse:
            self.dprint('skipping guestfs.umount_local() call -- nothing mounted')
