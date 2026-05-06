"""
AWS CDK Stack for API (ECS Fargate).
"""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_rds as rds
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, db: rds.DatabaseInstance, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cluster = ecs.Cluster(self, "ApiCluster", vpc=vpc)

        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "ApiService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=2,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("../../"),
                container_port=8000,
                environment={
                    "DCOS_MODE": "prod",
                    "DCOS_DATABASE": "postgresql",
                    # Connection string would be passed via Secrets Manager in production
                }
            ),
            public_load_balancer=True
        )

        # Allow ECS tasks to connect to the database
        db.connections.allow_default_port_from(self.fargate_service.service)
