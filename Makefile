.PHONY: help all clean install lint test package pre post api website cfn init
DOMAIN := ec2dash.example.com
STACK_NAME := $(subst .,-,$(DOMAIN))
DEPLOY_CERT = true

ifeq ($(CI),true)
	CI_DEPLOY_ROLE = --role-arn $(shell aws cloudformation describe-stacks \
		--query 'Stacks[0].Outputs[?OutputKey==`MainStackRole`].OutputValue' \
		--output text --stack-name $(STACK_NAME) )
endif

help:
	@echo 'Main Targets:'
	@echo '  * all DOMAIN=ec2dash.example.com'
	@echo	'  * init DOMAIN=ec2dash.example.com - Initial setup'
	@echo '  * diff DOMAIN=ec2dash.example.com - generate a changeset'
	@echo '  * configure-idp DOMAIN=ec2dash.example.com PROVIDER=Google Id=123456789 SECRET=Hunter1 - configure an identity provider'
	@echo
	@echo 'Included in all: clean install lint test package deploy sync clear-cache integration-test configure-ci'
	@echo 'Other Targets: diff pi website cfn lint-makefile [requires docker]'

all: pre deploy post
init: pre create diff package-website sync configure-ci

pre: install lint test package-api package-cfn
post: package-website sync clear-cache integration-test configure-ci

api: clean-api install-api lint-api test-api package-api
website: install-website lint-website test-website package-website sync
cfn: install-api clean-cfn lint-cfn package-cfn

clean: clean-api clean-cfn

clean-api:
	rm -f api/dist/*

clean-cfn:
	rm -f packaged-cloudformation.yaml

install: install-api install-website

install-api:
	pip install -r api/requirements.txt

install-website:
	cd website && npm i

lint: lint-cfn lint-api lint-website

lint-cfn:
	cfn-lint cloudformation.yaml

lint-api:
	black api/ tests/ &
	cd api && \
	pylint src/*.py && \
	mypy --ignore-missing-imports src/

lint-website:
	cd website && npm run lint

test: test-api test-website

test-api:
	pytest -v --cov-report=term-missing --cov-fail-under=95 --cov api/src/ api/src/

test-website:
	cd website && npm test

package: package-api package-cfn package-website

package-cfn:
	cfn-flip -j cloudformation.yaml | yq --rawfile InlineCode api/dist/index.py \
		'.Resources.DescribeInstancesFunction.Properties.InlineCode = $$InlineCode' \
		| cfn-flip -yc > packaged-cloudformation.yaml

package-api:
	grep ^import api/src/index.py > api/dist/index.py
	grep ^ec2client -B 1 -A 1000 api/src/index.py >> api/dist/index.py
	strip-hints --to-empty --inplace api/dist/index.py

package-website:
	export DOMAIN
	export CLIENT_ID=$(shell aws cloudformation describe-stacks \
				--stack-name $(STACK_NAME) \
				--query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
				--output text ) && \
	cd website && npm run package

create:
	aws cloudformation deploy --template-file packaged-cloudformation.yaml \
		--stack-name $(STACK_NAME) \
		--parameter-overrides Domain=$(DOMAIN) DeployCertificates=false \
		Repo=$(shell git remote -v | head -n 1 | cut -d '.' -f 2 | cut -c 5- | cut -d . -f 1) \
		--no-fail-on-empty-changeset --capabilities CAPABILITY_IAM

deploy:
	aws cloudformation deploy --template-file packaged-cloudformation.yaml \
		--stack-name $(STACK_NAME) \
		--no-fail-on-empty-changeset --capabilities CAPABILITY_IAM $(CI_DEPLOY_ROLE)

configure-idp: api package-cfn
	aws cloudformation deploy --template-file packaged-cloudformation.yaml \
		--stack-name $(STACK_NAME) \
		--parameter-overrides $(PROVIDER)ClientId=$(ID) $(PROVIDER)Secret=$(SECRET) \
		--no-fail-on-empty-changeset --capabilities CAPABILITY_IAM --no-execute-changeset

configure-ci:
	yq -iy ".jobs.Deploy.steps[0].with.\"role-to-assume\" = \"$(shell aws cloudformation describe-stacks \
				--stack-name $(STACK_NAME) --query 'Stacks[0].Outputs[?OutputKey==`DeploymentRole`].OutputValue' \
				--output text )\"" .github/workflows/main.yaml
	yq -iy ".jobs.Diff.steps[0].with.\"role-to-assume\" = \"$(shell aws cloudformation describe-stacks \
				--stack-name $(STACK_NAME) --query 'Stacks[0].Outputs[?OutputKey==`CreateDiffRole`].OutputValue' \
				--output text )\"" .github/workflows/diff.yaml
		
diff: api package-cfn
	CHANGE_SET=$$(aws cloudformation create-change-set \
		--stack-name $(STACK_NAME) \
		--change-set-name diff-change-set-$(GITHUB_SHA) \
		--template-body file://packaged-cloudformation.yaml \
		--parameters \
			ParameterKey=Domain,UsePreviousValue=true \
			ParameterKey=Repo,UsePreviousValue=true \
			ParameterKey=DeployCertificates,ParameterValue=true \
			ParameterKey=GoogleClientId,ParameterValue=true \
			ParameterKey=GoogleSecret,ParameterValue=true \
			ParameterKey=FacebookClientId,ParameterValue=true \
			ParameterKey=FacebookSecret,ParameterValue=true \
		--output text --query Id --capabilities CAPABILITY_IAM  \
		--role-arn $$( aws cloudformation describe-stacks \
			--stack-name $(STACK_NAME) \
			--output text \
			--query 'Stacks[0].Outputs[?OutputKey==`DiffStackRole`].OutputValue' \
		)) && \
		aws cloudformation wait change-set-create-complete --change-set-name $$CHANGE_SET && \
		aws cloudformation describe-change-set --change-set-name $$CHANGE_SET | yq -y

sync:
	cp website/favicon.ico website/dist/favicon.ico
	aws s3 sync --delete website/dist/ s3://$(DOMAIN)/

clear-cache:
	aws cloudfront create-invalidation \
		--paths '/*' --distribution-id \
		$(shell aws cloudformation describe-stacks \
		--query 'Stacks[0].Outputs[?OutputKey==`SiteDistributionId`].OutputValue' \
		--output text --stack-name $(STACK_NAME) )

integration-test:
	behave tests/