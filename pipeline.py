#-------------------------------------------------------------------------------
import logging
import sys
import multiprocessing
import os
from os import path
import subprocess
import re
import time
import config
import database
import smtplib
from email.mime.text import MIMEText
import httplib
import json
from cStringIO import StringIO

#-------------------------------------------------------------------------------
sys.path.append( config.USERS_LIB )
try:
    import users
except ImportError:
    print "Error loading Users library"
    print "Check USERS_LIB at config file"
    exit(-1)

#-------------------------------------------------------------------------------
remotehost = config.REMOTEHOST
remotehome = config.REMOTEHOME
data_dir = config.DATADIR

authority = config.LAUNCHER_SERVICE

#-------------------------------------------------------------------------------
def encodeRESTParams( params ):
    payload = json.dumps( params, ensure_ascii=False )
    payload.encode( 'utf-8' )

    # define the params encoding
    headers = { 'Content-Type': 'application/json; charset=utf-8'}

    return (payload, headers)

#-------------------------------------------------------------------------------
def getRESTResult( conn ):
    # get output from connection
    retValues = {}
    response = conn.getresponse()
    if response.status == 200:
        try:
            retValues = json.loads( response.read() )
        except ValueError:
            logging.error( "can't decode json response" )
            return None
    else:
        logging.error( "http error %d, %s"
                       % (response.status, response.reason) )
        return None

    # check error
    if not retValues.get('ok' , False ):
        logging.error( "REST return: "
                       + retValues.get('errormsg', "unknown error") )
        return None

    return retValues

#-------------------------------------------------------------------------------
def callGetJobStatus( joblist ):
    conn = httplib.HTTPConnection( authority )

    payload, headers = encodeRESTParams( {'joblist': joblist} )

    # call the remote service
    try:
        conn.request( 'GET', '/jobs', body=payload, headers=headers )
    except:
        logging.error( str(sys.exc_info()) )
        return None

    result = getRESTResult( conn )

    if result is not None:
        return result.get( 'jobs', [] )

    return []

#-------------------------------------------------------------------------------
def callRunJob( user, params ):
    conn = httplib.HTTPConnection( authority )

    # encode the request params
    params = {
        'user': user,
        'program': 'trufa',
        'params': params,
        }

    payload, headers = encodeRESTParams( params )

    # call the remote service
    try:
        conn.request( 'PUT', '/jobs', body=payload, headers=headers )
    except:
        logging.error( str(sys.exc_info()) )
        return None

    result = getRESTResult( conn )

    if result:
        return result.get( 'jobid', None )

    return None

#-------------------------------------------------------------------------------
def callJobStatus( jobid ):
    conn = httplib.HTTPConnection( authority )

    # call the remote service
    try:
        conn.request( 'GET', '/jobs/'+str(jobid) )
    except:
        logging.error( str(sys.exc_info()) )
        return None

    result = getRESTResult( conn )

    print result

    return result

#-------------------------------------------------------------------------------
def callCancelJob( jobid ):
    conn = httplib.HTTPConnection( authority )

    payload, headers = encodeRESTParams( {'cancel': True} )

    # call the remote service
    try:
        conn.request( 'POST', '/jobs/'+str(jobid),
                      body=payload, headers=headers )
    except:
        logging.error( str(sys.exc_info()) )
        return None

    result = getRESTResult( conn )

    if result:
        return result.get( 'ok', False )

    return False

#-------------------------------------------------------------------------------
def startJob( user, var1 ):
    logging.info( "RUNNIN JOB of '%s'", user )
    jobid = callRunJob( user, var1 )
    if jobid is not None:
        if database.insertNewJob( user, jobid ):
            return True

    raise RuntimeError( "Can't start new job for user " + user )

#-------------------------------------------------------------------------------
def cancelJob( user, jobid ):
    logging.info( "CANCELING JOB %d", jobid )
    jobinfo = database.getJobInfo( jobid )
    logging.debug( str(jobinfo) )

    if jobinfo['state'] == database.JOB_COMPLETED or jobinfo['state'] == database.JOB_CANCELED:
        logging.warning( "job %d already canceled", jobid )
        return True

    ret = callCancelJob( jobid )
    if ret:
        database.setJobCanceled( jobid )
        return True

    # Removing job folders:
        # Web and server job names should be corresponding before activating this
    # jname = jobinfo[ 'name' ]
    # print "Removing outputs from Job named: ", jname
    # command =  [ 'ssh', remotehost,
    #              'cd', data_dir + user,
    #              'rm -r', jname,
    #              'touch', "DONE"]
    # proc = subprocess.Popen( command, stdout=subprocess.PIPE )
    #output = proc.communicate()[0]

    return False

#-------------------------------------------------------------------------------
def run():
    p = multiprocessing.Process( target=pipelineLoop )
    p.start()
    return p

#-------------------------------------------------------------------------------
def sendJobCompletedEmail(jobid, username):

    usermail = users.getUserEmail( username )
    if usermail == None:
        logging.warning( "User %d hasn't email", username )
        return

    jobinfo = database.getJobInfo(jobid)

    body = ""
    with open( config.EMAIL_JOB_COMPLETE, 'r' ) as f:
        body = f.read()

    msg = MIMEText( body.format(jobinfo['name'], jobinfo['juid']))

    msg['Subject'] = config.EMAIL_JOB_COMPLETE_SUBJECT.format(jobinfo['name'])
    msg['From'] = config.EMAIL_SENDER
    msg['To'] = usermail

    print msg

    s = smtplib.SMTP( config.EMAIL_SMTP )
    s.sendmail( config.EMAIL_SENDER, usermail, msg.as_string())
    s.quit()

#-------------------------------------------------------------------------------
def updatePipelineState():
    jobs = database.getActiveJobs()
    if len(jobs) > 0:
        logging.info( "Checking %d job/s", len(jobs) )

    jobids = map( lambda j: j['jid'], jobs )
    if len(jobids) > 0:
        jobstats = callGetJobStatus( jobids )

        for stat in jobstats:
            jobid = stat['jobid']
            newstate = {
                'created': database.JOB_CREATED,
                'submitted': database.JOB_SUBMITTED,
                'running': database.JOB_RUNNING,
                'completed': database.JOB_COMPLETED,
                'canceled': database.JOB_CANCELED,
                'failed': database.JOB_FAILED,
                }.get( stat['state'], database.JOB_CREATED )

            jobinfo = database.getJobInfo( jobid )

            if newstate == database.JOB_RUNNING and jobinfo['state'] != database.JOB_RUNNING:
                logging.info( "Job %d start RUNNING", jobid )
                database.setJobRunning( jobid )

            if newstate == database.JOB_COMPLETED:
                # TODO stageout

                logging.info( "Job %d COMPLETED", jobid )
                database.setJobCompleted( jobid )

                #username = database.getUserName( jobinfo['uid'] )
                #sendJobCompletedEmail( jobinfo['jid'], username )

            if newstate == database.JOB_CANCELED:
                logging.info( "Job %d CANCELED", jobid )
                database.setJobCompleted( jobid )

            if newstate == database.JOB_FAILED:
                logging.info( "Job %d FAILED", jobid )
                database.setJobFailed( jobid )

#-------------------------------------------------------------------------------
def pipelineLoop():

    running = True
    logging.info( "Start pipeline loop" )
    while( running ):
        try:

            time.sleep( 100 )
            logging.info( "Update pipeline" )
            updatePipelineState()

        except KeyboardInterrupt:
            running = False
            break

        except:
            logging.error( "unknown error on loop: " + str(sys.exc_info()) )

    logging.info( "Ending pipeline loop" )


#-------------------------------------------------------------------------------
