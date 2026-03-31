import boto3

_cloudwatch = None

def _get_client():
    global _cloudwatch
    if _cloudwatch is None:
        _cloudwatch = boto3.client("cloudwatch", region_name="ap-northeast-2")
    return _cloudwatch

def put_metric(metric_name: str, value: float, unit: str = "Count", extra_dims: list = []):
    _get_client().put_metric_data(
        Namespace="CDCI/AgentCore",
        MetricData=[{
            "MetricName": metric_name,
            "Dimensions": [{"Name": "agent_name", "Value": "chatbot"}] + extra_dims,
            "Value": value,
            "Unit": unit,
        }]
    )
