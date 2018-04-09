Feature: severless web application scaffolding

    @wip
    @slow
    Scenario: Create a very basic serverless Python web application
        Given user has an AWS account
        When user runs the application to scaffold
        Then the program will have created a scaffold of a basic serverless Python web application
