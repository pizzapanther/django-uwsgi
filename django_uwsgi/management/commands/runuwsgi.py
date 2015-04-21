import django
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys
import multiprocessing

root = os.getcwd()
django_project = os.path.basename(root)


class Command(BaseCommand):
    help = "Runs this project as a uWSGI application. Requires the uwsgi binary in system path."

    http_port = '8000'
    socket_addr = None


    def handle(self, *args, **options):
        for arg in args:
            k, v = arg.split('=')
            if k == 'http':
                if self.http_port:
                    self.http_port = v
            elif k == 'socket':
                self.http_port = None
                self.socket_addr = v

        # load http and python plugin: first the specific version, otherwise try with the generic one
        if self.http_port:
            os.environ['UWSGI_PLUGINS'] = 'http,python%d%d:python' % (sys.version_info[0], sys.version_info[1])
        else:
            os.environ['UWSGI_PLUGINS'] = 'python%d%d:python' % (sys.version_info[0], sys.version_info[1])

        # load the Django WSGI handler
        os.environ['UWSGI_MODULE'] = '%s.wsgi' % django_project
        # DJANGO settings
        if options['settings']:
            os.environ['DJANGO_SETTINGS_MODULE'] = options['settings']
        else:
            os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings' % django_project

        # bind the http server to the default port
        if self.http_port:
            os.environ['UWSGI_HTTP'] = ':%s' % self.http_port
        elif self.socket_addr:
            os.environ['UWSGI_SOCKET'] = self.socket_addr
        # set process names
        os.environ['UWSGI_AUTO_PROCNAME'] = '1'
        os.environ['UWSGI_PROCNAME_PREFIX_SPACED'] = '[uWSGI %s]' % django_project
        # remove sockets/pidfile at exit
        os.environ['UWSGI_VACUUM'] = '1'
        # retrieve/set the PythonHome
        os.environ['UWSGI_PYHOME'] = sys.prefix
        # increase buffer size a bit
        os.environ['UWSGI_BUFFER_SIZE'] = '8192'
        # add threads for concurrency
        os.environ['UWSGI_ENABLE_THREADS'] = '1'
        os.environ['UWSGI_LAZY_APPS'] = '1'
        os.environ['UWSGI_SINGLE_INTERPRETER'] = '1'
        # set 10 workers and cheaper to number of cpus
        os.environ['UWSGI_WORKERS'] = '10'
        os.environ['UWSGI_CHEAPER'] = str(multiprocessing.cpu_count())
        # enable the master process
        os.environ['UWSGI_MASTER'] = '1'
        # set uid and gid
        os.environ['UWSGI_UID'] = str(os.getuid())
        os.environ['UWSGI_GID'] = str(os.getgid())
        # run spooler for mail task
        os.environ['UWSGI_SPOOLER'] = '/tmp'
        os.environ['UWSGI_SPOOLER_IMPORT'] = 'django_uwsgi.task'
        if settings.DEBUG:
            # map static files
            os.environ['UWSGI_STATIC_MAP'] = '%s=%s' % (settings.STATIC_URL, settings.STATIC_ROOT)
            os.environ['UWSGI_PY_AUTORELOAD'] = '2'
        # exec the uwsgi binary
        os.execvp('uwsgi', ('uwsgi',))


    def usage(self, subcomand):
        return r"""
run this project on the uWSGI server
  http=PORT		run the embedded http server on port PORT
  socket=ADDR		bind the uwsgi server on address ADDR (this will disable the http server)
        """
