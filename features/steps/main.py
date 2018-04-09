import boto3

from behave import *

@given('user has an AWS account')
def step_impl(context):
    iam = boto3.client('iam')
    sts = boto3.client('sts')
    arn = sts.get_caller_identity()['Arn']
    assert(arn is not None)

@when('user runs the application to scaffold')
def step_impl(context):
    assert False

@then('the program will have created a scaffold of a basic serverless Python web application')
def step_impl(context):
    assert False
