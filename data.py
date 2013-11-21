#-------------------------------------------------------------------------------
import shutil
import os
import os.path

#-------------------------------------------------------------------------------
DATADIR = "/var/genorama/cluster/res_projects/"

#-------------------------------------------------------------------------------
def getUserFilename( username, filename ):
    return os.path.join( DATADIR, username, filename )

#-------------------------------------------------------------------------------
def saveFile( filename, filedata ):
    dir = os.path.dirname( filename )
    if not os.path.isdir( dir ):
        os.makedirs( dir )

    with open( filename, 'w' ) as f:
        shutil.copyfileobj( filedata, f )

#-------------------------------------------------------------------------------
