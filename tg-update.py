import boto3
import json

# Initialize clients
rds_client = boto3.client('rds')
ec2_client = boto3.client('ec2')
elbv2_client = boto3.client('elbv2')

RDS_PROXY_NAME = 'your-rds-proxy-name'  # Replace with your RDS proxy name
TARGET_GROUP_ARN = 'your-target-group-arn'  # Replace with your Target Group


def get_rds_proxy_network_interfaces(rds_proxy_name):
    try:
        # Describe the RDS proxy to get the details
        response = rds_client.describe_db_proxies(DBProxyName=rds_proxy_name)
        
        if not response['DBProxies']:
            raise Exception(f"No RDS proxy found with name: {rds_proxy_name}")
        
        proxy = response['DBProxies'][0]
        endpoint = proxy['Endpoint']
        
        return [endpoint]
    except Exception as e:
        print(f"Error retrieving RDS proxy network interfaces: {e}")
        raise e


def get_existing_target_group_ips(target_group_arn):
    """
    Retrieve the IP addresses of the targets registered in the specified target group.
    """
    try:
        # Describe the target health to get the registered targets
        response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
        
        # Extract IP addresses from the response
        target_ips = [target['Target']['Id'] for target in response['TargetHealthDescriptions']]
        
        return target_ips
    except Exception as e:
        print(f"Error retrieving target group IPs: {e}")
        raise e


def update_target_group(target_group_arn, private_ips):
    try:
        # Get current registered targets
        current_targets = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
        current_ips = [target['Target']['Id'] for target in current_targets['TargetHealthDescriptions']]
        
        # Determine which IPs need to be registered or deregistered
        ips_to_register = [ip for ip in private_ips if ip not in current_ips]
        ips_to_deregister = [ip for ip in current_ips if ip not in private_ips]

        # Register new IPs
        if ips_to_register:
            elbv2_client.register_targets(
                TargetGroupArn=target_group_arn,
                Targets=[{'Id': ip, 'Port': 3306} for ip in ips_to_register]
            )

        # Deregister old IPs
        if ips_to_deregister:
            elbv2_client.deregister_targets(
                TargetGroupArn=target_group_arn,
                Targets=[{'Id': ip, 'Port': 3306} for ip in ips_to_deregister]
            )

        print(f"Successfully updated target group. Registered IPs: {ips_to_register}, Deregistered IPs: {ips_to_deregister}")
    except Exception as e:
        print(f"Error updating target group: {e}")
        raise e


def lambda_handler(event, context):
    try:
        # Get the IP addresses of the RDS proxy
        proxy_ips = get_rds_proxy_network_interfaces(RDS_PROXY_NAME)
        
        # Update the target group with the new private IPs
        update_target_group(TARGET_GROUP_ARN, proxy_ips)

        # Log the IP addresses
        print(f"RDS Proxy IP addresses: {proxy_ips}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully updated target group with RDS proxy IP addresses',
                'proxy_ips': proxy_ips
            })
        }
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
