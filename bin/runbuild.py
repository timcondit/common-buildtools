'''A build runner'''

# TODO
# - *done* [pri2] figure out what's wrong with no_confirm
# - [pri3] only print [config-file], [cmdline] and [default] if VERBOSE or DEBUG=True
# - *done* [pri1] fix the attribute ugliness in BuildProperties
# - *done* [pri0] add pass-thru args back in!!
# - [pri3] replace all instances of RELEASE in the Ant scripts with PATCH
# - *done* [pri1] TypeError when 'bin\runbuild.py' run without any arguments


from optparse import OptionParser, OptionGroup
import br   # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/120686
import ConfigParser
import os.path
import shutil
import subprocess
import sys

os.environ['JAVA_HOME'] = r'C:\Progra~1\Java\jdk1.6.0_14'
os.environ['ANT_HOME'] = r'C:\Progra~1\Ant\apache-ant-1.7.1'
os.environ['ANT_OPTS'] = '-Xmx1024m'

BRANCHES_BASE = r'svn://chinook/eps/branches'
TAGS_BASE = r'svn://chinook/eps/tags'
PROJECTS_BASE = r'\\Bigfoot\Engineering\Projects\build'
PRODUCTS_BASE = r'\\Bigfoot\Engineering\builds'
# should this be ant.home?
ANT = os.path.join(os.environ['ANT_HOME'], 'bin', 'ant.bat')
DEBUG = False


class BuildRunner(object):
    '''DOCSTRING'''
    def __init__(self):
        '''DOCSTRING'''
        self.prog=os.path.basename(__file__)
        self.bp = BuildProperties()
        self.retcode=None   # used in during() and after()

        usage_ = self.usage()
        self.parser=OptionParser(usage=usage_, version="%prog 0.8")
        less_common = OptionGroup(self.parser, 'Less common options')
        convenience_opts = OptionGroup(self.parser, 'Convenience options')

        self.parser.set_defaults(
                no_confirm = False,
                dry_run = False,
                more_help = False,
                )

        # common options
        self.parser.add_option('-c', '--config-file',
                help='full path to the INI config file')

        # less common options
        less_common.add_option('-s', '--source-url',
                help= '''Where's the code?  You can provide the
                full URL starting with svn://, or a short path
                that will be prepended with %s/''' % BRANCHES_BASE)
        less_common.add_option('-n', '--next',
                help='specify the NEXT build number')
        less_common.add_option('-p', '--previous',
                help='specify the PREVIOUS build number')

        # convenience options
        convenience_opts.add_option('-y', '--yes', '--no-confirm', action='store_true',
                dest="no_confirm", help='run the build without confirmation')
        convenience_opts.add_option('-d', '--dry-run', action='store_true',
                help='show what would have been done')
        convenience_opts.add_option('-m', '--more-help', action='store_true',
                help='show detailed help [NB: this may be out of date]')

        self.parser.add_option_group(less_common)
        self.parser.add_option_group(convenience_opts)
        (self.options, self.args) = self.parser.parse_args()

        if self.options.more_help:
            self._more_help()


    def before(self):   # AKA pre_build()
        '''DOCSTRING'''
        # Order of operations for setting build properties
        # (1) get config data if --config-file provided
        # (2) get command-line data
        # (3) set defaults as appropriate
        if self.options.config_file:
            self.bp._props_config_file(self.options.config_file)
        self.bp._props_cmdline(self.options, self.args)
        self.bp._props_defaults()

        # if anything is still missing, exit with an error
        missing = self.bp._check_missing()
        if len(missing) > 0:
            print("properties are missing: %s" % missing)
            print("exiting")
            sys.exit(1)

        if DEBUG:
            print("[DEBUG] self.options.no_confirm: %s" % self.options.no_confirm)
            print("[DEBUG] self.options.dry_run: %s" % self.options.dry_run)

        # pprint is True or False based on the value of dry_run
        self.antcall = self.bp.make_antcall(self.options.dry_run)
        print("\nHere is the Ant command based on provided input:")
        print("'''\n%s\n'''" % self.antcall)

        if self.options.dry_run: # old skool
            sys.exit(0)

        # if not no confirm - awkward ... :)
        if not self.options.no_confirm:
            prompt = 'Run it? [y/n] '
            run_build = None
            while run_build != 'y' and run_build != 'n':
                run_build = raw_input(prompt)
            if run_build != 'y':
                print("exiting")
                sys.exit(0)


    def during(self):   # AKA build()
        '''DOCSTRING'''
        for dir in [self.bp.logs_dir, self.bp.unittests_dir]:
            if not os.path.exists(dir):
                try:
                    print("making new dir %s" % dir)
                    os.makedirs(dir)
                except OSError:
                    # Don't kill the job here, because the compile can still
                    # run without this directory being present.  It just won't
                    # finish the last couple steps.
                    print("error: could not create %s" % self.bp.logs_dir)
        # do this separately in case the logs_dir exists, but the log.xsl does
        # not (it won't happen very often)
        if not os.path.exists(self.bp.log_xsl):
            log_xsl_local = os.path.join('logs', 'log.xsl')
            print("copying %s to %s" % (log_xsl_local, self.bp.logs_dir))
            shutil.copy(log_xsl_local, self.bp.logs_dir)

        try:
            self.retcode = subprocess.check_call(self.antcall)
        # one way to trigger this is by clobbering the process in task manager
        except subprocess.CalledProcessError:
            print("warning: something may be broken in subprocess")
            # prn18193: as a test, don't set the retcode to 1 (failure)
            self.retcode = 0
        print("[INFO] Ant call return status is %s" % self.retcode)


    # TODO this needs a substantial overhaul.  I want to do away with the
    # dependency on the semaphore with is generated by running Ant's end task.
    def after(self):    # AKA post_build()
        '''DOCSTRING'''
        # check for semaphore indicating build success
        # if semaphore present:
        #     note success
        #     append NEXT build number (from the just-completed build) to
        #       lkg.txt
        # else if semaphore not present:
        #     note failure
        # send status mail (success or failure) (maybe use Ant)
        build_success=False
        if self.retcode==0:
            build_success=True
            if not self.options.dry_run:
                # Ant moves the working directory from ...\Initial\base to,
                # say, ...\Initial\base-9.6.0000.6-r4495 as the last step
                # before giving control back to runbuild.  But it does not
                # pass the new name of the build directory back to the OS, so
                # runbuild has no (deterministic) way of finding the semaphore
                # file.  So I added '..' to the sem_file path to look for the
                # file OUTSIDE the working directory, at least temporarily.
                # This is a quick workaround until I come up with a more
                # robust and less ugly fix.  It obviously depends on Ant
                # putting the file in the right place as well.
                #
                # Late note: I want to move the semaphore file to the build
                # dir, or have it include the revision number (e.g. instead of
                # 9.7.0100.0_SUCCESS it would be something like
                # 9.7.0100.0-r6339_SUCCESS).  This would allow me to run
                # multiple builds with the same build number, but different
                # revisions of the product source.  In either case,
                # runbuild.py would need to get the revision number from
                # somewhere. -timc 1/2/2009
                semaphore = self.bp.next + '_SUCCESS'
                sem_file = os.path.join(self.bp.wc_dir, '..', semaphore)

                #
                # CAUTION
                #
                # The semaphore file will not exist unless the 'end' target in
                # build.xml is run.  Pay attention to the subprocess return
                # code!  In the worst case a previous build will be deleted
                # because an old semaphore file is present, but lkg.txt is not
                # updated with the latest build number.  (This would happen
                # because a previous build did call end, but this one did not.
                # It's an ugly hole that needs to be patched ASAP.)
                if os.path.exists(sem_file):
                    print("[INFO] found semaphore %s" % sem_file)
                    f=open(self.bp.lkg_file, 'a')
                    f.write(self.options.next)
                    f.write("\n")
                else: # build SUCCESS, notification FAILURE
                    print("build succeeded but semaphore %s does not exist?" % sem_file)
                    sys.exit(1)
            else: # not an official build
                pass
        else:
            build_success=False
        # send status mail
        print("[INFO] This is where we send status mail: %s %s" %
                (self.options.next, build_success))


    def usage(self):
        '''DOCSTRING'''
        return '''Usage: %s [options] [pass-thru args]\n
%s uses input from command-line options, lkg.txt (last known
good), or a combination of the two.  Use pass-thru args to pass
arguments on to Ant, typically to invoke specific targets.

Try '%s --help' for more details
''' % (self.prog, self.prog, self.prog)


    # TODO rewrite or delete
    def _more_help(self):
        '''DOCSTRING'''
        self.msg=self.usage()
        self.msg=self.msg + '''
lkg.txt: %s

There are no required arguments -- all inputs are optional.  If no
options are provided at the command-line then lkg.txt must exist
and must include at least one properly formatted build number.
This is the previous build number, which is incremented to get the
next.

Either the previous or next build numbers may be passed in as
options.  If previous only is provided, lkg.txt is not read, and
the given number is incremented to determine the next.  This
number is written to lkg.txt if the build succeeds.  If next only
is provided, previous is taken from lkg.txt, and next is written
to lkg.txt if the build succeeds.

The usual case where both next and previous are provided is when a
new release is being generated for the first time -- for example
if the last known good build was 9.4.0000.37, and we need to
generate 9.5.0000.0.  As previously, lkg.txt is not read, but the
next build number is written to it if the build succeeds.

NB: previous is never derived.  It must be provided via
command-line or lkg.txt.

Tip: to see the generated Ant call, use --dry-run.  The usual
caveats apply: if lkg.txt is not available, you will need to
provide previous and next.''' % ('TODO')

        print(self.msg)
        sys.exit(0)


    def test(self):
        '''DOCSTRING'''
        # Note, if none of these options are passed in, we use the default file
        # name (specified somewhere up top), and ask for confirmation to run the
        # generated Ant script.  In other words, it's not appropriate as written
        # to automatically dump the help text if no options are provided.
        if self.options.previous:
            print "[INFO] self.options.previous:", self.options.previous
            print "[INFO] checking if %s is a valid format:" % self.options.previous,
            print self._check_version(self.options.previous)
        if self.options.next:
            print "[INFO] self.options.next:", self.options.next
            print "[INFO] checking if %s is a valid format:" % self.options.next,
            print self._check_version(self.options.next)
        if self.options.dry_run:
            print "[INFO] self.options.dry_run:", self.options.dry_run
        if self.options.no_confirm:
            print "[INFO] self.options.no_confirm:", self.options.no_confirm
        if self.options.more_help:
#            print "[INFO] self.options.more_help:", self.options.more_help
            self._more_help()
        if self.options.source_url:
            print "[INFO] self.options.source_url:", self.options.source_url
        if self.options.wc_dir:
            print "[INFO] self.options.wc_dir:", self.options.wc_dir
        if self.options.logs_dir:
            print "[INFO] self.options.logs_dir:", self.options.logs_dir
        if self.args:
            print "[INFO] args:", self.args


class BuildProperties(object):
    '''DOCSTRING'''
    def __init__(self):
        self.triplet = None
        self.next = None
        self.previous = None
        self.source_url = None
        self.tags_url = None
        self.projects_dir = None
        self.products_dir = None
        # TODO It would be nice to set wc_dir to the full version number (e.g.
        # prefix/9.10.0110.2 instead of prefix/9.10.0110), but that's not
        # practical right now, since it's designed to be set in the config
        # file and not updated.  Something to think about later.
        self.wc_dir = None
        self.logs_dir = None
        self.log_file = None
        self.log_xsl = None # path to log.xsl on the publish share
        self.lkg_file = None
        self.unittests_dir = None
        self.major = self.minor = self.patch = self.bn = None
        self.p_major = self.p_minor = self.p_patch = self.p_bn = None

        # CAREFUL HERE: this is a dynamic dictionary, so it might work well,
        # or it might bring 'da pain.  The idea is to allow the list of
        # properties to grow and shrink dynamically, and account for them when
        # using plist.  It's better than the "solution" it replaces (two sets
        # of attributes ... gross).  But keep an eye on it.
        self.plist = self.__dict__.keys()

        # NB: attributes added after self.plist defined are NOT included in it
        self.pass_thru_args = None


    # consider using the property builtin:
    # http://docs.python.org/library/functions.html
    def prop(self, prop, value=None):
        if not hasattr(self, prop):
            if DEBUG:
                print("warning: property %s not found" % prop)
            return
        elif value:
            setattr(self, prop, value)
        return getattr(self, prop)


    def _props_config_file(self, config_file):
        '''DOCSTRING'''
        config=ConfigParser.SafeConfigParser()
        config.read(config_file)
        for key in self.plist:
            try:
                value = config.get('runtime', key)
                self.prop(key, value)
                print("[config-file] setting %s=%s" % (key, value))
            except ConfigParser.NoOptionError:
                if DEBUG:
                    print("[config-file] property '%s' not found in %s" % (key, config_file))


    def _props_cmdline(self, options, args):
        '''DOCSTRING'''
        if options.source_url:
            self.source_url =  options.source_url
            print("[cmdline] setting %s=%s" % ('source_url', options.source_url))
        if options.next:
            self.next = options.next
            print("[cmdline] setting %s=%s" % ('next', options.next))
        if options.previous:
            self.previous = options.previous
            print("[cmdline] setting %s=%s" % ('previous', options.previous))
        if args:
            print("[cmdline] got pass-thru args: %s" % args)
            self.pass_thru_args = args


    def _props_defaults(self):
        '''DOCSTRING'''
        # Ugly dependency: config file must include triplet (major, minor,
        # patch).  Otherwise, can't get to lkg.txt or anything else in the
        # projects_dir.
        if self.projects_dir is None:
            # projects_dir
            self.projects_dir = os.path.join(PROJECTS_BASE, self.triplet)
            print("[default] setting %s=%s" % ('projects_dir', self.projects_dir))

        if self.products_dir is None:
            # products_dir
            self.products_dir = os.path.join(PRODUCTS_BASE, self.triplet)
            print("[default] setting %s=%s" % ('products_dir', self.products_dir))

        # lkg.txt - the key to the whole flippin' thing
        if self.lkg_file is None:
            self.lkg_file = os.path.join(self.projects_dir, 'lkg.txt')
            # FIXME - lkg.txt is the value of the LAST build, not the next
            # one.
            print("[default] setting %s=%s" % ('lkg_file', self.lkg_file))

        # next!
        if self.lkg_file is not None and self.next is None:
            # FIXME - lkg.txt is the value of the LAST build, not the next
            # one.
            car, cdr = self._parse_buildfile().rsplit('.', 1)
            cdr = int(cdr) + 1
            self.next = car + '.' + str(cdr)
            print("[default] setting %s=%s" % ('next', self.next))

        if self.next:
            a, b, c, d = self.next.split('.')
            if self.major is None:
                self.major = a
            if self.minor is None:
                self.minor = b
            if self.patch is None:
                self.patch = c
            if self.bn is None:
                self.bn = d

        if self.previous:
            e, f, g, h = self.previous.split('.')
            if self.p_major is None:
                self.p_major = e
            if self.p_minor is None:
                self.p_minor = f
            if self.p_patch is None:
                self.p_patch = g
            if self.p_bn is None:
                self.p_bn = h

#        if self.triplet is not None:
#            try:
#                self.major_minor, tmp = self.triplet.rsplit('.', 1)
#                print("[default] setting %s=%s" % ('major_minor', self.major_minor))
#                self.triple_xx = self.triplet[:-2] + "xx"
#                print("[default] setting %s=%s" % ('triple_xx', self.triple_xx))
#            # this can happen when trying to split a PRN branch like PRN22180;
#            # a triplet implies patch branches like 9.10.0102
#            except ValueError:
#                print("Caught a ValueError.  If using a PRN branch, please")
#                print("idenfity 

        if self.logs_dir is None:
            self.logs_dir = os.path.join(self.projects_dir, 'logs')
            print("[default] setting %s=%s" % ('logs_dir', self.logs_dir))
            # log file
        if self.log_file is None:
            self.log_file = os.path.join(self.logs_dir, 'build_%s.xml' % self.next)
            print("[default] setting %s=%s" % ('log_file', self.log_file))
            # log.xsl
            self.log_xsl = os.path.join(self.logs_dir, 'log.xsl')
            print("[default] setting %s=%s" % ('log_xsl', self.log_xsl))
        if self.unittests_dir is None:
            self.unittests_dir = os.path.join(self.projects_dir, 'unittests')
            print("[default] setting %s=%s" % ('unittests_dir', self.unittests_dir))

        # example: svn://chinook/eps/tags/9.10/SP2/base
        # TAGS_BASE = r'svn://chinook/eps/tags'
        #
        # os.path.join() uses backslashes on Windows, but that's wrong here!
        if not self.tags_url:
            tmp = TAGS_BASE + r'/' + self.major + '.' + self.minor + r'/' + triplet
            self.tags_url =  tmp
            print("[default] setting %s=%s" % ('tags_url', self.tags_url))

        # TODO move this to ... _props_cmdline()?
        if not self.source_url.lower().startswith(BRANCHES_BASE):
            # os.path.join() uses backslashes on Windows, but that's wrong here!
            self.source_url = BRANCHES_BASE + r'/%s' % self.source_url


    def _check_missing(self):
        '''DOCSTRING'''
        # these properties must be set to continue
        missing = []
        for p in self.plist:
            try:
                tmp = getattr(self, p)
            except AttributeError:
                print("property not found: %s" % p)
            if tmp is None:
                missing.append(p)
        return missing


    def _parse_buildfile(self):
        '''DOCSTRING'''
        try:
            reader = br.BackwardsReader(self.lkg_file)
        # maybe give user another opportunity to provide the LKG build number?
        except WindowsError:
#            print("%s not found ..." % self.lkg_file)
            print("\nerror: %s not found." % self.lkg_file)
            print("If you include a version number with --next (and call the")
            print("'end' target in Ant), I'll be able to generate the file")
            print("for future use.")

            sys.exit(1)

        line = reader.readline()
        while line:
            if line.strip() == '' or line.lstrip().startswith('#'):
                line=reader.readline()
            else:
                last_line=line.strip()
                break
        try:
            return last_line
        except:
            return None


    def make_antcall(self, pprint=False):
        '''DOCSTRING'''
        p = pprint
        antcall  = self._pprint(ANT, p)
        # TODO only need an extra space if not --dry-run
        antcall += " "
        antcall += self._pprint('-Dversion.product=%s ' % self.next, p)
        antcall += self._pprint('-Dversion.previous=%s ' % self.previous, p)
        # I guess this will stay major.minor.patch for now.
        antcall += self._pprint('-Ddir.build=%s ' % self.wc_dir, p)
        antcall += self._pprint('-DMAJOR=%s ' % self.major, p)
        antcall += self._pprint('-DMINOR=%s ' % self.minor, p)
        antcall += self._pprint('-DRELEASE=%s ' % self.patch, p)
        antcall += self._pprint('-DBUILD=%s ' % self.bn, p)
        antcall += self._pprint('-Dp_MAJOR=%s ' % self.p_major, p)
        antcall += self._pprint('-Dp_MINOR=%s ' % self.p_minor, p)
        antcall += self._pprint('-Dp_RELEASE=%s ' % self.p_patch, p)
        antcall += self._pprint('-Dp_BUILD=%s ' % self.p_bn, p)
        antcall += self._pprint('-Durl.src=%s ' % self.source_url, p)
        antcall += self._pprint('-Durl.tags=%s ' % self.tags_url, p)
        antcall += self._pprint('-Ddir.projects=%s ' % self.projects_dir, p)
        antcall += self._pprint('-Ddir.products=%s ' % self.products_dir, p)
        antcall += self._pprint('-listener=org.apache.tools.ant.XmlLogger ', p)
        antcall += self._pprint('-DXmlLogger.file=%s ' % self.log_file, p)
        antcall += self._pprint('-Dant.XmlLogger.stylesheet.uri=%s ' % self.log_xsl, p)
        # last one is not pretty-printed
        try:
            for arg in self.pass_thru_args:
                antcall += arg + " "
        except TypeError:   # empty list
            pass
        return antcall

    # pretty print
    def _pprint(self, ugly, pretty=False):
        '''DOCSTRING'''
        if pretty:
            return ugly + '\n    '
        else:
            return ugly


if __name__=='__main__':
    runner=BuildRunner()
    if len(sys.argv) == 1:
        print runner.usage()
        sys.exit(1)

#    runner.test()
    runner.before()
    runner.during()
    runner.after()

