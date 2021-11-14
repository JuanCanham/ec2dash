from pathlib import Path, PurePath
from behave import given, when


@given("an instance is created")
def step_impl(context):
    try:
        context.cloudformation.describe_stacks(StackName=context.stack_name)
    except Exception:
        print(f"Creating Cloudformation stack with instnace ({context.stack_name})")
        create_response = context.cloudformation.create_stack(
            StackName=context.stack_name,
            TemplateBody=open(
                Path(PurePath(__file__).parent, "instance_cloudformation.yaml"),
                "r",
                encoding="utf-8",
            ).read(),
            ResourceTypes=["AWS::EC2::Instance"],
        )
        context.stack_id = create_response["StackId"]
        print(f"Waiting on Cloudformation stack completion ({context.stack_id})")
        waiter = context.cloudformation.get_waiter("stack_create_complete")
        waiter.wait(StackName=context.stack_name)


@when("the instance is started")
def step_impl(context):
    context.instance_id = get_instance_id(context)
    instance = context.ec2.Instance(context.instance_id)
    try:
        instance.start()
    except Exception:
        "ignore this as it's likely already running"
    instance.wait_until_running()


@when("the instance is stopped")
def step_impl(context):
    context.instance_id = get_instance_id(context)
    instance = context.ec2.Instance(context.instance_id)
    instance.stop()
    instance.wait_until_stopped()


@when("the instance is terminated")
def step_impl(context):
    context.instance_id = get_instance_id(context)
    context.cloudformation.delete_stack(StackName=context.stack_name)
    waiter = context.cloudformation.get_waiter("stack_delete_complete")
    waiter.wait(StackName=context.stack_name)


def get_instance_id(context):
    describe_response = context.cloudformation.describe_stacks(
        StackName=context.stack_name
    )
    instance_id = [
        out["OutputValue"]
        for out in describe_response["Stacks"][0]["Outputs"]
        if out["OutputKey"] == "InstanceId"
    ][0]
    print(f"Found instance ({instance_id})")
    return instance_id
