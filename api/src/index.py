import json
from typing import Dict, Optional
from typing import TypedDict
import boto3
from aws_lambda_typing.events.api_gateway_proxy import APIGatewayProxyEventV2
from aws_lambda_typing.responses.api_gateway_proxy import APIGatewayProxyResponseV2
from aws_lambda_typing.context.context import Context


class Instance(TypedDict):
    Name: str
    Id: str
    Type: str
    State: str
    AZ: str
    PublicIps: list[str]
    PrivateIps: list[str]


class Tag(TypedDict):
    Key: str
    Value: str


class IpLists(TypedDict):
    publicIps: list[str]
    privateIps: list[str]


class ResponseBody(TypedDict, total=False):
    NextToken: str
    Instances: list[Instance]


ec2client = boto3.client("ec2")


def get_name_from_tags(tags: list[Tag]) -> Optional[str]:
    for tag in tags:
        if tag["Key"] == "Name":
            return tag["Value"]

    for tag in tags:
        if tag["Key"] == "name":
            return tag["Value"]

    for tag in tags:
        if tag["Key"].lower().strip() == "name":
            return tag["Value"]

    return None


def get_ips(inst: dict) -> IpLists:
    private_ips = set()
    public_ips = set()
    if "PrivateIpAddress" in inst:
        private_ips.add(inst["PrivateIpAddress"])
    if "PublicIpAddress" in inst:
        public_ips.add(inst["PublicIpAddress"])

    for inter in inst.get("NetworkInterfaces", []):
        if "PrivateIpAddress" in inter:
            private_ips.add(inter["PrivateIpAddress"])
        if "Association" in inter and "PublicIp" in inter["Association"]:
            public_ips.add(inter["Association"]["PublicIp"])

        for priv_ip in inter.get("PrivateIpAddresses", []):
            if "PrivateIpAddress" in priv_ip:
                private_ips.add(priv_ip["PrivateIpAddress"])
            if "Association" in priv_ip and "PublicIp" in priv_ip["Association"]:
                public_ips.add(priv_ip["Association"]["PublicIp"])

    return {
        "publicIps": sorted(list(public_ips)),
        "privateIps": sorted(list(private_ips)),
    }


def parse_instance(inst: dict) -> Instance:
    ips = get_ips(inst)
    name = None
    if "Tags" in inst:
        name = get_name_from_tags(inst["Tags"])
    return {
        "Name": name or inst["InstanceId"],
        "Id": inst["InstanceId"],
        "Type": inst["InstanceType"],
        "State": inst["State"]["Name"],
        "AZ": inst["Placement"]["AvailabilityZone"],
        "PublicIps": list(ips["publicIps"]),
        "PrivateIps": list(ips["privateIps"]),
    }


def describe_instances(params: Dict[str, str]) -> dict:
    if (
        "MaxResults" in params
        and params["MaxResults"].isdecimal()
        and 1000 >= int(params["MaxResults"]) > 5
    ):
        if "NextToken" in params:
            return ec2client.describe_instances(
                MaxResults=int(params["MaxResults"]), NextToken=params["NextToken"]
            )
        return ec2client.describe_instances(MaxResults=int(params["MaxResults"]))
    if "NextToken" in params:
        return ec2client.describe_instances(NextToken=params["NextToken"])

    return ec2client.describe_instances()


def handler(
    event: APIGatewayProxyEventV2, _context: Context
) -> APIGatewayProxyResponseV2:
    try:
        response = describe_instances(event.get("queryStringParameters", {}))

        instances = []
        for res in response["Reservations"]:
            for instance in res["Instances"]:
                instances.append(parse_instance(instance))

        print(f"Got {len(instances)} instances")
        body: ResponseBody = {"Instances": instances}
        if "NextToken" in response:
            body["NextToken"] = response["NextToken"]

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(body),
        }
    except Exception as error:  # pylint: disable=broad-except
        print(f"Error when sending request, [{error}]")
        return {"statusCode": 500, "body": "Internal Error"}
