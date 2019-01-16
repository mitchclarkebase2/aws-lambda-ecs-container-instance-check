import boto3
import json
import os

class Config:
    """Lambda function runtime configuration"""

    CLUSTER = 'CLUSTER'
    REPORT_AS_CW_METRICS = 'REPORT_AS_CW_METRICS'
    CW_METRICS_NAMESPACE = 'CW_METRICS_NAMESPACE'

    def __init__(self, event):
        self.event = event
        self.defaults = {
            self.CLUSTER: 'default',
            self.REPORT_AS_CW_METRICS: '1',
            self.CW_METRICS_NAMESPACE: 'EcsCICheck',
        }

    def __get_property(self, property_name):
        if property_name in self.event:
            return self.event[property_name]
        if property_name in os.environ:
            return os.environ[property_name]
        if property_name in self.defaults:
            return self.defaults[property_name]
        return None

    @property
    def cluster(self):
        return self.__get_property(self.CLUSTER)


    @property
    def cwoptions(self):
        return {
            'enabled': self.__get_property(self.REPORT_AS_CW_METRICS),
            'namespace': self.__get_property(self.CW_METRICS_NAMESPACE),
        }

class EcsContainerInstanceCheck:
    """Query ECS cluster instances for agent health status"""

    def __init__(self,config):
        self.ecs_client = boto3.client('ecs')
        self.cluster = config.cluster

    def execute(self):
        response = []
        print(f"Checking instances in {self.cluster} ECS cluster")
        instances = self.get_container_instances()

        if not instances:
            return response

        instance_details = self.get_instances_details(instances)
        for instance in instance_details:
            response.append({
                'Disconnected Instance': {
                    'InstanceId': instance['ec2InstanceId'],
                    'AgentConnected': instance['agentConnected'],
                    'Status': instance['status'],
                    'RunningTasks': instance['runningTasksCount']
                }
            })
        return response

    def get_container_instances(self):
        instances = []
        try:
            response = self.ecs_client.list_container_instances(
                cluster=self.cluster,
                maxResults=100,
                filter="agentConnected == false"
            )
            instances=instances+response['containerInstanceArns']
        except self.ecs_client.exceptions.ClusterNotFoundException as e:
            raise ValueError(f"{self.cluster} ecs cluster not found")
        return instances


    def get_instances_details(self,instances):
        response = self.ecs_client.describe_container_instances(
            cluster=self.cluster,
            containerInstances=instances
        )

        return response['containerInstances']



class ResultReporter:
    """Reporting results to CloudWatch"""

    def __init__(self, config):
        self.options = config.cwoptions
        self.cluster = config.cluster

    def report(self,count):
        if self.options['enabled'] == '1':
            try:
                cloudwatch = boto3.client('cloudwatch')
                metric_data = [{
                    'MetricName': 'DisconnectedEcsContainerInstances',
                    'Dimensions': [
                        {'Name': 'Cluster', 'Value': self.cluster}
                    ],
                    'Unit': 'None',
                    'Value': int(count)
                }]
                result = cloudwatch.put_metric_data(
                    MetricData=metric_data,
                    Namespace=self.options['namespace']
                )
                print(f"Sent data to CloudWatch requestId=:{result['ResponseMetadata']['RequestId']}")
            except Exception as e:
                print(f"Failed to publish metrics to CloudWatch:{e}")


def run_check(event, context):
    """Lambda function handler"""

    config = Config(event)
    ecs_ci_check = EcsContainerInstanceCheck(config)
    results = ecs_ci_check.execute()

    if not results:
        return f"All ECS container instances in {config.cluster} cluster are connected"

    print(f"Found {len(results)} ECS conatiner instance(s) with their agent disconnected")
    for result in results:
        print(json.dumps(result))

    ResultReporter(config).report(len(results))

    return "Check Successful"
