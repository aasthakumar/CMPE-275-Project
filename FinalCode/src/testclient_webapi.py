from config import get_client_map, get_node_details, populate
from client import Client
import server_pb2
import server_pb2_grpc
from server_pb2 import Request, GetRequest, QueryParams 
from flask import Flask, stream_with_context
from flask import request, url_for
import json
import datetime
from datetime import date
from flask import Response
import logging
import chunk
app = Flask(__name__)


logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('test/myapp.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO) 

class HTTPMethodOverrideMiddleware(object):
    allowed_methods = frozenset([
        'GET',
        'HEAD',
        'POST',
        'DELETE',
        'PUT',
        'PATCH',
        'OPTIONS'
    ])
    bodyless_methods = frozenset(['GET', 'HEAD', 'OPTIONS', 'DELETE'])

@app.route('/')
def index():
    return 'OK'

@app.route('/getdata/<fromdate>,<todate>', methods=['GET'])
def getallitems(fromdate,todate): 
    def get_streaming_response(fromdate,todate):
        logger.info(datetime.datetime.now())
        populate()
        node_details = get_node_details(1)
        c = Client(node_details[0],node_details[1])
        for x in (c.GetHandler(fromdate,todate)):
            data = json.dumps((x.datFragment.data).decode('utf-8'))
            yield data
        logger.info(datetime.datetime.now())
    return Response(stream_with_context(get_streaming_response(fromdate,todate)),status=200, mimetype="text/event-stream")
    #return Response("hi",status=200,mimetype='text/json')

@app.route('/postdata',methods=['POST'])
def post_file():
    print("inside post")
    file = request.files['data']
    print(file)
    #chunk.process(file)
    for x in chunk.process(file):
        print(x)
    return Response(status=200)

 
#req = Request(fromSender="",toSender="",getRequest = GetRequest(queryParams=QueryParams(from_utc="2012-01-01",to_utc="2020-01-01"))

def run():
    app.run(host="0.0.0.0", port=7000, debug=True,threaded = True)

if __name__ == "__main__":
    run()

#print(c.GetHandler(1, 2))