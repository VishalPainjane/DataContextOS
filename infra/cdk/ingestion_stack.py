"""
AWS CDK Stack for Ingestion (Lambda + SQS).
"""

from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_events
)
from constructs import Construct

class IngestionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SQS Queue for metadata ingestion tasks
        self.ingestion_queue = sqs.Queue(
            self, "IngestionQueue",
            visibility_timeout=Duration.minutes(15)
        )

        # Lambda function to process ingestion events
        # We would use a container image lambda here due to dependencies
        self.ingestion_lambda = _lambda.DockerImageFunction(
            self, "IngestionLambda",
            code=_lambda.DockerImageCode.from_image_asset(
                "../../",
                cmd=["ingestion.pipeline.handler"] # Placeholder for actual handler
            ),
            timeout=Duration.minutes(15),
            memory_size=2048
        )

        # Trigger Lambda from SQS
        self.ingestion_lambda.add_event_source(
            lambda_events.SqsEventSource(self.ingestion_queue)
        )
