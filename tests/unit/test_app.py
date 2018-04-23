import click
import datetime
import json
import os
import pytest
import shutil
import sys

import troposphere.awslambda

import sam.app
from sam.app import App

from click.testing import CliRunner
from dateutil.tz import tzutc

@pytest.fixture
def runner():
    runner = CliRunner()
    return runner

@pytest.fixture
def obj(pill, settings):
    o = {}
    o['debug'] = False
    o['app'] = sam.app.App(name=settings['name'], session=pill.session)
    return o

def test_app_name_property(tmpdir):
    app_name = 'UnitTestAppName'
    app = App(name=app_name, cwd=tmpdir)
    assert(app.name == app_name)

def test_settings_initialized(tmpdir):
    app = App(debug=False, cwd=tmpdir)
    assert(type(app.settings) == dict)

def test_settings_save(tmpdir):
    assert(not os.path.isfile(str(tmpdir) + '/settings.json'))
    app = App(debug=False, cwd=tmpdir)
    assert(app._save_settings())
    assert(os.path.isfile(str(tmpdir) + '/settings.json'))

def test_scaffold(tmpdir, pill):
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': []}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = { "status_code": 200, "data": { "StackId": "arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz", "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "x-amzn-requestid": "xyz", "content-type": "text/xml", "content-length": "123"}, "RetryAttempts": 0 } } }
    pill.save_response(service='cloudformation', operation='CreateStack', response_data=response, http_response=200)

    app = App(debug=False, cwd=tmpdir, session=pill.session)
    status = app.scaffold()

    assert(app.function_name in app.cloud.template.resources)
    assert(app.rest_name in app.cloud.template.resources)
    assert(status['status_code'] == 200)

def test_check_stack_exists(tmpdir, pill, settings):
    stack_name = 'UnitTestStack'
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': stack_name, 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': settings['name'], 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    app = App(name=settings['name'], debug=False, cwd=tmpdir, session=pill.session)

    status = app.stack_exists(stack_name)
    assert(status)

    status = app.stack_exists()
    assert(status)

def test_check_stack_ready(tmpdir, pill, settings):
    stack_name = 'UnitTestStack'
    stack_name_not = 'UnitTestStackNot'
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': stack_name, 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': settings['name'], 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': []}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    app = App(name=settings['name'], debug=False, cwd=tmpdir, session=pill.session)

    status = app.stack_ready(stack_name)
    assert(status)

    status = app.stack_ready()
    assert(status)

    status = app.stack_ready(stack_name_not)
    assert(not status)

def test_upload_lambda_code(tmpdir, pill, settings):
    function_name = 'UnitTestFunctionName'
    code_filepath = str(tmpdir) + '/lambda.zip'
    open(code_filepath, 'a').close()

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': []}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = { "status_code": 200, "data": { "StackId": "arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz", "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "x-amzn-requestid": "xyz", "content-type": "text/xml", "content-length": "123"}, "RetryAttempts": 0 } } }
    pill.save_response(service='cloudformation', operation='CreateStack', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': settings['name'], 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = { "StackResourceSummaries": [ { "LogicalResourceId": "LambdaExecutionRole", "PhysicalResourceId": settings['name'], "ResourceType": troposphere.awslambda.Function.resource_type, "LastUpdatedTimestamp": { "__class__": "datetime", "year": 2018, "month": 3, "day": 18, "hour": 17, "minute": 24, "second": 33, "microsecond": 565000 }, "ResourceStatus": "CREATE_COMPLETE" } ] }
    pill.save_response(service='cloudformation', operation='ListStackResources', response_data=response, http_response=200)

    response = { "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "date": "123", "content-type": "application/json", "content-length": "649", "connection": "keep-alive", "x-amzn-requestid": "xyz" }, "RetryAttempts": 0 }, "FunctionName": function_name, "FunctionArn": "arn:aws:lambda:us-east-1:123:function:%s" % function_name, "Runtime": "python3.6", "Role": "arn:aws:iam::123:role/xyz", "Handler": "default", "CodeSize": 261, "Description": "", "Timeout": 3, "MemorySize": 128, "LastModified": "123", "CodeSha256": "xyz", "Version": "$LATEST", "TracingConfig": { "Mode": "PassThrough" }, "RevisionId": "6a636cf5-8bdc-4e49-8ca8-bf7e166347d9" }
    pill.save_response(service='lambda', operation='UpdateFunctionCode', response_data=response, http_response=200)

    app = App(name=settings['name'], debug=False, cwd=tmpdir, session=pill.session)
    status = app.scaffold()
    assert(status['status_code'] == 200)

    status = app.upload_lambda_code()
    assert(status)

def test_lambda_dir_exist_check(tmpdir, settings):
    app = App(name=settings['name'], debug=False, cwd=tmpdir)
    lambda_dir = str(tmpdir) + '/lambda'
    if os.path.exists(lambda_dir):
        shutil.rmtree(lambda_dir)

    status = app._lambda_dir_exists()
    assert(not status)

    os.mkdir(lambda_dir)
    status = app._lambda_dir_exists()
    assert(status)

def test_lambda_zip(tmpdir, settings):
    app = App(name=settings['name'], debug=False, cwd=tmpdir)
    lambda_dir = str(tmpdir) + '/lambda'
    lambda_zip = str(tmpdir) + '/lambda.zip'
    if not os.path.exists(lambda_dir):
        os.mkdir(lambda_dir)

    app._package_lambda()
    assert(os.path.exists(lambda_zip))

def test_cli(runner):
    result = runner.invoke(sam.app.cli, obj={})
    assert(result.exit_code == 0)

def test_cli_scaffold_dry(runner, obj, pill):
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': []}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    result = runner.invoke(sam.app.scaffold, ['--dry'], obj=obj)
    assert(result.exit_code == 0)
    assert(result.output == 'scaffolding...\n')

def test_cli_stack_exists(runner, obj, pill, settings):
    stack_name = 'UnitTestStack'
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': stack_name, 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': settings['name'], 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': settings['name'], 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    result = runner.invoke(sam.app.exists, ['--stack', stack_name], obj=obj)
    assert(result.output == 'stack %s exists\n' % stack_name)

    result = runner.invoke(sam.app.exists, obj=obj)
    assert(result.output == 'stack %s exists\n' % settings['name'])

    result = runner.invoke(sam.app.exists, ['--ready'], obj=obj)
    assert(result.output == 'stack %s ready\n' % settings['name'])

def test_cli_upload_lambda_code(runner, obj, pill, settings):
    function_name = obj['app'].function_name

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': []}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = { "status_code": 200, "data": { "StackId": "arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz", "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "x-amzn-requestid": "xyz", "content-type": "text/xml", "content-length": "123"}, "RetryAttempts": 0 } } }
    pill.save_response(service='cloudformation', operation='CreateStack', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': settings['name'], 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = { "StackResourceSummaries": [ { "LogicalResourceId": "LambdaExecutionRole", "PhysicalResourceId": settings['name'], "ResourceType": troposphere.awslambda.Function.resource_type, "LastUpdatedTimestamp": { "__class__": "datetime", "year": 2018, "month": 3, "day": 18, "hour": 17, "minute": 24, "second": 33, "microsecond": 565000 }, "ResourceStatus": "CREATE_COMPLETE" } ] }
    pill.save_response(service='cloudformation', operation='ListStackResources', response_data=response, http_response=200)

    response = { "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "date": "123", "content-type": "application/json", "content-length": "649", "connection": "keep-alive", "x-amzn-requestid": "xyz" }, "RetryAttempts": 0 }, "FunctionName": function_name, "FunctionArn": "arn:aws:lambda:us-east-1:123:function:%s" % function_name, "Runtime": "python3.6", "Role": "arn:aws:iam::123:role/xyz", "Handler": "default", "CodeSize": 261, "Description": "", "Timeout": 3, "MemorySize": 128, "LastModified": "123", "CodeSha256": "xyz", "Version": "$LATEST", "TracingConfig": { "Mode": "PassThrough" }, "RevisionId": "6a636cf5-8bdc-4e49-8ca8-bf7e166347d9" }
    pill.save_response(service='lambda', operation='UpdateFunctionCode', response_data=response, http_response=200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': settings['name'], 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = { "StackResourceSummaries": [ { "LogicalResourceId": "LambdaExecutionRole", "PhysicalResourceId": function_name, "ResourceType": troposphere.awslambda.Function.resource_type, "LastUpdatedTimestamp": { "__class__": "datetime", "year": 2018, "month": 3, "day": 18, "hour": 17, "minute": 24, "second": 33, "microsecond": 565000 }, "ResourceStatus": "CREATE_COMPLETE" } ] }
    pill.save_response(service='cloudformation', operation='ListStackResources', response_data=response, http_response=200)

    result = runner.invoke(sam.app.scaffold, obj=obj)
    assert(result.exit_code == 0)
    assert(result.output == 'scaffolding...\n')

    result = runner.invoke(sam.app.update, obj=obj)
    assert(result.output == 'lambda function %s updated\n' % function_name)
