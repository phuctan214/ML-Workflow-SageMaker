#=============================================
import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""

    # Get the s3 address from the Step Function event input
    key = event['s3_key']
    bucket = event['s3_bucket']
    
    print(bucket, key)
    # Download the data from s3 to /tmp/image.png
    path_store = "/tmp/image.png"
    s3_response_object = s3.get_object(Bucket=bucket, Key=key)
    object_content = s3_response_object['Body'].read()
    
    with open("/tmp/image.png", "wb") as f:
        f.write(object_content)

    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }

#=============================================
import json
import sagemaker
import base64
from sagemaker.serializers import IdentitySerializer
from sagemaker.predictor import Predictor
import os
import boto3

# Fill this in with the name of your deployed model
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
sagemaker_runtime = boto3.client('sagemaker-runtime')

def lambda_handler(event, context):
    
    image_data = event['image_data']
    # Decode the image data
    image = base64.b64decode(image_data)

    # Instantiate a Predictor
    response = sagemaker_runtime.invoke_endpoint(EndpointName= ENDPOINT_NAME,Body=image, ContentType='image/png')

    # For this model the IdentitySerializer needs to be "image/png"
    # predictor.serializer = IdentitySerializer("image/png")

    # Make a prediction:
    inferences = json.loads(response['Body'].read().decode('utf-8'))

    # We return the data back to the Step Function    
    event["inferences"] = inferences
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }

#=============================================
import json

THRESHOLD = 0.7

def lambda_handler(event, context):

    # Grab the inferences from the event
    inferences = event['inferences']

    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = max(inferences) >= THRESHOLD

    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }

