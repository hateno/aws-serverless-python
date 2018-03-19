import datetime
import placebo
import pytest
import uuid

from dateutil.tz import tzutc
from sam.template import Cloud

@pytest.fixture
def settings():
    '''
    Default settings for bucket object creation
    '''
    settings = dict()
    settings['bucket'] = 'UnitTestBucket'
    settings['template'] = 'UnitTestCloudformation'
    return settings

@pytest.fixture
def session():
    import boto3
    return boto3.Session()

@pytest.fixture
def pill(tmpdir, session):
    '''
    Get placebo for simulate boto3 calls
    '''
    pill = placebo.attach(session, tmpdir)
    pill.playback()
    yield pill
    pill.stop()

@pytest.fixture
def cloud(settings, pill):
    cloud = Cloud(settings, session=pill.session)
    return cloud

def test_template(cloud, settings):
    assert(cloud is not None)
    assert(cloud.name == settings['template'])

def test_s3_template(cloud):
    s3name = 'UnitTestS3Bucket'
    s3description = 'UnitTestS3Bucket Description'
    cloud.add_s3_bucket(s3name, bucket_description=s3description)

    assert(s3name in cloud.template.resources)
    assert(s3name in cloud.template.outputs)
    assert(cloud.template.outputs[s3name].properties['Description'] == s3description)

def test_deploy(cloud, pill):
    response = { "status_code": 200, "data": { "StackId": "arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz", "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "x-amzn-requestid": "xyz", "content-type": "text/xml", "content-length": "123"}, "RetryAttempts": 0 } } }
    pill.save_response(service='cloudformation', operation='CreateStack', response_data=response, http_response=200)

    cloud.add_s3_bucket('UnitTestS3Bucket')

    status = cloud.deploy()
    assert(status['status_code'] == 200)

def test_stack_exists(cloud, pill):
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': cloud.name, 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    status = cloud.stack_exists(cloud.name)
    assert(status)
