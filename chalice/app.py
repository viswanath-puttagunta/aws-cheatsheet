from chalice import Chalice, BadRequestError
from chalice import NotFoundError
from chalice import CORSConfig
import json
import boto3
from botocore.exceptions import ClientError

app = Chalice(app_name='khelloworld')
app.debug = True

CITIES_TO_STATE = {
  'seattle': 'WA',
  'portland': 'OR'    
}

S3 = boto3.client('s3', region_name='us-east-2')
BUCKET = 'vbucket-test1234'
BUCKET2 = 'vbucket-file1234'

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('vdynamodb')

@app.route('/')
def index():
    return {'hello': 'vworld'}

@app.route('/cities/{city}')
def state_of_city(city):
    try:
        return {'state': CITIES_TO_STATE[city]}
    except KeyError:
        raise BadRequestError("Unknown city '%s', valid choices are: %s" % (
              city, ', '.join(CITIES_TO_STATE.keys())))

@app.route('/objects/{key}', methods=['GET','PUT'], api_key_required=True)
def myobject(key):
    request = app.current_request
    if request.method == 'PUT':
        S3.put_object(Bucket=BUCKET, Key=key,Body=json.dumps(request.json_body))
        with table.batch_writer() as batch:
            batch.put_item(Item = {"fname": key})
    elif request.method == 'GET':
        try:
            response = S3.get_object(Bucket=BUCKET, Key=key)
            return json.loads(response['Body'].read())
        except ClientError as e:
            raise NotFoundError(key)

@app.route('/dynamo/{key}', methods=['GET','PUT'], api_key_required=True)
def dynamofn(key):
    request = app.current_request
    data = request.json_body
    if request.method == 'PUT':
        with table.batch_writer() as batch:
            batch.put_item(Item = data) 
        return data
    elif request.method == 'GET':
        try:
            response = table.get_item(
                Key={'fname':key}
            )
        except ClientError as e:
            raise NotFoundError(key)
        return response

@app.route('/files/{key}', methods=['GET','PUT'], api_key_required=True,content_types=['application/octet-stream'])
def myfile(key):
    request = app.current_request
    if request.method == 'PUT':
        S3.put_object(Bucket=BUCKET2, Key=key,Body=request.raw_body)
    else:
        pass
    return {}

cors_config = CORSConfig(
    allow_origin='https://h876bx1hx2.execute-api.us-east-2.amazonaws.com',
    allow_headers=['X-Special-Header'],
    max_age=600,
    expose_headers=['X-Special-Header'],
    allow_credentials=True
)

@app.route('/custom_cors', methods=['GET'], cors=cors_config)
def supports_custom_cors():
    return {'cors': True}



# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
