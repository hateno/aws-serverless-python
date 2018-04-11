import boto3

import sam.app

from behave import *
from click.testing import CliRunner

@given('user has an AWS account')
def step_impl(context):
    iam = boto3.client('iam')
    sts = boto3.client('sts')
    arn = sts.get_caller_identity()['Arn']
    assert(arn is not None)

@when('user runs the application to scaffold')
def step_impl(context):
    obj = {}
    obj['debug'] = True
    obj['app'] = sam.app.App()
    lambda_function_name = 'BehaveFunction'
    apigateway_name = 'BehaveAPIGateway'
    runner = CliRunner()
    status = runner.invoke(sam.app.scaffold, [lambda_function_name, apigateway_name], obj=obj)
    assert(status.output == 'scaffolding...\n')

@then('the program will have created a scaffold of a basic serverless Python web application')
def step_impl(context):
    obj = {}
    obj['debug'] = True
    obj['app'] = sam.app.App()
    stack_name = obj['app'].name
    runner = CliRunner()
    result = runner.invoke(sam.app.exists, obj=obj)
    assert(result.output == 'stack %s exists\n' % stack_name)
