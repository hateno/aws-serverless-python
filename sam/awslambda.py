import boto3
import logging
import os

class Lambda:
    def __init__(self, settings, session=None):
        self.log = logging.getLogger(settings['name'])
        self.client = boto3.client('lambda') if session is None else session.client('lambda')
        self.settings = settings

    def exists(self, function_name):
        functions = self.client.list_functions()
        for function in functions['data']['Functions']:
            if function['FunctionName'] == function_name:
                return True
        return False

    def update(self, function_name=None, code=None, handler=None):
        '''
        Updates an AWS Lambda function, either the code or the handler (or both) if they are specified.

        Either the code or handler argument must be specified, or an Exception will be raised.

        Args:
            function_name (str): name of the AWS Lambda function to update
            code (str): zip file location of the lambda code to upload
            handler (str): the name of the handler to update the function configuration
        '''
        if function_name is None:
            if 'function_name' not in self.settings:
                self.log.error('Lambda function name not specified in parameter or settings.json')
                return None
            else:
                function_name = self.settings['function_name']

        if code is None and handler is None:
            raise Exception('No code or handler configuration to update AWS Lambda function')
            return None

        if code is not None:
            if not os.path.exists(code):
                raise FileNotFoundError('%s not found' % code)
            response = self.client.update_function_code(FunctionName=function_name, ZipFile=open(code, 'rb').read())
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                return response


        if handler is not None:
            response = self.client.update_function_configuration(FunctionName=function_name, Handler=handler)

        return response
