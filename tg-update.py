import socket
import boto3

# Initialize clients for ELB
elbv2_client = boto3.client('elbv2')

# Configuration variables
rds_proxy_endpoint = 'your-rds-proxy-endpoint.amazonaws.com'
target_group_arn = 'your-target-group-arn'

def get_all_ips(endpoint):
    # Retrieve all IP addresses associated with the endpoint
    addresses = socket.getaddrinfo(endpoint, None)
    # Filter and return only unique IPv4 addresses
    return list(set(addr[4][0] for addr in addresses if addr[1] == socket.SOCK_STREAM))

def get_target_group_targets(target_group_arn):
    response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
    return [target['Target']['Id'] for target in response['TargetHealthDescriptions']]

def register_new_targets(target_group_arn, ips):
    elbv2_client.register_targets(
        TargetGroupArn=target_group_arn,
        Targets=[{'Id': ip, 'Port': 3306} for ip in ips]
    )

def deregister_old_targets(target_group_arn, targets):
    for target in targets:
        elbv2_client.deregister_targets(
            TargetGroupArn=target_group_arn,
            Targets=[{'Id': target}]
        )

def lambda_handler(event, context):
    current_ips = get_all_ips(rds_proxy_endpoint)
    current_targets = get_target_group_targets(target_group_arn)
    
    # Determine which targets need to be deregistered and registered
    targets_to_deregister = [target for target in current_targets if target not in current_ips]
    targets_to_register = [ip for ip in current_ips if ip not in current_targets]
    
    # Deregister old targets
    if targets_to_deregister:
        deregister_old_targets(target_group_arn, targets_to_deregister)
        
    # Register new targets
    if targets_to_register:
        register_new_targets(target_group_arn, targets_to_register)
    
    return {
        'statusCode': 200,
        'body': f'Successfully updated target group {target_group_arn} with IPs {current_ips}'
    }
