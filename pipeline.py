#-------------------------------------------------------------------------------
import multiprocessing
import os
from os import path
import subprocess
import re
import time
import config
import database

#-------------------------------------------------------------------------------
remotehost = config.REMOTEHOST
remotehome = config.REMOTEHOME
pipe_launch = config.PIPE_LAUNCH

reJOBID = re.compile(r"Submitted batch job (?P<slurmid>\d+)")

#-------------------------------------------------------------------------------
def startJob( user, var1 ):
    jobid = database.createJob( user )

    p = multiprocessing.Process( target=runjob, args=(user, jobid, var1) )
    p.start()

#-------------------------------------------------------------------------------
def runjob( user, jobid, var1):
    print "RUNNING JOB " + str(jobid)

# stagein
    if var1.file:
        fileid1 = int(var1.file)
        localfile1 = database.getFileFullName( fileid1 )
        remotefile1 = os.path.join( remotehome, localfile1 )
        database.addJobFile( jobid, fileid1, database.FILEIN )
        var1['filename1'] = remotefile1

    if var1.file2:
        fileid2 = int(var1.file2)
        localfile2 = database.getFileFullName( fileid2 )
        remotefile2 = os.path.join( remotehome, localfile2 )
        database.addJobFile( jobid, fileid2, database.FILEIN )
        var1['filename2'] = remotefile2
        
    if not var1.file2:
        # submit
        command = [ pipe_launch, user, str(var1), remotefile1, str(jobid) ]
    if var1.file and var1.file2:
        command = [ pipe_launch, user, str(var1), remotefile1, remotefile2, str(jobid) ]
    print command

    for k in var1:
        print k + " : " + var1[k]

    proc = subprocess.Popen( command, stdout=subprocess.PIPE )
    output = proc.communicate()[0]
    mm = reJOBID.search( output )
    if mm:
        slurmid = int(mm.group('slurmid'))
        print "Slurm ID", str(slurmid)
        database.setJobSubmitted( jobid )
        database.addJobSlurmRef( jobid, slurmid )
    else:
        raise (-1)


#-------------------------------------------------------------------------------
def run():
    p = multiprocessing.Process( target=pipelineLoop )
    p.start()
    return p

#-------------------------------------------------------------------------------
def checkSlurmJob( slurmid ):
    command = ["ssh", remotehost, "mnq", "--job", str(slurmid) ]
    proc = subprocess.Popen( command, stdout=subprocess.PIPE )
    output = proc.communicate()[0]

    if len(output.splitlines()) <= 1:
        return database.JOB_COMPLETED

    mm = re.search( "RUNNING", output )
    if mm is not None:
        return database.JOB_RUNNING

    return database.JOB_SUBMITTED

#-------------------------------------------------------------------------------
def pipelineLoop():
    try:
        while (1 == 1):
            time.sleep( 100 )
            jobs = database.getActiveJobs()
            if len(jobs) > 0:
                print "Checking " + str(len(jobs)) + " job/s"

            for job in jobs:
                jobid = job['jid']
                newstate = checkSlurmJob( job['slurmid'] )
                if newstate == database.JOB_RUNNING and job['state'] != database.JOB_RUNNING:
                    database.setJobRunning( jobid )

                if newstate == database.JOB_COMPLETED:
                    userid = job['uid']
                    slurmid = job['slurmid']
                    # stageout
                    outs = ["jor_"+str(slurmid)+".out", "jor_"+str(slurmid)+".err"]
                    for fileoutname in outs:
                        fileout = database.createFile( userid, fileoutname )
                        database.addJobFile( jobid, fileout, database.FILEOUT )
                        localfile = database.getFileFullName( fileout )
                        (localdir, localbase) = os.path.split( localfile )
                        remotedir = os.path.join( remotehome, localdir )
                        remotefile = os.path.join( remotehome, localfile )
                        os.system('scp "%s:%s" "%s"' % (remotehost, remotefile, localfile) )

                    database.setJobCompleted( jobid )

    except KeyboardInterrupt:
        print "ending pipeline loop"

#-------------------------------------------------------------------------------
