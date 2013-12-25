#-------------------------------------------------------------------------------
import shutil
import os
import os.path

#-------------------------------------------------------------------------------

DATADIR = "/gpfs/res_projects/cvcv/webserver/users/"

FT_UNKNOWN = 0
FT_FAST = 1
FT_TGZ_FAST = 2
FT_SEQ_DB = 3
FT_ASSEM = 4
FT_MAP_ASSEM = 5
FT_HMM = 6

fileExtTable = {
    'fastq': FT_FAST,
    'fq': FT_FAST,
    'fastq.tar.gz': FT_TGZ_FAST,
    'fq.tar.gz': FT_TGZ_FAST,
    'bam': FT_MAP_ASSEM,
    'sam': FT_MAP_ASSEM,
    'hmm': FT_HMM
}

fileOptionTable = {
    'undef' : FT_UNKNOWN,
    'fast' : FT_FAST,
    'tgz_fast' : FT_TGZ_FAST,
    'seq_db' : FT_SEQ_DB,
    'assem' : FT_ASSEM,
    'map_assem' : FT_MAP_ASSEM,
    'hmm_profile' : FT_HMM
}

#         typo            extension
# 0       Unknown
# 1       fastq           .fastq or .fq
# 2       compressed fq   .fastq.tar.gz or .fq.tar.gz
# 3       seq databases   .fas
# 4       assemblies      .fas
# 5       mapped assbl.   .bam or .sam
# 6       hmm profile     .hmm 

#-------------------------------------------------------------------------------
def getUserFilename( username, filename ):
    # NOTE EK: NOT SURE THIS IS CORRECT TO CHANGE PATH FOR DATA LIKE THIS
    # BEFORE WAS:     return os.path.join( DATADIR, username, filename )
    return os.path.join( DATADIR, username, "data", filename )

#-------------------------------------------------------------------------------
def saveFile( filename, filedata ):
    dir = os.path.dirname( filename )
    if not os.path.isdir( dir ):
        os.makedirs( dir )

    with open( filename, 'w' ) as f:
        shutil.copyfileobj( filedata, f )

#-------------------------------------------------------------------------------
def clearFilePart( filename ):
    if os.path.isfile( filename + '.part' ):
        os.remove( filename + '.part' )

#-------------------------------------------------------------------------------
def saveFilePart( filename, filedata ):
    dir = os.path.dirname( filename )
    if not os.path.isdir( dir ):
        os.makedirs( dir )

    with open( filename + '.part', 'a' ) as f:
        shutil.copyfileobj( filedata, f )

#-------------------------------------------------------------------------------
def endFilePart( filename ):
    if os.path.isfile( filename + '.part' ):
        shutil.move( filename + '.part', filename )

#-------------------------------------------------------------------------------
def getFileType( filename, option ):
    if option == 'auto':
        lname = filename.lower()
        for k,v in fileExtTable.items():
            if lname.endswith( k ):
                return v
        return FT_UNKNOWN

    return fileOptionTable.get( option.lower(), FT_UNKNOWN )

#-------------------------------------------------------------------------------
