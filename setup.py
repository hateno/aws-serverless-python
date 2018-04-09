from setuptools import setup, find_packages

setup(
    name='aws-serverless-python',
    version='0.1',
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'sapling = sam.app:main'
        ]
    },
    author='hateno',
    author_email='hateno@users.noreply.github.com',
    description='Serverless Python web application on top of AWS Lambda and Amazon API Gateway',
    license='Apache 2.0',
    url='https://github.com/hateno/aws-serverless-python'
)
