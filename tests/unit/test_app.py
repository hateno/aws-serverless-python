import click
import os
import sys
import pytest

import sam.app
from sam.app import App

from click.testing import CliRunner

@pytest.fixture
def runner():
    runner = CliRunner()
    return runner

@pytest.fixture
def obj():
    obj.debug = True
    obj.app = sam.app.App('UnitTestAppName')

def test_settings_initialized():
    app = App('foo', debug=True)
    assert(type(app.settings) == dict)

def test_cli(runner):
    result = runner.invoke(sam.app.cli, obj={})
    assert(result.exit_code == 0)

def test_scaffold(runner, obj):
    result = runner.invoke(sam.app.scaffold, ['--dry'], obj=obj)
    assert(result.exit_code == 0)
    assert(result.output == 'scaffolding...\n')
