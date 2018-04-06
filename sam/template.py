import boto3
import time
import uuid

from troposphere import GetAtt, Join, Output, Template, Ref
from troposphere.apigateway import Integration, IntegrationResponse, Method, MethodResponse, Model, RestApi, Resource
from troposphere.apigateway import ApiKey, Deployment, Stage, StageKey
from troposphere.awslambda import Code, Function, Permission
from troposphere.iam import Policy, Role
from troposphere.s3 import Bucket, Private

class Cloud(object):
    version = '2010-09-09'
    stage_name = 'v1'

    def __init__(self, settings, session=None):
        self.client = boto3.client('cloudformation') if session is None else session.client('cloudformation')
        self._name = settings['template']
        self.template = Template()
        self.template.add_version(self.version)

        self.lambda_role = None
        self.lambda_function = None

    @property
    def name(self):
        return self._name

    def add_s3_bucket(self, bucket_name, bucket_description=''):
        bucket = Bucket(bucket_name, AccessControl=Private)
        self.template.add_resource(bucket)
        self.template.add_output(Output(bucket_name, Value=Ref(bucket), Description=bucket_description))

    def deploy(self):
        template_body = self.template.to_json()
        if self.stack_exists(self.name):
            status = self.client.delete_stack(StackName=self.name)
            while self.stack_exists(self.name):
                time.sleep(5) # add logger
        status = self.client.create_stack(StackName=self.name, TemplateBody=template_body, Capabilities=['CAPABILITY_IAM'])
        return status

    def stack_exists(self, stack_name):
        stacks = self.client.list_stacks(StackStatusFilter=['CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE', 'DELETE_IN_PROGRESS', 'DELETE_FAILED', 'ROLLBACK_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_COMPLETE'])
        for stack in stacks['StackSummaries']:
            if stack['StackName'] == stack_name:
                return True
        return False

    def add_lambda(self, lambda_name, lambda_handler, lambda_role_name):
        self.lambda_role = self.create_lambda_role(lambda_role_name)
        self.template.add_resource(self.lambda_role)

        code = Code(ZipFile=Join('\n', [
            'import json',
            '',
            'def handler(event, context):',
            '\tresponse = {',
            '\t\t\'statusCode\': 200,',
            '\t\t\'headers\': {},',
            '\t\t\'body\': json.dumps(event),',
            '\t\t\'isBase64Encoded\': False',
            '\t}',
            '\treturn response'
        ])) # add default function, update later through upload
        self.lambda_function = Function(
            lambda_name,
            Code=code,
            Handler=lambda_handler,
            Runtime='python3.6',
            Role=GetAtt(lambda_role_name, 'Arn')
        )
        self.template.add_resource(self.lambda_function)

    def create_lambda_role(self, lambda_role_name='LambdaExecutionRole'):
        role = Role(lambda_role_name,
                Path='/',
                Policies=[Policy(
                    PolicyName='root',
                    PolicyDocument={
                        'Version': '2012-10-17',
                        'Statement': [
                            {
                                'Action': [
                                    'logs:*'
                                ],
                                'Resource': 'arn:aws:logs:*:*:*',
                                'Effect': 'Allow'
                            },
                            {
                                'Action': [
                                    's3:GetObject',
                                    's3:PutObject'
                                ],
                                'Resource': [
                                    'arn:aws:s3:::*'
                                ],
                                'Effect': 'Allow'
                            },
                            {
                                'Action': [
                                    'lambda:*'
                                ],
                                'Resource': '*',
                                'Effect': 'Allow'
                            }
                        ]
                    })],
                AssumeRolePolicyDocument={
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Action': ['sts:AssumeRole'],
                        'Effect': 'Allow',
                        'Principal': {
                            'Service': [
                                'lambda.amazonaws.com',
                                'apigateway.amazonaws.com'
                            ]
                        }
                    }]
                },
            )
        return role

    def add_api_gateway(self, apigateway_name):
        # define all value used by api gateway
        lambda_method_name = '%sLambdaMethod' % apigateway_name
        lambda_permission_name = '%sLambdaPermission' % apigateway_name
        resource_name = '%sResource' % apigateway_name
        deployment_name = '%sDeployment' % self.stage_name
        apikey_name = '%sApiKey' % apigateway_name

        # start creating api gateway template
        self.apigateway = RestApi(apigateway_name, Name=apigateway_name)
        self.template.add_resource(self.apigateway)

        resource = Resource(
            resource_name,
            RestApiId=Ref(self.apigateway),
            PathPart='{proxy+}',
            ParentId=GetAtt(apigateway_name, 'RootResourceId')
        )
        self.template.add_resource(resource)

        permission = Permission(
            lambda_permission_name,
            Action='lambda:invokeFunction',
            FunctionName=GetAtt(self.lambda_function, 'Arn'),
            Principal='apigateway.amazonaws.com',
            SourceArn=Join("", [
                'arn:aws:execute-api:',
                Ref('AWS::Region'), ':',
                Ref('AWS::AccountId'), ':',
                Ref(self.apigateway), '/*'
            ])
        )
        self.template.add_resource(permission)

        method = Method(
            lambda_method_name,
            DependsOn=lambda_permission_name,
            RestApiId=Ref(self.apigateway),
            ResourceId=Ref(resource),
            HttpMethod='ANY',
            AuthorizationType='NONE',
            Integration=Integration(
                Type='AWS_PROXY',
                IntegrationHttpMethod='POST',
                Uri=Join("", [
                    'arn:aws:apigateway:',
                    Ref('AWS::Region'),
                    ':lambda:path/2015-03-31/functions/',
                    GetAtt(self.lambda_function, 'Arn'),
                    '/invocations'
                ])
            ),
            MethodResponses=[
                MethodResponse(
                    StatusCode='200'
                )
            ]
        )
        self.template.add_resource(method)

        # create a deployment
        deployment = Deployment(
            deployment_name,
            DependsOn=lambda_method_name,
            RestApiId=Ref(self.apigateway)
        )
        self.template.add_resource(deployment)

        stage = Stage(
            '%sStage' % self.stage_name,
            StageName=self.stage_name,
            RestApiId=Ref(self.apigateway),
            DeploymentId=Ref(deployment)
        )
        self.template.add_resource(stage)

        key = ApiKey(
            apikey_name,
            StageKeys=[StageKey(
                RestApiId=Ref(self.apigateway),
                StageName=Ref(stage)
            )]
        )
        self.template.add_resource(key)
