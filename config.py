PROJECT_NAME = "trufa"
VERSION = "0.8.0"

REMOTEHOST = "genorama@altamira1.ifca.es"

# for testing
REMOTEHOME = "testing"
DATADIR = "testing"

# for stable
#REMOTEHOME = "users"
#DATADIR = "/gpfs/res_projects/cvcv/webserver/users/"

# for testing
PIPE_LAUNCH = "../server_side/pipe_launcher.py"

# for stable
#PIPE_LAUNCH = "../../server_side/stable/pipe_launcher.py"

## Database Configurations
DB_RESET = True
DB_DATABASE = 'database.db'
DB_PASSFILE = 'htpasswd.db'

USELOGFILE = False
LOGFILE = "trufa.log"
#LOGFILE = "/var/genorama/log/trufa.log"
LOGFILEBYTES = 500*1024

USEWLOGFILE = True
WLOGFILE = "trufa_web.log"
#WLOGFILE = "/var/genorama/log/trufa_web.log"

import logging
logging.getLogger().setLevel( logging.DEBUG )
