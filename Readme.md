# EC2 Dashboard

[![Validation](https://github.com/JuanCanham/ec2dash/actions/workflows/push.yaml/badge.svg)](https://github.com/JuanCanham/ec2dash/actions/workflows/push.yaml)

This will deploy a simple website (typescript) & api (python), to view deployed ec2 instances
Authentication is handled by Cognito
Deployment is handled by cloudformation (for more details see make file)
Integration testing is handled by behave & selenium

## Initial Deployment

1. Deploy the cloudformation without Certificates `make initial DOMAIN=example.com`
2. Update DNS Nameservers for the domain to point to the created hostedzone (outputs Nameservers)
  * This is needed to for certificate verification
3. Execute the change set against the stack

## Updates

Updates can be run with `make all DOMAIN=example.com` or via CI

### CI/CD

CI/CD is done using github actions, to set this up

1. Deploy `Make initial DOMAIN=ec2dash.juancanham.com`
2. Create a key for the `DeploymentUser` that is created
3. Store the key as a [github actions secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

The CD role cannot deploy IAM changes by design,
these must be deployed using a PR and an admin executing the resultant change set.

Note that deploying the certificate

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
1. A Default VPC to exist (otherwise update `tests/steps/instance_cloudformation.yaml`)
2. `AWS_PROFILE` to be set to a role that can:
 * Create the API (cloudformation, lambda, apigateway, cognito, iam, route53, cloudwatch-logs, s3, cloudfront, acm)
 * Test the API (cognito-idp, cloudformation, ec2)

## TODO

The following areas could be improved

* Frontend - Move to framework
  * Move packaging back to webpack
* API - move to proper repo structure
* Security - add Oauth Providers to prevent the use of a dedicated password