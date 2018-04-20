import click
import json
import logging
import os
import shutil
import sys
import uuid

import sam.cloud
import sam.awslambda

__version__ = '0.0.1'

class App(object):
    """
    Main class that handles CLI and interacts with sub-modules
    """
    SETTINGS_FILE = 'settings.json'
    LAMBDA_DIR = 'lambda/'
    FORMAT_STRING = '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'

    def __init__(self, name=None, debug=False, cwd=None, session=None):
        """Constructor for the App class

        Args:
            name (str): if name does not exist in settings.json, then will use this name instead of auto-generating one
                else this parameter will be ignored
            debug (bool): sets the DEBUG level for logging
            cwd (str): changes the current working directory, important for settings.json and for testing purposes
            session (boto3.session.Session): specifies the boto session, only important for testing purposes
        """
        self.log = logging.getLogger(name)
        self.session = session
        self._debug = debug
        self._configure_logging()

        if cwd is not None:
            os.chdir(cwd)
        self.log.info('Current working directory is %s' % os.getcwd())

        self._load_settings()
        self._preload_settings(name)

        self.cloud = sam.cloud.Cloud(self.settings, session=self.session)

    @property
    def name(self):
        return self._settings('name')

    @property
    def function_name(self):
        return self._settings('function_name')

    @property
    def rest_name(self):
        return self._settings('rest_name')

    def _settings(self, key):
        return None if self.settings is None else self.settings[key]

    def _preload_settings(self, name):
        if 'name' not in self.settings:
            if name is None:
                self.settings['name'] = 'MyWebApplication' + str(uuid.uuid4()).split('-')[-1]
            else:
                self.settings['name'] = name
        else:
            self.log.warn('Using name %s from settings.json' % self.settings['name'])

        if 'function_name' not in self.settings:
            self.settings['function_name'] = '%sFunction' % self.name

        if 'rest_name' not in self.settings:
            self.settings['rest_name'] = '%sAPIGateway' % self.name

    def _lambda_dir_exists(self):
        return os.path.exists('./%s' % self.LAMBDA_DIR)

    def _package_lambda(self):
        self.log.info('Creating lambda.zip') # create lambda.zip
        shutil.make_archive('lambda', 'zip', './%s' % self.LAMBDA_DIR)

    def _load_settings(self):
        # validate existence of ./lambda/ directory
        if not self._lambda_dir_exists():
            self.log.info('Lambda directory does not exist, creating one...')
            os.mkdir('./%s' % self.LAMBDA_DIR)
        self._package_lambda()

        # import or init settings.json
        if not os.path.isfile(self.SETTINGS_FILE):
            self.log.info('%s does not exist, initializing' % self.SETTINGS_FILE)
            with open(self.SETTINGS_FILE, 'w') as f:
                f.write('{}')
        settings_fh = open(self.SETTINGS_FILE, 'r')
        settings_json = settings_fh.read()
        settings_fh.close()

        self.settings = json.loads(settings_json)

    def _save_settings(self):
        with open('settings.json', 'w') as f:
            if self.settings is None:
                self.settings = {}
            json.dump(self.settings, f)
        return os.path.isfile('settings.json')

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

    def scaffold(self, dry=False):
        self.log.info('Creating scaffold in AWS cloud...')
        self.cloud.add_lambda(self.function_name)
        self.cloud.add_api_gateway(self.rest_name)
        status = self.cloud.deploy(dry=dry)
        return status

    def stack_exists(self, stack_name=None):
        if stack_name is None:
            stack_name = self.name
        status = self.cloud.stack_exists(stack_name)
        return status

    def upload_lambda_code(self):
        '''
        Packages the lambda/ directory and upload it to AWS Lambda
        '''
        function_name = self.cloud.function_name
        if function_name is None:
            self.log.error('AWS Lambda Function not deployed to cloud, please deploy first')
            return None
        if not self._lambda_dir_exists():
            self.log.error('Lambda directory not found')
            return None
        if self.settings['function_name'] is None:
            self.log.error('Scaffold does not exist, please scaffold first')
            return None
        self._package_lambda()
        # retrieve function_name from cloudformation stack
        awslambda = sam.awslambda.Lambda(self.settings, session=self.session)
        status = awslambda.update(code='lambda.zip')
        return status

##
# CLI
##

@click.group()
@click.version_option(version=__version__, message='%(prog)s %(version)s')
@click.option('--debug/--no-debug', default=False, help='Print debug logs to stderr.')
@click.pass_context
def cli(ctx, debug=False):
    ctx.obj['debug'] = debug
    ctx.obj['app'] = App(debug=debug)

@cli.command()
@click.option('--dry/--no-dry', default=False, help='No changes are committed locally or to AWS')
@click.pass_context
def scaffold(ctx, dry=False):
    app = ctx.obj['app']
    click.echo('scaffolding...')
    status = app.scaffold(dry=dry)

@cli.command()
@click.option('--stack', type=str, default=None, nargs=1)
@click.pass_context
def exists(ctx, stack):
    app = ctx.obj['app']
    if stack is None:
        stack = app.name
    result = app.stack_exists(stack)
    status = 'exists'
    if not result:
        status = 'does not exist'

    click.echo('stack %s %s' % (stack, status))

@cli.command()
@click.pass_context
def update(ctx):
    app = ctx.obj['app']
    result = app.upload_lambda_code()
    status = 'lambda function %s' % app.function_name
    if not result:
        status += ' not'
    status += ' updated'

    click.echo(status)

def main():
    try:
        return cli(obj={})
    except Exception as e:
        import traceback
        click.echo(traceback.format_exc(), err=True)
        return 2
