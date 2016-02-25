# ------------------------------------------------------------------------------
import sqlite3
import bcrypt
import os
import htpasswd
import re
from email.utils import parseaddr
from . import config

# ------------------------------------------------------------------------------
BCRYPT_ROUNDS = 5
DATABASE = config.DB_DATABASE
PASSWDFILE = config.DB_PASSFILE

EMAIL_REGEX = re.compile(r"[^@ ]+@[^@ ]+\.[^@ ]+")


# ------------------------------------------------------------------------------
def mkEmptyDatabase(dbname):
    if os.path.isfile(dbname):
        os.remove(dbname)

    conn = sqlite3.connect(dbname)
    cur = conn.cursor()
    cur.execute("CREATE TABLE user ( "
                "uid INTEGER PRIMARY KEY AUTOINCREMENT, name text, "
                "passwd text, email text, enabled INTEGER NOT NULL DEFAULT 1, "
                "UNIQUE(name), UNIQUE(email))")
    conn.commit()

    conn.close()


# ------------------------------------------------------------------------------
def init():
    mkEmptyDatabase(DATABASE)

    if os.path.isfile(PASSWDFILE):
        os.remove(PASSWDFILE)

    open(PASSWDFILE, 'w').close()

    insertUser(config.DB_TEST_USER, config.DB_TEST_PASS, config.DB_TEST_EMAIL)


# ------------------------------------------------------------------------------
def insertUser(name, passwd, email):
    checkedEmail = parseaddr(email)[1]
    if len(checkedEmail) == 0 or not EMAIL_REGEX.match(checkedEmail):
        return (False, "Invalid email %s" % email)

    hpass = bcrypt.hashpw(passwd, bcrypt.gensalt(BCRYPT_ROUNDS))

    conn = sqlite3.connect(DATABASE)
    try:
        with conn:
            conn.execute('INSERT INTO user(uid,name,passwd,email) '
                         'VALUES (null,?,?,?)',
                         (name, hpass, checkedEmail))
    except sqlite3.IntegrityError:
        return (False, "User '%s' Already Exists" % name)

    try:
        with htpasswd.Basic(PASSWDFILE) as userdb:
            userdb.add(name, passwd)
    except htpasswd.basic.UserExists, err:
        return (False, "User '%s' Already Exists [%s]" % (name, str(err)))

    return (True, "")


# ------------------------------------------------------------------------------
def getUserEmail(name):
    conn = sqlite3.connect(DATABASE)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT email FROM user WHERE name=?', (name,))
            val = cur.fetchone()
            return val[0]
    except:
        pass

    return None


# ------------------------------------------------------------------------------
def getUserName(uid):
    conn = sqlite3.connect(DATABASE)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT name FROM user WHERE uid=?', (uid,))
            val = cur.fetchone()
            return val[0]
    except:
        pass

    return None


# ------------------------------------------------------------------------------
def checkUser(name, passwd):
    conn = sqlite3.connect(DATABASE)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT passwd FROM user '
                        'WHERE name=? AND enabled=1', (name,))
            val = cur.fetchone()
            if val is not None:
                return bcrypt.hashpw(passwd, val[0]) == val[0]
    except:
        return False

    return False


# ------------------------------------------------------------------------------
def changeUserPassword(name, newpass):
    try:
        with htpasswd.Basic(PASSWDFILE) as userdb:
            userdb.change_password(name, newpass)
    except htpasswd.basic.UserNotExists:
        return False

    hpass = bcrypt.hashpw(newpass, bcrypt.gensalt(BCRYPT_ROUNDS))

    conn = sqlite3.connect(DATABASE)
    try:
        with conn:
            conn.execute('UPDATE user SET passwd=? WHERE name=?',
                         (hpass, name))
    except:
        return False

    return True


# ------------------------------------------------------------------------------
def checkIfUserAvailable(name):
    conn = sqlite3.connect(DATABASE)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM user WHERE name=?', (name,))
            val = cur.fetchone()
            return val is None
    except:
        return False

    return False


# ------------------------------------------------------------------------------
def enableUser(name):
    conn = sqlite3.connect(DATABASE)
    with conn:
        conn.execute('UPDATE user SET enabled=1 WHERE name=?', (name,))


# ------------------------------------------------------------------------------
def disableUser(name):
    conn = sqlite3.connect(DATABASE)
    with conn:
        conn.execute('UPDATE user SET enabled=0 WHERE name=?', (name,))


# ------------------------------------------------------------------------------
def deleteUser(name):
    conn = sqlite3.connect(DATABASE)

    conn.execute('DELETE FROM user WHERE name=?', (name,))

    conn.commit()
    conn.close()

    try:
        with htpasswd.Basic(PASSWDFILE) as userdb:
            userdb.pop(name)
    except htpasswd.basic.UserNotExists:
        pass


# ------------------------------------------------------------------------------
