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

reSLURMLINE = re.compile(r"slurmids: (?P<slurmids>\d+(,\d+)*)")
reSLURMID = re.compile(r"\,")

#-------------------------------------------------------------------------------
def startJob( user, var1 ):
    jobid = database.createJob( user )

    p = multiprocessing.Process( target=runjob, args=(user, jobid, var1) )
    p.start()

#-------------------------------------------------------------------------------
def getSlurmIds( output ):
    mm = reSLURMLINE.search( output )
    sids = []
    if mm:
        slurmline = mm.group('slurmids')
        slurmids = reSLURMID.split( slurmline )
        sids = map(int,slurmids)

    return sids

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
    slurmids = getSlurmIds( ouput )

    if len(slurmids) > 0:
        database.setJobSubmitted( jobid )
    else:
        print "WARNING : task without slurm ids"

    for si in slurmids:
        database.addJobSlurmRef( jobid, slurmid )

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
def pipelineLoop():
    try:
        print "start pipeline loop"
        while (1 == 1):
            time.sleep( 60 )
            # check
            zjobs = database.getJustCreatedJobs()
            if len(zjobs) > 0:
                zjobids = map( lambda js: js['jid'], zjobs )
                print "Warning: " + str(len(zjobs)) + " zombie jobs : " + str(zjobids)

            jobs = database.getActiveJobs()
            if len(jobs) > 0:
                print "Checking " + str(len(jobs)) + " job/s"

            for job in jobs:
                jobid = job['jid']
                newstate = checkSlurmJob( job['slurmids'] )
                if newstate == database.JOB_RUNNING and job['state'] != database.JOB_RUNNING:
                    print "Job " + str(jobid) + " start RUNNING"
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

                    print "Job " + str(jobid) + " COMPLETED"
                    database.setJobCompleted( jobid )

    except KeyboardInterrupt:
        print "ending pipeline loop"

#-------------------------------------------------------------------------------
