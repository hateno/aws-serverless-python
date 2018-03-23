import boto3
import os

class Lambda:
    def __init__(self, settings, session=None):
        self.client = boto3.client('lambda') if session is None else session.client('lambda')
        self.settings = settings

    def exists(self, function_name):
        functions = self.client.list_functions()
        for function in functions['data']['Functions']:
            if function['FunctionName'] == function_name:
                return True
        return False

    def update(self, function_name, code=None, handler=None):
        if code is not None:
            if not os.path.exists(code):
                raise FileNotFoundError('%s not found' % code)
            response = self.client.update_function_code(FunctionName=function_name, ZipFile=open(code, 'rb').read())
            if response['status_code'] != 200:
                return response

        if handler is not None:
            response = self.client.update_function_configuration(FunctionName=function_name, Handler=handler)

        return response
