import json
from unittest.mock import call, patch
import pytest

import index


@pytest.mark.parametrize(
    "tags",
    [
        [
            {"Key": "Name", "Value": "CorrectName"},
            {"Key": "name", "Value": "InCorrectName"},
        ],
        [
            {"Key": "name", "Value": "CorrectName"},
            {"Key": "nAme", "Value": "InCorrectName"},
        ],
        [
            {"Key": "nAme", "Value": "CorrectName"},
            {"Key": "NotName", "Value": "InCorrectName"},
        ],
    ],
)
def test_get_name_from_tags_returns_name(tags):
    assert index.get_name_from_tags(tags) == "CorrectName"


@pytest.mark.parametrize(
    "tags",
    [
        [],
        [{"Key": "NotName", "Value": "InCorrectName"}],
    ],
)
def test_get_name_from_tags_returns_none(tags):
    assert index.get_name_from_tags(tags) is None


@pytest.mark.parametrize(
    "inst",
    [
        {
            "PrivateIpAddress": "192.168.0.1",
            "PublicIpAddress": "8.8.8.8",
        },
        {
            "NetworkInterfaces": [
                {
                    "PrivateIpAddress": "192.168.0.1",
                    "Association": {"PublicIp": "8.8.8.8"},
                }
            ]
        },
        {
            "NetworkInterfaces": [
                {
                    "PrivateIpAddresses": [
                        {
                            "PrivateIpAddress": "192.168.0.1",
                            "Association": {"PublicIp": "8.8.8.8"},
                        }
                    ]
                }
            ]
        },
        {
            "PrivateIpAddress": "192.168.0.1",
            "PublicIpAddress": "8.8.8.8",
            "NetworkInterfaces": [
                {
                    "PrivateIpAddress": "192.168.0.1",
                    "Association": {"PublicIp": "8.8.8.8"},
                    "PrivateIpAddresses": [
                        {
                            "PrivateIpAddress": "192.168.0.1",
                            "Association": {"PublicIp": "8.8.8.8"},
                        }
                    ],
                }
            ],
        },
    ],
)
def test_get_ips_returns_single_ips(inst):
    assert index.get_ips(inst) == {
        "publicIps": ["8.8.8.8"],
        "privateIps": ["192.168.0.1"],
    }


def test_get_ips_returns_multiple_or_no_ips():
    inst = {
        "PrivateIpAddress": "192.168.0.1",
        "NetworkInterfaces": [
            {
                "PrivateIpAddress": "192.168.0.2",
                "PrivateIpAddresses": [
                    {
                        "PrivateIpAddress": "192.168.0.3",
                    }
                ],
            }
        ],
    }
    assert index.get_ips(inst) == {
        "publicIps": [],
        "privateIps": ["192.168.0.1", "192.168.0.2", "192.168.0.3"],
    }


def test_parse_instance_returns_instnace_data():
    inst = {
        "InstanceId": "i-0c7fd23e5de25b3f8",
        "InstanceType": "small",
        "State": {"Name": "running"},
        "Placement": {"AvailabilityZone": "us-east-1"},
    }
    expected = {
        "Name": "i-0c7fd23e5de25b3f8",
        "Id": "i-0c7fd23e5de25b3f8",
        "Type": "small",
        "State": "running",
        "AZ": "us-east-1",
        "PublicIps": [],
        "PrivateIps": [],
    }

    assert index.parse_instance(inst) == expected

    inst["Tags"] = [{"Key": "Name", "Value": "My Instance"}]
    expected["Name"] = "My Instance"
    assert index.parse_instance(inst) == expected


@patch("index.ec2client")
def test_index_handles_failure(mock_ec2client):
    mock_ec2client.describe_instances.side_effect = Exception()
    assert index.handler({}, {}) == {"statusCode": 500, "body": "Internal Error"}


@patch("index.ec2client")
def test_index_handles_no_params(mock_ec2client):
    mock_ec2client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-0c7fd23e5de25b3f8",
                        "InstanceType": "small",
                        "State": {"Name": "running"},
                        "Placement": {"AvailabilityZone": "us-east-1"},
                    }
                ]
            }
        ]
    }
    result = index.handler({}, {})
    assert result["statusCode"] == 200
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["body"] == json.dumps(
        {
            "Instances": [
                {
                    "Name": "i-0c7fd23e5de25b3f8",
                    "Id": "i-0c7fd23e5de25b3f8",
                    "Type": "small",
                    "State": "running",
                    "AZ": "us-east-1",
                    "PublicIps": [],
                    "PrivateIps": [],
                }
            ]
        }
    )
    assert mock_ec2client.describe_instances.call_count == 1
    assert mock_ec2client.describe_instances.call_args == call()


@patch("index.ec2client")
def test_index_handles_next(mock_ec2client):
    mock_ec2client.describe_instances.return_value = {
        "Reservations": [{"Instances": []}],
        "NextToken": "page-3",
    }
    result = index.handler({"queryStringParameters": {"NextToken": "page-2"}}, {})
    assert result["statusCode"] == 200
    assert result["body"] == json.dumps({"Instances": [], "NextToken": "page-3"})
    assert mock_ec2client.describe_instances.call_args == call(NextToken="page-2")


@patch("index.ec2client")
def test_index_handles_max(mock_ec2client):
    mock_ec2client.describe_instances.return_value = {
        "Reservations": [{"Instances": []}]
    }
    result = index.handler({"queryStringParameters": {"MaxResults": "1000"}}, {})
    assert result["statusCode"] == 200
    assert result["body"] == json.dumps({"Instances": []})
    assert mock_ec2client.describe_instances.call_args == call(MaxResults=1000)


@patch("index.ec2client")
def test_index_handles_max_and_next(mock_ec2client):
    mock_ec2client.describe_instances.return_value = {
        "Reservations": [{"Instances": []}]
    }
    result = index.handler(
        {"queryStringParameters": {"MaxResults": "1000", "NextToken": "page-2"}}, {}
    )
    assert result["statusCode"] == 200
    assert mock_ec2client.describe_instances.call_args == call(
        MaxResults=1000, NextToken="page-2"
    )


@pytest.mark.parametrize("max_results", ["3", "2000", "Hax"])
@patch("index.ec2client")
def test_index_handles_invalid_max(mock_ec2client, max_results):
    mock_ec2client.describe_instances.return_value = {
        "Reservations": [{"Instances": []}]
    }
    result = index.handler({"queryStringParameters": {"MaxResults": max_results}}, {})
    assert result["statusCode"] == 200
    assert result["body"] == json.dumps({"Instances": []})
    assert mock_ec2client.describe_instances.call_args == call()
