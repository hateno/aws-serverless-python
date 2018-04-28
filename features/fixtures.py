import logging

import sam.app

from click.testing import CliRunner
from behave import fixture

@fixture
def scaffold(context):
    stack_exists = context.runner.invoke(sam.app.exists, obj=context.obj)
    if not stack_exists:
        runner.invoke(sam.app.scaffold, obj=context.obj)

@fixture
def app(context):
    obj = {}
    obj['debug'] = True
    obj['app'] = sam.app.App()

    context.obj = obj
    context.runner = CliRunner()

@fixture
def setlog(context):
    context.log = logging.getLogger()
    context.log.setLevel(logging.INFO)
