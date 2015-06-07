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
pipe_launch = config.LAUNCHER_TOOL
data_dir = config.DATADIR

reSLURMLINE = re.compile(r"slurmids: (?P<slurmids>\d+(,\d+)*)")
reSLURMID = re.compile(r"\,")

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

    print result

    return result

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

    print result

    return result

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

    # Canceling Jobid:
    logging.info( str(jobinfo['slurmids']) )
    for slurmid in jobinfo['slurmids']:
        logging.info( "canceling slurm job %d", slurmid["slurmid"] )

        command = ["ssh", remotehost, "mncancel", str(slurmid["slurmid"]) ]
        proc = subprocess.Popen( command, stdout=subprocess.PIPE )
        output = proc.communicate()[0]
        logging.info( str(output) )

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

    database.setJobCanceled( jobid )
    return True

#-------------------------------------------------------------------------------
def run():
    p = multiprocessing.Process( target=pipelineLoop )
    p.start()
    return p

#-------------------------------------------------------------------------------
def checkSlurmJob( slurmids ):
    if len(slurmids) > 0:
        idsstr = ",".join(map(str,slurmids))
        command = ["ssh", remotehost, "mnq", "--job", idsstr ]
        proc = subprocess.Popen( command, stdout=subprocess.PIPE )
        output = proc.communicate()[0]

        if len(output.splitlines()) <= 1:
            return database.JOB_COMPLETED

        mm = re.search( "RUNNING", output )
        if mm is not None:
            return database.JOB_RUNNING

    return database.JOB_SUBMITTED

#-------------------------------------------------------------------------------
def sendJobCompletedEmail(jobid, username):

    usermail = users.getUserEmail( username )
    if usermail == None:
        logging.warning( "User %d hasn't email", username )
        return

    jdata = database.getJobInfo(jobid)

    body = ""
    with open( config.EMAIL_JOB_COMPLETE, 'r' ) as f:
        body = f.read()

    msg = MIMEText( body.format(jdata['name'], jdata['juid']))

    msg['Subject'] = config.EMAIL_JOB_COMPLETE_SUBJECT.format(jdata['name'])
    msg['From'] = config.EMAIL_SENDER
    msg['To'] = usermail

    print msg

    s = smtplib.SMTP( config.EMAIL_SMTP )
    s.sendmail( config.EMAIL_SENDER, usermail, msg.as_string())
    s.quit()

#-------------------------------------------------------------------------------
def pipelineLoop():
    try:
        logging.info( "Start pipeline loop" )
        while (1 == 1):
            time.sleep( 60 )
            # check
            zjobs = database.getJustCreatedJobs()
            if len(zjobs) > 0:
                zjids = map( lambda js: js['jid'], zjobs )
                logging.warning( "%d zombie jobs: %s", len(zjobs), str(zjids) )

            jobs = database.getActiveJobs()
            if len(jobs) > 0:
                logging.info( "Checking %d job/s", len(jobs) )

            for job in jobs:
                jobid = job['jid']
                newstate = checkSlurmJob( job['slurmids'] )
                if newstate == database.JOB_RUNNING and job['state'] != database.JOB_RUNNING:
                    logging.info( "Job %d start RUNNING", jobid )
                    database.setJobRunning( jobid )

                if newstate == database.JOB_COMPLETED:
            #         userid = job['uid']
            #         slurmid = job['slurmid']
            #         # stageout
            #         outs = ["jor_"+str(slurmid)+".out", "jor_"+str(slurmid)+".err"]
            #         for fileoutname in outs:
            #             fileout = database.createFile( userid, fileoutname )
            #             database.addJobFile( jobid, fileout, database.FILEOUT )
            #             localfile = database.getFileFullName( fileout )
            #             (localdir, localbase) = os.path.split( localfile )
            #             remotedir = os.path.join( remotehome, localdir )
            #             remotefile = os.path.join( remotehome, localfile )
            #             os.system('scp "%s:%s" "%s"' % (remotehost, remotefile, localfile) )

                    logging.info( "Job %d COMPLETED", jobid )
                    database.setJobCompleted( jobid )

                    #username = database.getUserName( job['uid'] )
                    #sendJobCompletedEmail( job['jid'], username )

    except KeyboardInterrupt:
        logging.info( "Ending pipeline loop" )

#-------------------------------------------------------------------------------
