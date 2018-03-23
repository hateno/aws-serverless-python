import json
import logging
import os
import shutil
import sys

__version__ = '0.0.1'

class App(object):
    SETTINGS_FILE = 'settings.json'
    LAMBDA_DIR = 'lambda/'
    FORMAT_STRING = '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'

    def __init__(self, app_name, debug=False):
        self._debug = debug
        self.log = logging.getLogger(app_name)

        self._configure_logging()
        self._load_settings()

    def _load_settings(self):
        # validate existence of ./lambda/ directory
        if not os.path.exists('./%s' % self.LAMBDA_DIR):
            self.log.error('Lambda directory does not exist, please create one before proceeding')
            sys.exit()
        self.log.info('Creating lambda.zip') # create lambda.zip
        shutil.make_archive('lambda', 'zip', './%s' % self.LAMBDA_DIR)

        # import or init settings.json
        if not os.path.isfile(self.SETTINGS_FILE):
            self.log.info('%s does not exist, initializing' % self.SETTINGS_FILE)
            with open(self.SETTINGS_FILE, 'w') as f:
                f.write('{}')
        settings_fh = open(self.SETTINGS_FILE, 'r')
        settings_json = settings_fh.read()
        settings_fh.close()

        self.settings = json.loads(settings_json)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._configure_log_level()

    def _configure_log_level(self):
        if self._debug:
            level = logging.DEBUG
        else:
            level = logging.ERROR
        self.log.setLevel(level)

    def _configure_logging(self):
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(self.FORMAT_STRING)
        handler.setFormatter(formatter)
        self.log.propogate = False
        self._configure_log_level()
        self.log.addHandler(handler)
