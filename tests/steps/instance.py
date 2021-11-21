from pathlib import Path, PurePath
from behave import given, when
from botocore.exceptions import ClientError


@given("an instance is created")
def step_impl(context):
    try:
        context.cloudformation.describe_stacks(StackName=context.test_stack_name)
    except ClientError:
        print(
            f"Creating Cloudformation stack with instnace ({context.test_stack_name})"
        )

        with open(
            Path(PurePath(__file__).parent, "instance_cloudformation.yaml"),
            "r",
            encoding="utf-8",
        ) as template_file:
            create_response = context.cloudformation.create_stack(
                StackName=context.test_stack_name,
                TemplateBody=template_file.read(),
                ResourceTypes=["AWS::EC2::Instance"],
                RoleARN=get_stack_output(
                    context, context.main_stack_name, "IntegrationTestStackRole"
                ),
            )
        context.stack_id = create_response["StackId"]
        print(f"Waiting on Cloudformation stack completion ({context.stack_id})")
        waiter = context.cloudformation.get_waiter("stack_create_complete")
        waiter.wait(StackName=context.test_stack_name)


@when("the instance is started")
def step_impl(context):
    context.instance_id = get_stack_output(
        context, context.test_stack_name, "InstanceId"
    )
    instance = context.ec2.Instance(context.instance_id)
    instance.start()
    instance.wait_until_running()


@when("the instance is stopped")
def step_impl(context):
    context.instance_id = get_stack_output(
        context, context.test_stack_name, "InstanceId"
    )
    instance = context.ec2.Instance(context.instance_id)
    instance.stop()
    instance.wait_until_stopped()


@when("the instance is terminated")
def step_impl(context):
    context.instance_id = get_stack_output(
        context, context.test_stack_name, "InstanceId"
    )
    context.cloudformation.delete_stack(
        StackName=context.test_stack_name,
        RoleARN=get_stack_output(
            context, context.main_stack_name, "IntegrationTestStackRole"
        ),
    )
    waiter = context.cloudformation.get_waiter("stack_delete_complete")
    waiter.wait(StackName=context.test_stack_name)


def get_stack_output(context, stack_name: str, key: str):
    describe_response = context.cloudformation.describe_stacks(StackName=stack_name)
    value = [
        out["OutputValue"]
        for out in describe_response["Stacks"][0]["Outputs"]
        if out["OutputKey"] == key
    ][0]
    return value
