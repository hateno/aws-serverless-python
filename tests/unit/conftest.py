import placebo
import pytest

@pytest.fixture
def settings():
    '''
    Default settings for unit tests
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
