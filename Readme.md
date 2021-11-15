# EC2 Dashboard

This will deploy a simple website (typescript) & api (python), to view deployed ec2 instances
Authentication is handled by Cognito
Deployment is handled by cloudformation (for more details see make file)
Integration testing is handled by behave & selenium

## Deployment

1. Deploy the cloudformation without Certificates `make all DOMAIN=example.com DEPLOY_CERT=false`
2. Update DNS Nameservers for the domain to point to the created hostedzone (outputs Nameservers)
  * This is needed to for certificate verification
3. Update the cloudformation `make all DOMAIN=example.com`

### User Creation

1. Browse to chosen domain, click login and sign-up via cognito
2. Login to the Cognito dashboard and confirm the user
3. Browse to chosen domain and click login

## Components

### Website

The website is built using typescript and webpack, webpack needs 2 environment variables to be present

* `DOMAIN`
* `CLIENT_ID`

It's very basic and rolled by hand without a framework.

Pros: Code is simple and can audited
Cons: It's probably grown to the point where it would be easier to just use react/similar

### API

The api is built as a single file using python3

Again very basic

Pros: Code is simple and can audited
Cons: single file doesn't transform into testable & deployable easily on lambda

### Infrastructure

The infrastructure is built using cloudformation

### Security 

This is handled by cognito & Oauth, allowing no room for mistakes in my code.
For the sake of simplicity, no Cookies are used and the jwk is stored in an variable

### Integration Tests

Tests are written in behave and test both the API and frontend

Note that the tests require:
1. the chrome [selenium chrome webdriver be installed](https://www.selenium.dev/documentation/getting_started/installing_browser_drivers/)
2. A Default VPC to exist (otherwise update `tests/steps/instance_cloudformation.yaml`)
3. `AWS_PROFILE` to be set to a role that can:
 * Create the API (cloudformation, lambda, apigateway, cognito, iam, route53, cloudwatch-logs, s3, cloudfront, acm)
 * Test the API (cognito-idp, cloudformation, ec2)

## TODO

The following areas could be improved

* Frontend - Move to framework
  * Move packaging back to webpack
* API - move to proper repo structure
* Security - add Oauth Providers to prevent the use of a dedicated password