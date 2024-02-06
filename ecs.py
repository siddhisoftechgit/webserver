import aws_cdk as cdk
from aws_cdk.aws_ecr import Repository
from aws_cdk.aws_ecs import Cluster, FargateTaskDefinition, ContainerImage
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedFargateService
from aws_cdk.aws_ec2 import SecurityGroup, Peer, Port, Vpc
from aws_cdk.aws_iam import Role, ServicePrincipal
from constructs import Construct
from aws_cdk import (
    aws_ecs as ecs,
    aws_iam as iam
)
class EcsStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fai_vpc_id = "vpc-0120297056c23531f" 

        fai_vpc = Vpc.from_lookup(self, "FAIVPC", vpc_id=fai_vpc_id)

        # ecr_repository = Repository(self, "FAIEcrRepository")
        ecr_repository = "httpd"

        ecs_cluster = Cluster(self, "FAIEcsCluster",
            vpc=fai_vpc
        )


        execution_role = iam.Role(self, "ExecutionRole",
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )
        execution_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonECSTaskExecutionRolePolicy'))

        # Define the task role
        task_role = iam.Role(self, "TaskRole",
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )
        task_role.add_to_policy(iam.PolicyStatement(
            actions=["ecr:*","iam:CreateServiceLinkedRole"],
            resources=['*']
        ))        

        task_definition = FargateTaskDefinition(self, "FAITaskDefinition",
            cpu=256,
            memory_limit_mib=512,
            execution_role=execution_role,
            task_role=task_role            
        )

        task_definition.add_container("FAIContainer",
            image=ContainerImage.from_registry(ecr_repository),
            essential=True,
            port_mappings=[ecs.PortMapping(container_port=80)]
        )

        security_group = SecurityGroup(self, "FAISecurityGroup",
            vpc=ecs_cluster.vpc,
            allow_all_outbound=True
        )
        security_group.add_ingress_rule(Peer.any_ipv4(), Port.tcp(80))

        ApplicationLoadBalancedFargateService(self, "FAIFargateService",
            cluster=ecs_cluster,
            task_definition=task_definition,
            security_groups=[security_group],
            public_load_balancer=True
        )
