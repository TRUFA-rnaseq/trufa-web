#-------------------------------------------------------------------------------
import sqlite3
import bcrypt
import os
import shutil
import data
import htpasswd
import re
from email.utils import parseaddr
import config

#-------------------------------------------------------------------------------
BCRYPT_ROUNDS = 5
template = 'template.db'
database = config.DB_DATABASE
passwdfile = config.DB_PASSFILE

# JOB STATE
JOB_CREATED = 0   # Just Created
JOB_SUBMITTED = 1 # Submitted
JOB_RUNNING = 2   # Running
JOB_COMPLETED = 3 # Completed

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
    c.execute( "CREATE TABLE user (uid INTEGER PRIMARY KEY AUTOINCREMENT, name text, passwd text, email text, UNIQUE(name))" )

    c.execute( "CREATE TABLE file (fid INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, global INTEGER, filename text, filetype INTEGER)" )
    conn.commit()

    c.execute( "CREATE TABLE job (jid INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, state INTEGER)" )
    conn.commit()

    c.execute( "CREATE TABLE jobslurm (jid INTEGER, slurmid INTEGER, PRIMARY KEY(jid, slurmid), FOREIGN KEY(jid) REFERENCES job(jid) )" )
    conn.commit()

    c.execute( "CREATE TABLE jobfile (jid INTEGER, fid INTEGER, jobfiletype INTEGER, PRIMARY KEY(jid, fid) )" )
    conn.commit()

    conn.close()

#-------------------------------------------------------------------------------
def clearDB():
    mkEmptyDatabase( template )
    if os.path.isfile( database ):
        os.remove( database )

#-------------------------------------------------------------------------------
def init():
    if config.DB_RESET:
        if not os.path.isfile( template ):
            clearDB()

        if not os.path.isfile( database ):
            shutil.copy( template, database )

        # create empty password file
        if not os.path.isfile( passwdfile ):
            open( passwdfile, 'w' ).close()

        name = 'admin' # same name and passwd
        insertUser( name, name, "j.smith@example.com" )

#-------------------------------------------------------------------------------
def insertUser( name, passwd, email ):
    checkedName, checkedEmail = parseaddr( email )
    if len( checkedEmail ) == 0 or not EMAIL_REGEX.match( checkedEmail):
        print "ERROR: Invalid email ", email
        return

    h = bcrypt.hashpw( passwd, bcrypt.gensalt(BCRYPT_ROUNDS) )

    conn = sqlite3.connect( database )
    try:
        with conn:
            conn.execute( 'INSERT INTO user VALUES (null,?,?,?)', (name,h,checkedEmail) )
    except sqlite3.IntegrityError:
        print "ERROR: User Already Exists ", name
        return

    try:
        with htpasswd.Basic( passwdfile ) as userdb:
            userdb.add( name, passwd )
    except htpasswd.basic.UserExists, e:
        print "ERROR: User Already Exists ", name, e

#-------------------------------------------------------------------------------
def changeUserPassword( name, newpass ):
    try:
        with htpasswd.Basic( passwdfile ) as userdb:
            userdb.change_password( name, newpass )
    except htpasswd.basic.UserNotExists, e:
        print "ERROR: User Not Exists ", name, e
        return False

    h = bcrypt.hashpw( newpass, bcrypt.gensalt(BCRYPT_ROUNDS) )

    conn = sqlite3.connect( database )
    try:
        with conn:
            conn.execute( 'UPDATE user SET passwd=? WHERE name=?', (h,name) )
    except:
        print "ERROR: changing password ", name
        return False

    return True

#-------------------------------------------------------------------------------
def checkUser( name, passwd ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT passwd FROM user WHERE name=?', (name,) )
    val = c.fetchone()
    conn.close()
    if val is not None:
        return bcrypt.hashpw( passwd, val[0] ) == val[0]

    return False

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
            c.execute( 'INSERT INTO file VALUES (null,?,?,?,?)', (uid[0],0,filename,0) )
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
            c.execute( 'INSERT INTO file VALUES (null,?,?,?,?)', (uid[0],0,filename,filetype) )
            conn.commit()
            conn.close()
    else:
        conn.close()
        raise RuntimeError( "insertFileWithType with invalid user " + user )

#-------------------------------------------------------------------------------
def createFile( userid, filename ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'INSERT INTO file VALUES (null,?,?,?,?)', (userid,0,filename,0) )
    c.execute( 'SELECT last_insert_rowid() FROM file' )
    fileid = c.fetchone()[0]
    conn.commit()
    conn.close()
    return fileid

#-------------------------------------------------------------------------------
def createFileWithType( userid, filename, filetype ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'INSERT INTO file VALUES (null,?,?,?,?)', (userid,0,filename,filetype) )
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
        c.execute( 'INSERT INTO job VALUES (null,?,0)', (uid[0],) )
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
        c.execute( 'SELECT jid FROM job WHERE uid=?', (uid[0],) )
        dbjobs = c.fetchall()
        for j in dbjobs:
            jobs.append( {'id': j[0]} )

    conn.close()

    return jobs

#-------------------------------------------------------------------------------
def addJobFile( jobid, fileid, jftype ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'INSERT INTO jobfile VALUES (?,?,?)', (jobid,fileid,jftype) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def addJobSlurmRef( jobid, slurmid ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'INSERT INTO jobslurm VALUES (?,?)', (jobid,slurmid) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def setJobSubmitted( jobid ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'UPDATE job SET state=1 WHERE jid=?', (jobid,) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def setJobRunning( jobid ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'UPDATE job SET state=2 WHERE jid=?', (jobid,) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def setJobCompleted( jobid ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'UPDATE job SET state=3 WHERE jid=?', (jobid,) )
    conn.commit()
    conn.close()

#-------------------------------------------------------------------------------
def getJobInfo( jobid ):
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute('SELECT state FROM job WHERE jid=?', (jobid,) )
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

    return { 'jobid': jobid, 'state': jdata[0], 'slurmids': slurms, 'files': files }

#-------------------------------------------------------------------------------
def getJustCreatedJobs():
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT jid,uid,state FROM job WHERE state=0' )
    jdata = c.fetchall()
    jobs = []
    for j in jdata:
        jobs.append( {'jid':j[0],'uid':j[1],'state':j[2]} )

    return jobs

#-------------------------------------------------------------------------------
def getActiveJobs():
    conn = sqlite3.connect( database )
    c = conn.cursor()
    c.execute( 'SELECT jid,uid,state FROM job WHERE state=1 OR state=2' )
    jdata = c.fetchall()
    jobs = []
    for j in jdata:
        c.execute('SELECT slurmid FROM jobslurm WHERE jid=?', (j[0],) )
        jslurms = c.fetchall()

        slurms = []
        for js in jslurms:
            slurms.append( js[0] )

        jobs.append( {'jid':j[0],'uid':j[1],'state':j[2],'slurmids':slurms} )

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
