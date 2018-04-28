Feature: severless web application scaffolding and management

    @slow
    @fixture.app
    @fixture.logging
    Scenario: Create a very basic serverless Python web application
        Given I have an AWS account
        When I run the application to scaffold
        Then the program will have created a scaffold of a basic serverless Python web application

    @slow
    @fixture.app
    @fixture.scaffold
    @fixture.logging
    Scenario: Update Lambda code on serverless Python web application
        Given I have an AWS serverless Python web application already set up
        And I have a local AWS Lambda code that I want to upload
        When I run the application to update the AWS Lambda code
        Then the program will have successfully uploaded the AWS Lambda code for its particular stack
