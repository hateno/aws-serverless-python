import boto3
import datetime
import os
import sys
import placebo
import pytest
import uuid

from botocore.stub import Stubber
from sam.bucket import Bucket

# TODO replace Stubber with placebo
@pytest.fixture
def settings():
    '''
    Default settings for bucket object creation
    '''
    settings = dict()
    settings['bucket'] = 'test-lambda-%s' % uuid.uuid4()
    return settings

def test_bucket_initialize(settings):
    bucket = Bucket(settings)
    assert(bucket.name == settings['bucket'])

def test_bucket_exists(settings):
    bucket = Bucket(settings)

    stubber = Stubber(bucket.client)
    response = {
        'Buckets': [{
            'CreationDate': datetime.datetime(2018, 1, 10, 1, 10, 16),
            'Name': settings['bucket']
        }]
    }
    expected_params = {}

    stubber.add_response('list_buckets', response, expected_params)
    stubber.activate()

    exists = bucket.bucket_exists()
    assert(exists)

def test_bucket_does_not_exist(settings):
    bucket = Bucket(settings)
    stubber = Stubber(bucket.client)

    response = {
        'Buckets': []
    }
    expected_params = {}
    stubber.add_response('list_buckets', response, expected_params)

    stubber.activate()

    exists = bucket.bucket_exists()
    assert(not exists)

def test_bucket_create(settings):
    bucket = Bucket(settings)
    stubber = Stubber(bucket.client)

    response = {'Buckets': []}
    stubber.add_response('list_buckets', response)

    response = {'Location': '/%s' % settings['bucket'], 'ResponseMetadata': {'HTTPHeaders': {'content-length': '0', 'location': '/%s' % settings['bucket'], 'server': 'AmazonS3', 'x-amz-id-2': 'xyz', 'x-amz-request-id': 'xyz'}, 'HTTPStatusCode': 200, 'HostId': 'xyz', 'RequestId': 'xyz', 'RetryAttempts': 0}}
    expected_params = {'Bucket': settings['bucket']}
    stubber.add_response('create_bucket', response, expected_params)

    stubber.activate()

    status = bucket.create_bucket()
    assert(status['ResponseMetadata']['HTTPStatusCode'] == 200)
