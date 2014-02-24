VERSION = "0.5.0"

REMOTEHOST = "genorama@altamira1.ifca.es"

# for testing
REMOTEHOME = "testing"
DATADIR = "/gpfs/res_projects/cvcv/webserver/testing/"

# for stable
#REMOTEHOME = "users"
#DATADIR = "/gpfs/res_projects/cvcv/webserver/users/"

PIPE_LAUNCH = "../server_side/pipe_launcher.py"

# for stable
#PIPE_LAUNCH = "../../server_side/stable/pipe_launcher.py"

## Database Configurations
DB_RESET = True
DB_DATABASE = 'database.db'
DB_PASSFILE = 'htpasswd.db'
