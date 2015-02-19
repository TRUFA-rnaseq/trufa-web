#-------------------------------------------------------------------------------
import logging
import datetime
import sqlite3
import bcrypt
import os
import data
import htpasswd
import re
from email.utils import parseaddr
import config

#-------------------------------------------------------------------------------
BCRYPT_ROUNDS = 5
database = config.DB_DATABASE
passwdfile = config.DB_PASSFILE

# JOB STATE
JOB_CREATED = 0   # Just Created
JOB_SUBMITTED = 1 # Submitted
JOB_RUNNING = 2   # Running
JOB_COMPLETED = 3 # Completed
JOB_CANCELED = 4 # Canceled

# JOB FILE TYPE
FILEIN = 0
FILEOUT = 1

EMAIL_REGEX = re.compile(r"[^@ ]+@[^@ ]+\.[^@ ]+")

#-------------------------------------------------------------------------------
def mkEmptyDatabase( dbname ):
    if os.path.isfile( dbname ):
        os.remove( dbname )

    conn = sqlite3.connect( dbname )
    c = conn.cursor()
    c.execute( "CREATE TABLE user (uid INTEGER PRIMARY KEY AUTOINCREMENT, name text, passwd text, email text, enabled INTEGER NOT NULL DEFAULT 1, UNIQUE(name), UNIQUE(email))" )

    c.execute( "CREATE TABLE file (fid INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, global INTEGER, filename text, filetype INTEGER)" )
    conn.commit()

    c.execute( "CREATE TABLE job (jid INTEGER PRIMARY KEY AUTOINCREMENT, juid INTEGER NOT NULL, uid INTEGER NOT NULL, state INTEGER, name text NOT NULL DEFAULT 'unnamed', created TEXT NOT NULL DEFAULT '2014-03-01 08:00:00.000000', updated TEXT NOT NULL DEFAULT '2014-03-01 08:00:00.000000', FOREIGN KEY(uid) REFERENCES user(uid) )" )
    conn.commit()

    c.execute( "CREATE TABLE jobslurm (jid INTEGER, slurmid INTEGER, PRIMARY KEY(jid, slurmid), FOREIGN KEY(jid) REFERENCES job(jid) )" )
    conn.commit()

    c.execute( "CREATE TABLE jobfile (jid INTEGER, fid INTEGER, jobfiletype INTEGER, PRIMARY KEY(jid, fid) )" )
    conn.commit()

    conn.close()

#-------------------------------------------------------------------------------
def dropJobTables():
    conn = sqlite3.connect( database )
    c = conn.cursor()

    c.execute( "DROP TABLE IF EXISTS jobfile" )
    conn.commit()
    c.execute( "DROP TABLE IF EXISTS jobslurm" )
    conn.commit()
    c.execute( "DROP TABLE IF EXISTS job" )
    conn.commit()

    c.execute( "CREATE TABLE job (jid INTEGER PRIMARY KEY AUTOINCREMENT, juid INTEGER NOT NULL, uid INTEGER NOT NULL, state INTEGER, name text NOT NULL DEFAULT 'unnamed', created TEXT NOT NULL DEFAULT '2014-03-01 08:00:00.000000', updated TEXT NOT NULL DEFAULT '2014-03-01 08:00:00.000000', FOREIGN KEY(uid) REFERENCES user(uid) )" )
    conn.commit()

    c.execute( "CREATE TABLE jobslurm (jid INTEGER, slurmid INTEGER, PRIMARY KEY(jid, slurmid), FOREIGN KEY(jid) REFERENCES job(jid) )" )
    conn.commit()

    c.execute( "CREATE TABLE jobfile (jid INTEGER, fid INTEGER, jobfiletype INTEGER, PRIMARY KEY(jid, fid) )" )
    conn.commit()

    conn.close()

#-------------------------------------------------------------------------------
def init():
    if config.DB_RESET:
        if not os.path.isfile( database ):
            mkEmptyDatabase( database )

        # create empty password file
        if not os.path.isfile( passwdfile ):
            open( passwdfile, 'w' ).close()

        insertUser( config.DB_TEST_USER, config.DB_TEST_PASS, config.DB_TEST_EMAIL )

#-------------------------------------------------------------------------------
def fixdbJobName():
    column_name = 'name'
    conn = sqlite3.connect( database )
    c = conn.cursor()
    # add new column if needed
    try:
        c.execute( 'SELECT %s FROM job' % (column_name,))
    except sqlite3.OperationalError, e:
        logging.info( "Adding new Column %", column_name )
        c.execute( 'ALTER TABLE job ADD COLUMN %s TEXT NOT NULL DEFAULT "unnamed"' % (column_name,))
        conn.commit()

    # fix all jobs
    c.execute( 'SELECT jid,juid FROM job' )
    jdata = c.fetchall()
    for j in jdata:
        jobname = "job " + str(j[1])
        logging.info( "Set job name %d = '%s'", j[0], jobname )
        c.execute( 'UPDATE job SET %s=? WHERE jid=?' % (column_name,),
                   (jobname, j[0],) )
    conn.commit()

    conn.close()

#-------------------------------------------------------------------------------
def insertUser( name, passwd, email ):
    checkedName, checkedEmail = parseaddr( email )
    if len( checkedEmail ) == 0 or not EMAIL_REGEX.match( checkedEmail):
        logging.error( "Invalid email %s", email )
        return

    h = bcrypt.hashpw( passwd, bcrypt.gensalt(BCRYPT_ROUNDS) )

    conn = sqlite3.connect( database )
    try:
        with conn:
            conn.execute( 'INSERT INTO user(uid,name,passwd,email) VALUES (null,?,?,?)',
                          (name,h,checkedEmail) )
    except sqlite3.IntegrityError:
        logging.error( "User '%s' Already Exists", name )
        return

    try:
        with htpasswd.Basic( passwdfile ) as userdb:
            userdb.add( name, passwd )
    except htpasswd.basic.UserExists, e:
        logging.error( "User '%s' Already Exists [%s]", name, str(e) )

    insertDemoData( name )
        
#-------------------------------------------------------------------------------
def insertDemoData( name ):
    for demo_f in config.DEMO_INFILES:

        # Now only work for fastq files (f_type is set to 1)
        insertFileWithType(name, demo_f, 1)
        data.linkDemoFile(name, demo_f)

#-------------------------------------------------------------------------------
def getUserEmail( uid ):
    conn = sqlite3.connect( database )
    try:
        with conn:
            c = conn.cursor()
            c.execute( 'SELECT email FROM user WHERE uid=?', (uid,) )
            val = c.fetchone()
            return val[0]
    except:
        logging.error("Unable to get user with uid:'%s' email", uid )
        
#-------------------------------------------------------------------------------
def changeUserPassword( name, newpass ):
    try:
        with htpasswd.Basic( passwdfile ) as userdb:
            userdb.change_password( name, newpass )
    except htpasswd.basic.UserNotExists, e:
        logging.error( "User Not Exists %s [%s]", name, str(e) )
        return False

    h = bcrypt.hashpw( newpass, bcrypt.gensalt(BCRYPT_ROUNDS) )

    conn = sqlite3.connect( database )
    try:
        with conn:
            conn.execute( 'UPDATE user SET passwd=? WHERE name=?', (h,name) )
    except:
        logging.error( "changing password %s", name )
        return False

    return True

#-------------------------------------------------------------------------------
def checkUser( name, passwd ):
    conn = sqlite3.connect( database )
    try:
        with conn:
            c = conn.cursor()
            c.execute( 'SELECT passwd FROM user WHERE name=? AND enabled=1', (name,) )
            val = c.fetchone()
            if val is not None:
                return bcrypt.hashpw( passwd, val[0] ) == val[0]
    except:
        return False

    return False

#-------------------------------------------------------------------------------
def checkIfUserAvailable( name ):
    conn = sqlite3.connect( database )
    try:
        with conn:
            c = conn.cursor()
            c.execute( 'SELECT * FROM user WHERE name=?', (name,) )
            val = c.fetchone()
            if val is None:
                return True
    except:
        return False

    return False

#-------------------------------------------------------------------------------
def enableUser( name ):
    conn = sqlite3.connect( database )
    with conn:
        c = conn.cursor()
        c.execute( 'SELECT uid FROM user WHERE name=?', (name,) )
        uidrow = c.fetchone()
        if uidrow is not None:
            c.execute( 'UPDATE user SET enabled=1 WHERE uid=?', (uidrow[0],) )

#-------------------------------------------------------------------------------
def disableUser( name ):
    conn = sqlite3.connect( database )
    with conn:
        c = conn.cursor()
        c.execute( 'SELECT uid FROM user WHERE name=?', (name,) )
        uidrow = c.fetchone()
        if uidrow is not None:
            c.execute( 'UPDATE user SET enabled=0 WHERE uid=?', (uidrow[0],) )

#-------------------------------------------------------------------------------
def deleteUser( name ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid FROM user WHERE name=?', (name,) )
    uidrow = c.fetchone()
    if uidrow is not None:
        uid = uidrow[0]
        logging.info( "Deleting user %s %d", name, uid )

        c.execute( 'SELECT jid FROM job WHERE uid=?', (uid,) )
        dbjobs = c.fetchall()
        for jobrow in dbjobs:
            jid = jobrow[0]
            logging.info( "Deleting user job %d", jid )
            c.execute( 'DELETE FROM jobslurm WHERE jid=?', (jid,) )
            c.execute( 'DELETE FROM jobfile WHERE jid=?', (jid,) )
            c.execute( 'DELETE FROM job WHERE jid=?', (jid,) )
        conn.commit()
        c.execute( 'SELECT fid FROM file WHERE uid=?', (uid,) )
        dbfiles = c.fetchall()
        for filerow in dbfiles:
            fid = filerow[0]
            logging.info( "Deleting user file %d", fid )
            c.execute( 'DELETE FROM file WHERE fid=?', (fid,) )
        conn.commit()
        c.execute( 'DELETE FROM user WHERE uid=?', (uid,) )
        conn.commit()
    else:
        logging.error( "Unknown user %s", name )

    conn.close()

    try:
        with htpasswd.Basic( passwdfile ) as userdb:
            userdb.pop( name )
    except htpasswd.basic.UserNotExists, e:
        logging.error( "User Not Exists %s [%s]", name, str(e) )

#-------------------------------------------------------------------------------
def insertFile( user, filename ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid FROM user WHERE name=?', (user,) )
    uid = c.fetchone()
    if uid is not None:
        c.execute( 'SELECT fid FROM file WHERE uid=? AND filename=?', (uid[0],filename) )
        exists = c.fetchone()
        if exists is None:
            c.execute( 'INSERT INTO file(fid,uid,global,filename,filetype) VALUES (null,?,?,?,?)',
                       (uid[0],0,filename,0) )
            conn.commit()
            conn.close()
    else:
        conn.close()
        raise RuntimeError( "insertFile with invalid user " + user )

#-------------------------------------------------------------------------------
def insertFileWithType( user, filename, filetype ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid FROM user WHERE name=?', (user,) )
    uid = c.fetchone()
    if uid is not None:
        c.execute( 'SELECT fid FROM file WHERE uid=? AND filename=?', (uid[0],filename) )
        exists = c.fetchone()
        if exists is None:
            c.execute( 'INSERT INTO file(fid,uid,global,filename,filetype) VALUES (null,?,?,?,?)',
                       (uid[0],0,filename,filetype) )
            conn.commit()
            conn.close()
    else:
        conn.close()
        raise RuntimeError( "insertFileWithType with invalid user " + user )

#-------------------------------------------------------------------------------
def createFile( userid, filename ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'INSERT INTO file(fid,uid,global,filename,filetype) VALUES (null,?,?,?,?)',
               (userid,0,filename,0) )
    c.execute( 'SELECT last_insert_rowid() FROM file' )
    fileid = c.fetchone()[0]
    conn.commit()
    conn.close()
    return fileid

#-------------------------------------------------------------------------------
def createFileWithType( userid, filename, filetype ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'INSERT INTO file(fid,uid,global,filename,filetype) VALUES (null,?,?,?,?)',
               (userid,0,filename,filetype) )
    c.execute( 'SELECT last_insert_rowid() FROM file' )
    fileid = c.fetchone()[0]
    conn.commit()
    conn.close()
    return fileid

#-------------------------------------------------------------------------------
def getUserFiles( user ):
    files = []
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid FROM user WHERE name=?', (user,) )
    uid = c.fetchone()
    if uid is not None:
        c.execute( 'SELECT fid,filename FROM file WHERE uid=? OR global=1', (uid[0],) )
        dbfiles = c.fetchall()
        for f in dbfiles:
            files.append( {'id': f[0], 'file': f[1]} )

    conn.close()

    return files

#-------------------------------------------------------------------------------
def getUserFilesWithType( user, filetype ):
    files = []
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid FROM user WHERE name=?', (user,) )
    uid = c.fetchone()
    if uid is not None:
        c.execute( 'SELECT fid,filename FROM file WHERE (uid=? OR global=1) AND filetype=?', (uid[0],filetype) )
        dbfiles = c.fetchall()
        for f in dbfiles:
            files.append( {'id': f[0], 'file': f[1]} )

    conn.close()

    return files

#-------------------------------------------------------------------------------
def getFileFullName( fid ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid,filename FROM file WHERE fid=?', (fid,) )
    fdata = c.fetchone()
    if fdata is None:
        conn.close()
        raise RuntimeError( "getFileFullName with invalid id " + str(fid) )

    c.execute('SELECT name FROM user WHERE uid=?', (fdata[0],) )
    udata = c.fetchone()
    if udata is None:
        conn.close()
        raise RuntimeError( "getFileFullName with invalid user " + str(fdata[0]) )

    conn.close()

    return data.getUserFilename( udata[0], fdata[1] )

#-------------------------------------------------------------------------------
def isFileAllowedFromUser( fileid, user ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid FROM user WHERE name=?', (user,) )
    udata = c.fetchone()
    if udata is None:
        conn.close()
        return False

    c.execute( 'SELECT uid,global FROM file WHERE fid=?', (fileid,) )
    fdata = c.fetchone()
    if fdata is None:
        conn.close()
        return False

    conn.close()

    return fdata[1] != 0 or fdata[0] == udata[0]

#-------------------------------------------------------------------------------
def createJob( user ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid FROM user WHERE name=?', (user,) )
    uid = c.fetchone()
    if uid is not None:
        newjuid = 1
        c.execute( 'SELECT max(juid) FROM job WHERE uid=?', (uid[0],) )
        lastjuid = c.fetchone()[0]
        if lastjuid is not None:
            newjuid = lastjuid + 1

        now = datetime.datetime.now()

        jobname = 'job ' + str(newjuid)
        c.execute( 'INSERT INTO job(jid,juid,uid,name,state,created,updated) VALUES (null,?,?,?,0,?,?)',
                   (newjuid,uid[0],jobname,now,now) )
        c.execute( 'SELECT last_insert_rowid() FROM job' )
        jobid = c.fetchone()[0]
        conn.commit()
        conn.close()
        return jobid
    else:
        conn.close()
        raise RuntimeError( "createJob with invalid user " + user )

#-------------------------------------------------------------------------------
def getUserJobs( user ):
    jobs = []
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid FROM user WHERE name=?', (user,) )
    uid = c.fetchone()
    if uid is not None:
        c.execute( 'SELECT jid,juid,name FROM job WHERE uid=?', (uid[0],) )
        dbjobs = c.fetchall()
        for j in dbjobs:
            jobs.append( {'id': j[0],'juid': j[1], 'name': j[2]} )

    conn.close()

    return jobs

#-------------------------------------------------------------------------------
def addJobFile( jobid, fileid, jftype ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'INSERT INTO jobfile(jid,fid,jobfiletype) VALUES (?,?,?)',
               (jobid,fileid,jftype) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def addJobSlurmRef( jobid, slurmid ):
    conn = sqlite3.connect( database )
    try:
        with conn:
            conn.execute( 'INSERT INTO jobslurm(jid,slurmid) VALUES (?,?)',
                          (jobid,slurmid) )
    except sqlite3.IntegrityError:
        logging.error( "Adding duplicate slurm id %d on job %d", slurmid, jobid )

    conn.close()

#-------------------------------------------------------------------------------
def setJobSubmitted( jobid ):
    now = datetime.datetime.now()
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'UPDATE job SET state=1,updated=? WHERE jid=?', (now,jobid,) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def setJobRunning( jobid ):
    now = datetime.datetime.now()
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'UPDATE job SET state=2,updated=? WHERE jid=?', (now,jobid,) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def setJobCompleted( jobid ):
    now = datetime.datetime.now()
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'UPDATE job SET state=3,updated=? WHERE jid=?', (now,jobid,) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def setJobCanceled( jobid ):
    now = datetime.datetime.now()
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'UPDATE job SET state=4,updated=? WHERE jid=?', (now,jobid,) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def deleteJob( jobid ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    logging.info( "Deleting job %d", jobid )
    c.execute( 'DELETE FROM jobslurm WHERE jid=?', (jobid,) )
    c.execute( 'DELETE FROM jobfile WHERE jid=?', (jobid,) )
    c.execute( 'DELETE FROM job WHERE jid=?', (jobid,) )
    conn.commit()

#-------------------------------------------------------------------------------
def changeJobName( jobid, newname ):
    conn = sqlite3.connect( database )
    with conn:
        conn.execute( 'UPDATE job SET name=? WHERE jid=?',
                      (newname,jobid) )

#-------------------------------------------------------------------------------
def getJobInfo( jobid ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT state,juid,name,created,updated FROM job WHERE jid=?',
               (jobid,) )
    jdata = c.fetchone()
    if jdata is None:
        conn.close()
        raise RuntimeError( "getJobInfo with invalid id " + str(jobid) )

    c.execute('SELECT fid,jobfiletype FROM jobfile WHERE jid=?', (jobid,) )
    jfiles = c.fetchall()

    files = []
    for jf in jfiles:
        c.execute('SELECT filename FROM file WHERE fid=?', (jf[0],) )
        fdata = c.fetchone()
        if fdata is None:
            conn.close()
            raise RuntimeError( "getJobInfo with invalid file " + str(jf[0]) )

        files.append( {'fid': jf[0], 'name': fdata[0], 'type': jf[1] } )

    c.execute('SELECT slurmid FROM jobslurm WHERE jid=?', (jobid,) )
    jslurms = c.fetchall()

    slurms = []
    for js in jslurms:
        slurms.append( {'slurmid': js[0] } )

    conn.close()

    return { 'jobid': jobid, 'juid': jdata[1], 'name': jdata[2], 'state': jdata[0],
             'created': jdata[3], 'updated': jdata[4],
             'slurmids': slurms, 'files': files }

#-------------------------------------------------------------------------------
def getJustCreatedJobs():
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT jid,juid,uid,state FROM job WHERE state=0' )
    jdata = c.fetchall()
    jobs = []
    for j in jdata:
        jobs.append( {'jid':j[0],'juid':j[1],'uid':j[2],'state':j[3]} )

    return jobs

#-------------------------------------------------------------------------------
def getActiveJobs():
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT jid,juid,uid,state FROM job WHERE state=1 OR state=2' )
    jdata = c.fetchall()
    jobs = []
    for j in jdata:
        c.execute('SELECT slurmid FROM jobslurm WHERE jid=?', (j[0],) )
        jslurms = c.fetchall()

        slurms = []
        for js in jslurms:
            slurms.append( js[0] )

        jobs.append( {'jid':j[0],'juid':j[1],'uid':j[2],'state':j[3],'slurmids':slurms} )

    conn.close()

    return jobs

#-------------------------------------------------------------------------------
def isJobFromUser( jobid, user ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT uid FROM user WHERE name=?', (user,) )
    udata = c.fetchone()
    if udata is None:
        conn.close()
        return False

    c.execute( 'SELECT uid FROM job WHERE jid=?', (jobid,) )
    jdata = c.fetchone()
    if jdata is None:
        conn.close()
        return False

    conn.close()

    return jdata[0] == udata[0]

#-------------------------------------------------------------------------------
