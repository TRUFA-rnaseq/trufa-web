######################################################################
PROJECT_NAME = "trufa"
VERSION = "0.12.0"

######################################################################
### Web Configurations ###

SERVER_CRT = "cert/server.crt"
SERVER_KEY = "cert/server.key"
WEB_DEBUG = False

EMAIL_JOB_COMPLETE = "mail/job_complete.txt"
EMAIL_JOB_COMPLETE_SUBJECT = 'TRUFA: Your analysis "{}" all done !'
EMAIL_SENDER = "kornobis@trufa.ifca.es"
EMAIL_SMTP = "localhost"

######################################################################
### Database configuracion ###
DB_RESET = True
DB_DATABASE = 'database.db'
DB_PASSFILE = 'htpasswd.db'

DB_TEST_USER = "admin"
DB_TEST_PASS = "admin"
DB_TEST_EMAIL = "j.smith@example.com"

######################################################################
### Job/runner configuration ###

REMOTEHOST = "genorama@altamira1.ifca.es"

# for testing
REMOTEHOME = "testing"
DATADIR = "/gpfs/res_projects/cvcv/webserver/testing/"

# for stable
#REMOTEHOME = "users"
#DATADIR = "/gpfs/res_projects/cvcv/webserver/users/"

## Launcher library
# for testing
PIPE_LAUNCH = "../server_side/pipe_launcher.py"
LAUNCHER_PATH = '../server_side/lib'

# for stable
#PIPE_LAUNCH = "../../server_side/stable/pipe_launcher.py"
#LAUNCHER_PATH = '/var/genorama/server_side/stable/lib'

# Demo datasets
DEMO_DIR = "/gpfs/res_projects/cvcv/webserver/demo_data/"
DEMO_INFILES = [ "Spombe_left.fq", "Spombe_right.fq"]

######################################################################
### Log/debug configuration ###

USELOGFILE = False
LOGFILE = "trufa.log"
#LOGFILE = "/var/genorama/log/trufa.log"
LOGFILEBYTES = 500*1024

USEWLOGFILE = True
WLOGFILE = "trufa_web.log"
#WLOGFILE = "/var/genorama/log/trufa_web.log"

######################################################################
import logging
logging.getLogger().setLevel( logging.DEBUG )

######################################################################
