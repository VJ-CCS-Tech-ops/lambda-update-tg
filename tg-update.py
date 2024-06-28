import boto3
import json

# Initialize clients
elbv2_client = boto3.client('elbv2')

TARGET_GROUP_ARN = 'your-target-group-arn'  # Replace with your Target Group ARN

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

def lambda_handler(event, context):
    """
    Lambda function handler to get and return the existing target group IPs.
    """
    try:
        # Get the existing target group IPs
        existing_ips = get_existing_target_group_ips(TARGET_GROUP_ARN)
        
        # Log the existing IPs
        print(f"Existing target group IPs: {existing_ips}")

        # Return the IPs as a response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'existing_ips': existing_ips
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
