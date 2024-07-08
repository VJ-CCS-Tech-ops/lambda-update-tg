import boto3
import socket

# Initialize clients for RDS and ELB
rds_client = boto3.client('rds')
elbv2_client = boto3.client('elbv2')
route53_client = boto3.client('route53')

# Configuration variables
rds_proxy_endpoint = 'your-rds-proxy-endpoint.amazonaws.com'
target_group_arn = 'your-target-group-arn'

def get_current_ip(endpoint):
    return socket.gethostbyname(endpoint)

def get_target_group_targets(target_group_arn):
    response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
    return [target['Target']['Id'] for target in response['TargetHealthDescriptions']]

def register_new_target(target_group_arn, ip):
    elbv2_client.register_targets(
        TargetGroupArn=target_group_arn,
        Targets=[{'Id': ip, 'Port': 3306}]
    )

def deregister_old_targets(target_group_arn, targets):
    elbv2_client.deregister_targets(
        TargetGroupArn=target_group_arn,
        Targets=[{'Id': target} for target in targets]
    )

def lambda_handler(event, context):
    current_ip = get_current_ip(rds_proxy_endpoint)
    current_targets = get_target_group_targets(target_group_arn)
    
    if current_ip not in current_targets:
        deregister_old_targets(target_group_arn, current_targets)
        register_new_target(target_group_arn, current_ip)
        
    return {
        'statusCode': 200,
        'body': f'Successfully updated target group {target_group_arn} with IP {current_ip}'
    }
