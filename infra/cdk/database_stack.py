"""
AWS CDK Stack for Database (RDS PostgreSQL with pgvector).
"""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    RemovalPolicy,
    SecretValue
)
from constructs import Construct

class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.db_instance = rds.DatabaseInstance(
            self, "DataContextOSDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_1
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MEDIUM
            ),
            allocated_storage=20,
            max_allocated_storage=100,
            database_name="datacontextos",
            credentials=rds.Credentials.from_generated_secret("postgres"),
            removal_policy=RemovalPolicy.SNAPSHOT,
            deletion_protection=True,
        )
