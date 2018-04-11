import click
import datetime
import os
import sys
import pytest

import sam.app
from sam.app import App

from click.testing import CliRunner
from dateutil.tz import tzutc

APP_NAME = 'UnitTestAppName'

@pytest.fixture
def runner():
    runner = CliRunner()
    return runner

@pytest.fixture
def obj(pill):
    o = {}
    o['debug'] = True
    o['app'] = sam.app.App(name=APP_NAME, session=pill.session)
    return o

def test_settings_initialized(tmpdir):
    app = App(debug=True, cwd=tmpdir)
    assert(type(app.settings) == dict)

def test_settings_save(tmpdir):
    assert(not os.path.isfile(str(tmpdir) + '/settings.json'))
    app = App(debug=True, cwd=tmpdir)
    assert(app._save_settings())
    assert(os.path.isfile(str(tmpdir) + '/settings.json'))

def test_scaffold(tmpdir, pill):
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': []}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = { "status_code": 200, "data": { "StackId": "arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz", "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "x-amzn-requestid": "xyz", "content-type": "text/xml", "content-length": "123"}, "RetryAttempts": 0 } } }
    pill.save_response(service='cloudformation', operation='CreateStack', response_data=response, http_response=200)

    lambda_function_name = 'UnitTestFunction'
    apigateway_name = 'UnitTestRestAPIGateway'
    app = App(debug=True, cwd=tmpdir, session=pill.session)
    status = app.scaffold(lambda_function_name, apigateway_name)

    assert(lambda_function_name in app.cloud.template.resources)
    assert(apigateway_name in app.cloud.template.resources)
    assert(status['status_code'] == 200)

def test_check_check(tmpdir, pill):
    stack_name = 'UnitTestStack'
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': stack_name, 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': APP_NAME, 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    app = App(name=APP_NAME, debug=True, cwd=tmpdir, session=pill.session)

    status = app.stack_exists(stack_name)
    assert(status)

    status = app.stack_exists()
    assert(status)

def test_cli(runner):
    result = runner.invoke(sam.app.cli, obj={})
    assert(result.exit_code == 0)

def test_cli_scaffold_dry(runner, obj, pill):
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': []}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    lambda_function_name = 'UnitTestFunction'
    apigateway_name = 'UnitTestRestAPIGateway'
    result = runner.invoke(sam.app.scaffold, [lambda_function_name, apigateway_name, '--dry'], obj=obj)
    assert(result.exit_code == 0)
    assert(result.output == 'scaffolding...\n')

def test_cli_stack_exists(runner, obj, pill):
    stack_name = 'UnitTestStack'
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': stack_name, 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': APP_NAME, 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    result = runner.invoke(sam.app.exists, ['--stack', stack_name], obj=obj)
    assert(result.output == 'stack %s exists\n' % stack_name)

    result = runner.invoke(sam.app.exists, obj=obj)
    assert(result.output == 'stack %s exists\n' % APP_NAME)

def test_app_name_property(tmpdir):
    app_name = 'UnitTestAppName'
    app = App(name=app_name, cwd=tmpdir)
    assert(app.name == app_name)
