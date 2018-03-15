import boto3
import uuid

class Bucket(object):
    def __init__(self, settings):
        self.client = boto3.client('s3')
        self.settings = settings

        self._initialize()

    def _initialize(self):
        self.name = self.settings['bucket'] if 'bucket' in self.settings else 'my-lambda-%s' % uuid.uuid4()

    def bucket_exists(self):
        exists = False
        buckets = self.client.list_buckets()
        for ibucket in buckets['Buckets']:
            ibucket_name = ibucket['Name']
            if ibucket_name == self.name:
                exists = True # bucket already exists
                break

        return exists

    def create_bucket(self):
        exists = self.bucket_exists()
        if exists:
            return

        status = self.client.create_bucket(Bucket=self.name)
        return status
