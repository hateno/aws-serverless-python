import boto3
import logging
import os
import time

import sam.app

from behave import *

@given('I have an AWS account')
def step_impl(context):
    iam = boto3.client('iam')
    sts = boto3.client('sts')
    arn = sts.get_caller_identity()['Arn']
    assert(arn is not None)

@when('I run the application to scaffold')
def step_impl(context):
    status = context.runner.invoke(sam.app.scaffold, obj=context.obj)
    assert(status.output == 'scaffolding...\n')

@then('the program will have created a scaffold of a basic serverless Python web application')
def step_impl(context):
    result = context.runner.invoke(sam.app.exists, obj=context.obj)
    stack_name = context.obj['app'].name
    assert(result.output == 'stack %s exists\n' % stack_name)

@given('I have an AWS serverless Python web application already set up')
def step_impl(context):
    stack_name = context.obj['app'].name

    exists_status = context.runner.invoke(sam.app.exists, obj=context.obj)
    context.log.info('stack exist status %s' % exists_status.output)
    if exists_status != 'stack %s exists' % stack_name:
        status = context.runner.invoke(sam.app.scaffold, obj=context.obj)
        assert(status.output == 'scaffolding...\n')

    ready_status = None
    timeout = 10
    while ready_status is None or ready_status.output != 'stack %s ready\n' % stack_name:
        ready_status = context.runner.invoke(sam.app.exists, ['--ready'], obj=context.obj)
        time.sleep(5)
        timeout -= 1
        if timeout == 0:
            break
    assert(ready_status.output == 'stack %s ready\n' % stack_name)

    result = context.runner.invoke(sam.app.exists, obj=context.obj)
    assert(result.output == 'stack %s exists\n' % stack_name)

@given('I have a local AWS Lambda code that I want to upload')
def step_impl(context):
    assert(os.path.isdir('./lambda'))
    assert(context.obj['app']._lambda_dir_exists())

@when('I run the application to update the AWS Lambda code')
def step_impl(context):
    result = context.runner.invoke(sam.app.update, obj=context.obj)
    function_name = context.obj['app'].cloud.function_name
    assert(result.output == 'lambda function %s updated\n' % function_name)

@then('the program will have successfully uploaded the AWS Lambda code for its particular stack')
def step_impl(context):
    client = boto3.client('lambda')
    function_name = context.obj['app'].cloud.function_name
    response = client.get_function(FunctionName=function_name)
    size = response['Configuration']['CodeSize']
    statinfo = os.stat('./lambda.zip')
    assert(size == statinfo.st_size)
