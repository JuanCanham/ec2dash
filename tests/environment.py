import os
import random
import string
import boto3
from selenium import webdriver


def before_all(context):
    context.cloudformation = boto3.client("cloudformation")
    context.cognito = boto3.client("cognito-idp")
    context.ec2 = boto3.resource("ec2")

    context.domain = os.environ["DOMAIN"]
    context.user_name = f"test-example@{context.domain}"
    context.dashboard = f"https://{context.domain}/"

    context.api = f"https://api.{context.domain}"
    context.webdriver = webdriver.Chrome()
    context.password = gen_password(32)

    context.stack_name = f"{context.domain.replace('.','-')}-integration-test-stack"

    cleanup_user(context)


def after_all(context):
    cleanup_user(context)


def cleanup_user(context):
    try:
        cfn_response = context.cloudformation.describe_stacks(
            StackName=context.domain.replace(".", "-")
        )
        context.user_pool_id = [
            out["OutputValue"]
            for out in cfn_response["Stacks"][0]["Outputs"]
            if out["OutputKey"] == "UserPoolId"
        ][0]
        context.cognito.admin_delete_user(
            UserPoolId=context.user_pool_id, Username=context.user_name
        )
    except Exception as error:
        print(f"User not deleted as {error}")


def gen_password(length: int):
    password = [random.choice(string.ascii_lowercase) for i in range(length - 3)]
    password += random.choice(string.ascii_uppercase)
    password += random.choice(string.digits)
    password += random.choice("!@£$%^&*()-+".split())
    if os.environ.get("DEBUG") == "true":
        print(f"password for run is {''.join(password)}")
    return "".join(password)
