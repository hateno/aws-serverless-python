import boto3
import uuid

from troposphere import GetAtt, Output, Template, Ref
from troposphere.apigateway import Integration, Method, RestApi, Resource
from troposphere.awslambda import Code, Function
from troposphere.iam import Policy, Role
from troposphere.s3 import Bucket, Private

class Cloud(object):
    version = '2010-09-09'

    def __init__(self, settings, session=None):
        self.client = boto3.client('cloudformation') if session is None else session.client('cloudformation')
        self._name = settings['template']
        self.template = Template()
        self.template.add_version(self.version)

    @property
    def name(self):
        return self._name

    def add_s3_bucket(self, bucket_name, bucket_description=''):
        bucket = self.template.add_resource(Bucket(bucket_name, AccessControl=Private))
        self.template.add_output(Output(bucket_name, Value=Ref(bucket), Description=bucket_description))

    def deploy(self):
        template_body = self.template.to_json()
        status = self.client.create_stack(StackName=self.name, TemplateBody=template_body)
        return status

    def stack_exists(self, stack_name):
        stacks = self.client.list_stacks(StackStatusFilter=['IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE', 'DELETE_IN_PROGRESS', 'DELETE_FALIED'])
        for stack in stacks['StackSummaries']:
            if stack['StackName'] == stack_name:
                return True
        return False
