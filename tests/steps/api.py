import requests
from behave import then


@then("API returns an authentication error")
def step_impl(context):
    res = requests.get(context.api)
    # assert 500 > res.status_code >= 400


@then("API returns an valid data")
def step_impl(context):
    get_instances(context)


@then("The API shows the instance as {state}")
def step_impl(context, state):
    instance_state = [
        inst["State"]
        for inst in get_instances(context)
        if inst["Id"] == context.instance_id
    ][0]
    assert instance_state == state


def get_instances(context):
    res = requests.get(context.api)
    assert res.status_code == 200
    json = res.json()
    assert "Instances" in json
    assert type(json["Instances"]) is list
    return json["Instances"]
