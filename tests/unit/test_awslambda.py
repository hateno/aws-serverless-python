import pytest

from sam.awslambda import Lambda

@pytest.fixture
def awslambda(settings, pill):
    awslambda = Lambda(settings, pill.session)
    return awslambda

def test_lambda_initialize(awslambda):
    assert(awslambda is not None)

def test_lambda_function_exists(awslambda, pill):
    function_name = 'UnitTestFunctionName'

    response = {
        'status_code': 200,
        'data': {'Functions': [{'FunctionName': function_name}]}
    }
    pill.save_response(service='lambda', operation='ListFunctions', response_data=response, http_response=200)

    assert(awslambda.exists(function_name))

def test_lambda_update_function(awslambda, pill, tmpdir):
    function_name = 'UnitTestFunctionName'
    code_filepath = 'lambda.zip'

    response = { "status_code": 200, "data": { "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "date": "123", "content-type": "application/json", "content-length": "649", "connection": "keep-alive", "x-amzn-requestid": "xyz" }, "RetryAttempts": 0 }, "FunctionName": function_name, "FunctionArn": "arn:aws:lambda:us-east-1:123:function:%s" % function_name, "Runtime": "python3.6", "Role": "arn:aws:iam::123:role/xyz", "Handler": "default", "CodeSize": 261, "Description": "", "Timeout": 3, "MemorySize": 128, "LastModified": "123", "CodeSha256": "xyz", "Version": "$LATEST", "TracingConfig": { "Mode": "PassThrough" }, "RevisionId": "6a636cf5-8bdc-4e49-8ca8-bf7e166347d9" } }
    pill.save_response(service='lambda', operation='UpdateFunctionCode', response_data=response, http_response=200)

    response = awslambda.update(function_name, code=code_filepath)
    assert(response['status_code'] == 200)

def test_lambda_update_function_filenotfound(awslambda, pill):
    function_name = 'UnitTestFunctionName'
    code_filepath = 'does_not_exist'

    with pytest.raises(FileNotFoundError):
        awslambda.update(function_name, code=code_filepath)

def test_lambda_update_function_handler(awslambda, pill):
    function_name = 'UnitTestFunctionName'
    handler = 'main.exports'

    response = { "status_code": 200, "data": { "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "date": "123", "content-type": "application/json", "content-length": "123", "connection": "keep-alive", "x-amzn-requestid": "xyz" }, "RetryAttempts": 0 }, "FunctionName": function_name, "FunctionArn": "arn:aws:lambda:us-east-1:123:function:%s" % function_name, "Runtime": "python3.6", "Role": "arn:aws:iam::123:role/role", "Handler": "main.handler", "CodeSize": 123, "Description": "", "Timeout": 3, "MemorySize": 128, "LastModified": "123", "CodeSha256": "xyz", "Version": "$LATEST", "TracingConfig": { "Mode": "PassThrough" }, "RevisionId": "xyz" } }
    pill.save_response(service='lambda', operation='UpdateFunctionConfiguration', response_data=response, http_response=200)

    response = awslambda.update(function_name, handler=handler)
    assert(response['status_code'] == 200)
