.PHONY: help all clean install lint test package pre post api website cfn
STACK_NAME := $(subst .,-,$(DOMAIN))
DEPLOY_CERT = true

help:
	@echo 'Main Targets:'
	@echo '  * all DOMAIN=example.com'
	@echo	'  * all DOMAIN=example.com DEPLOY_CERT=false - Deploy the template without a certificate (see Readme)'
	@echo 'Included in all: clean install lint test package deploy sync clear-cache integration-test'
	@echo 'Other Targets: diff pi website cfn lint-makefile [requires docker]'

all: pre deploy post

pre: install lint test package-api package-cfn
post: package-website sync clear-cache integration-test

api: clean-api install-api lint-api test-api package-api
website: clean-website install-website lint-website test-website package-website
cfn: install-api clean-cfn lint-cfn package-cfn

clean: clean-api clean-website clean-cfn

clean-api:
	rm -f api/dist/*

clean-cfn:
	rm -f packaged-cloudformation.yaml

clean-website:
	cd website && npm run clean

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
	pytest -v --cov --cov-report=term-missing --cov-fail-under=95 api/src/

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
	cd website && npm run prepare

deploy: 
	aws cloudformation deploy --template-file packaged-cloudformation.yaml \
		--stack-name $(STACK_NAME) \
		--parameter-overrides Domain=$(DOMAIN) DeployCertificates=$(DEPLOY_CERT) \
		--no-fail-on-empty-changeset --capabilities CAPABILITY_IAM
		
diff:
	aws cloudformation deploy --template-file packaged-cloudformation.yaml \
		--stack-name $(STACK_NAME) \
		--no-fail-on-empty-changeset --no-execute-changeset --capabilities CAPABILITY_IAM
		

sync:
	aws s3 cp website/index.html s3://$(DOMAIN)/
	aws s3 cp website/dist/* s3://$(DOMAIN)/dist/

clear-cache:
	aws cloudfront create-invalidation \
		--paths '/*' --distribution-id \
		$(shell aws cloudformation describe-stacks \
		--query 'Stacks[0].Outputs[?OutputKey==`SiteDistributionId`].OutputValue' \
		--output text --stack-name $(STACK_NAME) )

integration-test:
	behave tests/

	
lint-makefile:
	docker run --rm -v $(pwd):/data cytopia/checkmake Makefile

