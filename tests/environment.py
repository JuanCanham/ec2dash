import os
import random
import string
import boto3
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager


def before_all(context):
    context.cloudformation = boto3.client("cloudformation")
    context.cognito = boto3.client("cognito-idp")
    context.ec2 = boto3.resource("ec2")

    context.domain = os.environ["DOMAIN"]
    context.user_name = f"test-example@{context.domain}"
    context.dashboard = f"https://{context.domain}"

    context.api = f"https://api.{context.domain}"
    context.webdriver = webdriver.Firefox(
        executable_path=GeckoDriverManager().install()
    )
    context.password = gen_password(32)

    context.main_stack_name = context.domain.replace(".", "-")
    context.test_stack_name = f"{context.main_stack_name}-integration-test-stack"

    cleanup_user(context)


def after_all(context):
    cleanup_user(context)


def cleanup_user(context):
    try:
        cfn_response = context.cloudformation.describe_stacks(
            StackName=context.main_stack_name
        )
        context.user_pool_id = [
            out["OutputValue"]
            for out in cfn_response["Stacks"][0]["Outputs"]
            if out["OutputKey"] == "UserPoolId"
        ][0]
        context.cognito.admin_delete_user(
            UserPoolId=context.user_pool_id, Username=context.user_name
        )
    except context.cognito.exceptions.UserNotFoundException:
        """Ignore if user doesnt exist"""


def gen_password(length: int):
    password = [random.choice(string.ascii_lowercase) for i in range(length - 3)]
    password += random.choice(string.ascii_uppercase)
    password += random.choice(string.digits)
    password += random.choice("!@£$%^&*()-+".split())
    if os.environ.get("DEBUG") == "true":
        print(f"password for run is {''.join(password)}")
    return "".join(password)
