import datetime
import pytest

from dateutil.tz import tzutc
from sam.template import Cloud
from sam.bucket import Bucket

@pytest.fixture
def cloud(settings, pill):
    cloud = Cloud(settings, session=pill.session)
    return cloud

def test_bucket_deploy_and_exists(settings, cloud, pill):
    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': []}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    response = { "status_code": 200, "data": { "StackId": "arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz", "ResponseMetadata": { "RequestId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "x-amzn-requestid": "xyz", "content-type": "text/xml", "content-length": "123"}, "RetryAttempts": 0 } } }
    pill.save_response(service='cloudformation', operation='CreateStack', response_data=response, http_response=200)

    cloud.add_s3_bucket(settings['bucket'])

    status = cloud.deploy()
    assert(status['status_code'] == 200)

    response = {'ResponseMetadata': {'HTTPHeaders': {'content-length': '123', 'content-type': 'text/xml', 'date': 'xyz', 'x-amzn-requestid': 'xyz'}, 'HTTPStatusCode': 200, 'RequestId': 'xyz', 'RetryAttempts': 0}, 'StackSummaries': [{'CreationTime': datetime.datetime(2018, 1, 1, tzinfo=tzutc()), 'StackId': 'arn:aws:cloudformation:us-east-1:123:stack/TestStackName/xyz', 'StackName': cloud.name, 'StackStatus': 'CREATE_COMPLETE'}]}
    pill.save_response(service='cloudformation', operation='ListStacks', response_data=response, http_response=200)

    status = cloud.stack_exists(cloud.name)
    assert(status)

    response = { 'Buckets': [{ 'CreationDate': datetime.datetime(2018, 1, 10, 1, 10, 16), 'Name': settings['bucket'] }] }
    pill.save_response(service='s3', operation='ListBuckets', response_data=response, http_response=200)

    bucket = Bucket(settings, pill.session)
    exists = bucket.bucket_exists()
    assert(exists)
