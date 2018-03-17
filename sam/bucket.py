import boto3
import uuid

class Bucket(object):
    def __init__(self, settings, session=None):
        self.client = boto3.client('s3') if session is None else session.client('s3')
        self.settings = settings

        self.name = self.settings['bucket'] if 'bucket' in self.settings else 'my-lambda-%s' % uuid.uuid4()

    def bucket_exists(self):
        buckets = self.client.list_buckets()
        for ibucket in buckets['Buckets']:
            ibucket_name = ibucket['Name']
            if ibucket_name == self.name:
                return True

        return False

    def create_bucket(self):
        exists = self.bucket_exists()
        if exists:
            return

        status = self.client.create_bucket(Bucket=self.name)
        return status

    def upload_file(self, filepath, filename):
        self.client.upload_file(filepath, self.name, filename)
