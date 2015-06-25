# ------------------------------------------------------------------------------
import logging
import datetime
import sqlite3
import os
import data
import config

# ------------------------------------------------------------------------------
database = config.DB_DATABASE

# JOB STATE
JOB_CREATED = 0    # Just Created
JOB_SUBMITTED = 1  # Submitted
JOB_RUNNING = 2    # Running
JOB_COMPLETED = 3  # Completed
JOB_CANCELED = 4   # Canceled
JOB_FAILED = 5     # job failed

# JOB FILE TYPE
FILEIN = 0
FILEOUT = 1


# ------------------------------------------------------------------------------
def mkEmptyDatabase(dbname):
    if os.path.isfile(dbname):
        os.remove(dbname)

    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    c.execute("CREATE TABLE user ( "
              "uid INTEGER PRIMARY KEY AUTOINCREMENT, "
              "name text, UNIQUE(name))")

    c.execute("CREATE TABLE file ( "
              "fid INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, "
              "global INTEGER, filename text, filetype INTEGER)")
    conn.commit()

    c.execute("CREATE TABLE job ( "
              "jid INTEGER PRIMARY KEY AUTOINCREMENT, juid INTEGER NOT NULL, "
              "uid INTEGER NOT NULL, state INTEGER, "
              "name text NOT NULL DEFAULT 'unnamed', "
              "created TEXT NOT NULL DEFAULT '2014-03-01 08:00:00.000000', "
              "updated TEXT NOT NULL DEFAULT '2014-03-01 08:00:00.000000', "
              "FOREIGN KEY(uid) REFERENCES user(uid))")
    conn.commit()

    c.execute("CREATE TABLE jobfile ( "
              "jid INTEGER, fid INTEGER, jobfiletype INTEGER, "
              "PRIMARY KEY(jid, fid))")
    conn.commit()

    conn.close()


# ------------------------------------------------------------------------------
def dropJobTables():
    conn = sqlite3.connect(database)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS jobfile")
    conn.commit()
    c.execute("DROP TABLE IF EXISTS job")
    conn.commit()

    c.execute("CREATE TABLE job ( "
              "jid INTEGER PRIMARY KEY AUTOINCREMENT, juid INTEGER NOT NULL, "
              "uid INTEGER NOT NULL, state INTEGER, "
              "name text NOT NULL DEFAULT 'unnamed', "
              "created TEXT NOT NULL DEFAULT '2014-03-01 08:00:00.000000', "
              "updated TEXT NOT NULL DEFAULT '2014-03-01 08:00:00.000000', "
              "FOREIGN KEY(uid) REFERENCES user(uid))")
    conn.commit()

    c.execute("CREATE TABLE jobfile ( "
              "jid INTEGER, fid INTEGER, jobfiletype INTEGER, "
              "PRIMARY KEY(jid, fid))")
    conn.commit()

    conn.close()


# ------------------------------------------------------------------------------
def init():
    if config.DB_RESET:
        if not os.path.isfile(database):
            mkEmptyDatabase(database)


# ------------------------------------------------------------------------------
def fixdbUserTable():
    conn = sqlite3.connect(database)
    c = conn.cursor()

    c.execute("ALTER TABLE user RENAME TO user0")

    c.execute("CREATE TABLE user ( "
              "uid INTEGER PRIMARY KEY AUTOINCREMENT, "
              "name text, UNIQUE(name))")

    c.execute("INSERT INTO user (uid,name) "
              "SELECT user0.uid,user0.name FROM user0")

    c.execute("DROP TABLE user0")

    conn.commit()

    conn.close()


# ------------------------------------------------------------------------------
def fixdbJobName():
    column_name = 'name'
    conn = sqlite3.connect(database)
    c = conn.cursor()
    # add new column if needed
    try:
        c.execute('SELECT %s FROM job' % (column_name,))
    except sqlite3.OperationalError:
        logging.info("Adding new Column %s", (column_name,))
        c.execute('ALTER TABLE job '
                  'ADD COLUMN %s TEXT NOT NULL DEFAULT "unnamed"' %
                  (column_name,))
        conn.commit()

    # fix all jobs
    c.execute('SELECT jid,juid FROM job')
    jdata = c.fetchall()
    for j in jdata:
        jobname = "job " + str(j[1])
        logging.info("Set job name %d = '%s'", j[0], jobname)
        c.execute('UPDATE job SET %s=? WHERE jid=?' % (column_name,),
                  (jobname, j[0],))
    conn.commit()

    conn.close()


# ------------------------------------------------------------------------------
def fixdbDeleteSlurm():
    conn = sqlite3.connect(database)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS jobslurm")
    conn.commit()

    conn.close()


# ------------------------------------------------------------------------------
def checkIfUserExists(name):
    conn = sqlite3.connect(database)
    try:
        with conn:
            c = conn.cursor()
            c.execute('SELECT * FROM user WHERE name=?', (name,))
            val = c.fetchone()
            if val is not None:
                return True
    except:
        return False

    return False


# ------------------------------------------------------------------------------
def insertNewUser(name):
    if not checkIfUserExists(name):
        conn = sqlite3.connect(database)
        try:
            with conn:
                conn.execute('INSERT INTO user(uid,name) VALUES (null,?)',
                             (name,))
        except sqlite3.IntegrityError:
            logging.error("User '%s' Already Exists", name)
            return

        logging.warning("Inserting new user '%s'", name)

        insertDemoData(name)


# ------------------------------------------------------------------------------
def insertDemoData(name):
    for demo_f in config.DEMO_INFILES:

        # Now only work for fastq files (f_type is set to 1)
        insertFileWithType(name, demo_f, 1)
        data.linkDemoFile(name, demo_f)


# ------------------------------------------------------------------------------
def deleteUser(name):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid FROM user WHERE name=?', (name,))
    uidrow = c.fetchone()
    if uidrow is not None:
        uid = uidrow[0]
        logging.info("Deleting user %s %d", name, uid)

        c.execute('SELECT jid FROM job WHERE uid=?', (uid,))
        dbjobs = c.fetchall()
        for jobrow in dbjobs:
            jid = jobrow[0]
            logging.info("Deleting user job %d", jid)
            c.execute('DELETE FROM jobfile WHERE jid=?', (jid,))
            c.execute('DELETE FROM job WHERE jid=?', (jid,))
        conn.commit()
        c.execute('SELECT fid FROM file WHERE uid=?', (uid,))
        dbfiles = c.fetchall()
        for filerow in dbfiles:
            fid = filerow[0]
            logging.info("Deleting user file %d", fid)
            c.execute('DELETE FROM file WHERE fid=?', (fid,))
        conn.commit()
        c.execute('DELETE FROM user WHERE uid=?', (uid,))
        conn.commit()
    else:
        logging.error("Unknown user %s", name)

    conn.close()


# ------------------------------------------------------------------------------
def insertFile(user, filename):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid FROM user WHERE name=?', (user,))
    uid = c.fetchone()
    if uid is not None:
        c.execute('SELECT fid FROM file WHERE uid=? AND filename=?',
                  (uid[0], filename))
        exists = c.fetchone()
        if exists is None:
            c.execute('INSERT INTO file(fid,uid,global,filename,filetype) '
                      'VALUES (null,?,?,?,?)', (uid[0], 0, filename, 0))
            conn.commit()
            conn.close()
    else:
        conn.close()
        raise RuntimeError("insertFile with invalid user " + user)


# ------------------------------------------------------------------------------
def insertFileWithType(user, filename, filetype):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid FROM user WHERE name=?', (user,))
    uid = c.fetchone()
    if uid is not None:
        c.execute('SELECT fid FROM file WHERE uid=? AND filename=?',
                  (uid[0], filename))
        exists = c.fetchone()
        if exists is None:
            c.execute('INSERT INTO file(fid,uid,global,filename,filetype) '
                      'VALUES (null,?,?,?,?)',
                      (uid[0], 0, filename, filetype))
            conn.commit()
            conn.close()
    else:
        conn.close()
        raise RuntimeError("insertFileWithType with invalid user " + user)


# ------------------------------------------------------------------------------
def createFile(userid, filename):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('INSERT INTO file(fid,uid,global,filename,filetype) '
              'VALUES (null,?,?,?,?)', (userid, 0, filename, 0))
    c.execute('SELECT last_insert_rowid() FROM file')
    fileid = c.fetchone()[0]
    conn.commit()
    conn.close()
    return fileid


# ------------------------------------------------------------------------------
def createFileWithType(userid, filename, filetype):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('INSERT INTO file(fid,uid,global,filename,filetype) '
              'VALUES (null,?,?,?,?)', (userid, 0, filename, filetype))
    c.execute('SELECT last_insert_rowid() FROM file')
    fileid = c.fetchone()[0]
    conn.commit()
    conn.close()
    return fileid


# ------------------------------------------------------------------------------
def getUserFiles(user):
    files = []
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid FROM user WHERE name=?', (user,))
    uid = c.fetchone()
    if uid is not None:
        c.execute('SELECT fid,filename FROM file WHERE uid=? OR global=1',
                  (uid[0],))
        dbfiles = c.fetchall()
        for f in dbfiles:
            files.append({'id': f[0], 'file': f[1]})

    conn.close()

    return files


# ------------------------------------------------------------------------------
def getUserFilesWithType(user, filetype):
    files = []
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid FROM user WHERE name=?', (user,))
    uid = c.fetchone()
    if uid is not None:
        c.execute('SELECT fid,filename FROM file '
                  'WHERE (uid=? OR global=1) AND filetype=?',
                  (uid[0], filetype))
        dbfiles = c.fetchall()
        for f in dbfiles:
            files.append({'id': f[0], 'file': f[1]})

    conn.close()

    return files


# ------------------------------------------------------------------------------
def getFileFullName(fid):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid,filename FROM file WHERE fid=?', (fid,))
    fdata = c.fetchone()
    if fdata is None:
        conn.close()
        raise RuntimeError("getFileFullName with invalid id " + str(fid))

    c.execute('SELECT name FROM user WHERE uid=?', (fdata[0],))
    udata = c.fetchone()
    if udata is None:
        conn.close()
        raise RuntimeError("getFileFullName invalid user " + str(fdata[0]))

    conn.close()

    return data.getUserFilename(udata[0], fdata[1])


# ------------------------------------------------------------------------------
def isFileAllowedFromUser(fileid, user):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid FROM user WHERE name=?', (user,))
    udata = c.fetchone()
    if udata is None:
        conn.close()
        return False

    c.execute('SELECT uid,global FROM file WHERE fid=?', (fileid,))
    fdata = c.fetchone()
    if fdata is None:
        conn.close()
        return False

    conn.close()

    return fdata[1] != 0 or fdata[0] == udata[0]


# ------------------------------------------------------------------------------
def insertNewJob(user, jobid):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid FROM user WHERE name=?', (user,))
    uid = c.fetchone()
    if uid is not None:
        newjuid = 1
        c.execute('SELECT max(juid) FROM job WHERE uid=?', (uid[0],))
        lastjuid = c.fetchone()[0]
        if lastjuid is not None:
            newjuid = lastjuid + 1

        now = datetime.datetime.now()
        jobname = 'job ' + str(newjuid)
        try:
            c.execute(
                'INSERT INTO job(jid,juid,uid,name,state,created,updated) '
                'VALUES (?,?,?,?,?,?,?)',
                (jobid, newjuid, uid[0], jobname, JOB_SUBMITTED, now, now))
            conn.commit()
        except sqlite3.IntegrityError:
            logging.error("Jobid '%d' Already Exists", jobid)
            conn.close()
            return False

        conn.close()
    else:
        conn.close()
        raise RuntimeError("createJob with invalid user " + user)

    return True


# ------------------------------------------------------------------------------
def getUserJobs(user):
    jobs = []
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid FROM user WHERE name=?', (user,))
    uid = c.fetchone()
    if uid is not None:
        c.execute('SELECT jid,juid,name FROM job WHERE uid=?', (uid[0],))
        dbjobs = c.fetchall()
        for j in dbjobs:
            jobs.append({'jid': j[0], 'juid': j[1], 'name': j[2]})

    conn.close()

    return jobs


# ------------------------------------------------------------------------------
def addJobFile(jobid, fileid, jftype):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('INSERT INTO jobfile(jid,fid,jobfiletype) VALUES (?,?,?)',
              (jobid, fileid, jftype))
    conn.commit()
    conn.close()


# ------------------------------------------------------------------------------
def setJobState(jobid, newstate):
    now = datetime.datetime.now()
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('UPDATE job SET state=?,updated=? WHERE jid=?',
              (newstate, now, jobid,))
    conn.commit()
    conn.close()


# ------------------------------------------------------------------------------
def setJobSubmitted(jobid):
    setJobState(jobid, JOB_SUBMITTED)


# ------------------------------------------------------------------------------
def setJobRunning(jobid):
    setJobState(jobid, JOB_RUNNING)


# ------------------------------------------------------------------------------
def setJobCompleted(jobid):
    setJobState(jobid, JOB_COMPLETED)


# ------------------------------------------------------------------------------
def setJobCanceled(jobid):
    setJobState(jobid, JOB_CANCELED)


# ------------------------------------------------------------------------------
def setJobFailed(jobid):
    setJobState(jobid, JOB_FAILED)


# ------------------------------------------------------------------------------
def deleteJob(jobid):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    logging.info("Deleting job %d", jobid)
    c.execute('DELETE FROM jobfile WHERE jid=?', (jobid,))
    c.execute('DELETE FROM job WHERE jid=?', (jobid,))
    conn.commit()


# ------------------------------------------------------------------------------
def changeJobName(jobid, newname):
    conn = sqlite3.connect(database)
    with conn:
        conn.execute('UPDATE job SET name=? WHERE jid=?',
                     (newname, jobid))


# ------------------------------------------------------------------------------
def getJobInfo(jobid):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT state,juid,name,created,updated FROM job WHERE jid=?',
              (jobid,))
    jdata = c.fetchone()
    if jdata is None:
        conn.close()
        raise RuntimeError("getJobInfo with invalid id " + str(jobid))

    c.execute('SELECT fid,jobfiletype FROM jobfile WHERE jid=?', (jobid,))
    jfiles = c.fetchall()

    files = []
    for jf in jfiles:
        c.execute('SELECT filename FROM file WHERE fid=?', (jf[0],))
        fdata = c.fetchone()
        if fdata is None:
            conn.close()
            raise RuntimeError("getJobInfo with invalid file " + str(jf[0]))

        files.append({'fid': jf[0], 'name': fdata[0], 'type': jf[1]})

    conn.close()

    return {'jid': jobid, 'juid': jdata[1], 'name': jdata[2],
            'state': jdata[0], 'created': jdata[3],
            'updated': jdata[4], 'files': files}


# ------------------------------------------------------------------------------
def getJustCreatedJobs():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT jid,juid,uid,state FROM job WHERE state=0')
    jdata = c.fetchall()
    jobs = []
    for j in jdata:
        jobs.append({'jid': j[0], 'juid': j[1], 'uid': j[2], 'state': j[3]})

    return jobs


# ------------------------------------------------------------------------------
def getActiveJobs():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT jid,juid,uid,state FROM job WHERE state=1 OR state=2')
    jdata = c.fetchall()
    jobs = []
    for j in jdata:
        jobs.append({'jid': j[0], 'juid': j[1], 'uid': j[2], 'state': j[3]})

    conn.close()

    return jobs


# ------------------------------------------------------------------------------
def isJobFromUser(jobid, user):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT uid FROM user WHERE name=?', (user,))
    udata = c.fetchone()
    if udata is None:
        conn.close()
        return False

    c.execute('SELECT uid FROM job WHERE jid=?', (jobid,))
    jdata = c.fetchone()
    if jdata is None:
        conn.close()
        return False

    conn.close()

    return jdata[0] == udata[0]


# ------------------------------------------------------------------------------
