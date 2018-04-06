import datetime
import os
import sys
import uuid

from sam.bucket import Bucket

def test_bucket_initialize(settings, pill):
    bucket = Bucket(settings, pill.session)
    assert(bucket.name == settings['bucket'])

def test_bucket_exists(settings, pill):
    response = { 'Buckets': [{ 'CreationDate': datetime.datetime(2018, 1, 10, 1, 10, 16), 'Name': settings['bucket'] }] }
    pill.save_response(service='s3', operation='ListBuckets', response_data=response, http_response=200)

    bucket = Bucket(settings, pill.session)
    exists = bucket.bucket_exists()
    assert(exists)

def test_bucket_does_not_exist(settings, pill):
    response = {'Buckets': []}
    pill.save_response(service='s3', operation='ListBuckets', response_data=response, http_response=200)

    bucket = Bucket(settings, pill.session)
    exists = bucket.bucket_exists()
    assert(not exists)

def test_bucket_create(settings, pill):
    response = {'Buckets': []}
    pill.save_response(service='s3', operation='ListBuckets', response_data=response, http_response=200)

    response = {'Location': '/%s' % settings['bucket'], 'ResponseMetadata': {'HTTPHeaders': {'content-length': '0', 'location': '/%s' % settings['bucket'], 'server': 'AmazonS3', 'x-amz-id-2': 'xyz', 'x-amz-request-id': 'xyz'}, 'HTTPStatusCode': 200, 'HostId': 'xyz', 'RequestId': 'xyz', 'RetryAttempts': 0}}
    pill.save_response(service='s3', operation='CreateBucket', response_data=response, http_response=200)

    bucket = Bucket(settings, pill.session)
    status = bucket.create_bucket()
    assert(status['ResponseMetadata']['HTTPStatusCode'] == 200)
    assert(status['Location'] == '/%s' % settings['bucket'])

def test_bucket_upload_file(settings, pill, tmpdir):
    response = {"status_code": 200, "data": { "ResponseMetadata": { "RequestId": "xyz", "HostId": "xyz", "HTTPStatusCode": 200, "HTTPHeaders": { "x-amz-id-2": "xyz", "x-amz-request-id": "xyz", "etag": "\"xyz\"", "content-length": "0", "server": "AmazonS3" }, "RetryAttempts": 0 }, "ETag": "\"xyz\"" } }
    pill.save_response(service='s3', operation='PutObject', response_data=response, http_response=200)

    filename = 'test_file.txt'
    p = tmpdir.join(filename)
    p.write('content')
    filepath = str(p)

    bucket = Bucket(settings, pill.session)
    status = bucket.upload_file(filepath, filename)
