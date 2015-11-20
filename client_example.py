#-------------------------------------------------------------------------------
# simple client to test REST API of Job Launcher
import httplib
import json
from cStringIO import StringIO

#-------------------------------------------------------------------------------
authority = "localhost:8181"

#-------------------------------------------------------------------------------
def callGetJobStatus( joblist ):
    conn = httplib.HTTPConnection( authority )

    # encode the request params
    params = {
        'joblist': joblist,
        }

    payload = json.dumps( params, ensure_ascii=False )
    payload.encode( 'utf-8' )

    # define the params encoding
    headers = { 'Content-Type': 'application/json; charset=utf-8'}

    # call the remote service
    cleanURI = '/jobs'
    conn.request( 'GET', cleanURI, body=payload, headers=headers )

    # get the result
    retValues = {}
    response = conn.getresponse()
    if response.status == 200:
        try:
            retValues = json.loads( response.read() )
        except ValueError:
            print "error: can't decode json response"
    else:
        print "error :", response.status, response.reason

    print retValues

#-------------------------------------------------------------------------------
def callRunJob( user, params ):
    conn = httplib.HTTPConnection( authority )

    # encode the request params
    params = {
        'user': user,
        'program': 'trufa',
        'params': params,
        }

    payload = json.dumps( params, ensure_ascii=False )
    payload.encode( 'utf-8' )

    # define the params encoding
    headers = { 'Content-Type': 'application/json; charset=utf-8'}

    # call the remote service
    cleanURI = '/jobs'
    conn.request( 'PUT', cleanURI, body=payload, headers=headers )

    # get the result
    retValues = {}
    response = conn.getresponse()
    if response.status == 200:
        try:
            retValues = json.loads( response.read() )
        except ValueError:
            print "error: can't decode json response"
    else:
        print "error :", response.status, response.reason

    print retValues

#-------------------------------------------------------------------------------
def callJobStatus( jobid ):
    conn = httplib.HTTPConnection( authority )

    # call the remote service
    cleanURI = '/jobs/'+str(jobid)
    conn.request( 'GET', cleanURI )

    # get the result
    retValues = {}
    response = conn.getresponse()
    if response.status == 200:
        try:
            retValues = json.loads( response.read() )
        except ValueError:
            print "error: can't decode json response"
    else:
        print "error :", response.status, response.reason

    print retValues

#-------------------------------------------------------------------------------
def callCancelJob( jobid ):
    conn = httplib.HTTPConnection( authority )

    # encode the request params
    params = {
        'cancel': True,
        }

    payload = json.dumps( params, ensure_ascii=False )
    payload.encode( 'utf-8' )

    # define the params encoding
    headers = { 'Content-Type': 'application/json; charset=utf-8'}

    # call the remote service
    cleanURI = '/jobs/'+str(jobid)
    conn.request( 'POST', cleanURI, body=payload, headers=headers )

    # get the result
    retValues = {}
    response = conn.getresponse()
    if response.status == 200:
        try:
            retValues = json.loads( response.read() )
        except ValueError:
            print "error: can't decode json response"
    else:
        print "error :", response.status, response.reason

    print retValues

#-------------------------------------------------------------------------------
