#-------------------------------------------------------------------------------
import shutil
import os
import os.path
import config

#-------------------------------------------------------------------------------

DATADIR = config.DATADIR

FT_UNKNOWN = 0
# Read file (fastq, fq)
FT_FAST = 1
# Compressed Read file (fastq.gz ...)
FT_TGZ_FAST = 2
# Nucleotide seqs database (.fas)
FT_SEQ_DB_NUC = 3
# Amino acids seqs database (.fas)
FT_SEQ_DB_AA = 4
# Assembled transcripts (.fas)
FT_ASSEM = 5
# Mapped transcripts (.bam )
FT_MAP_ASSEM = 6
# Protein hmm for hmmer (.hmm)
FT_HMM = 7

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
    'seq_db_nuc' : FT_SEQ_DB_NUC,
    'seq_db_aa' : FT_SEQ_DB_AA,
    'assem' : FT_ASSEM,
    'map_assem' : FT_MAP_ASSEM,
    'hmm_profile' : FT_HMM
}

#         typo            extension
# 0       Unknown
# 1       fastq           .fastq or .fq
# 2       compressed fq   .fastq.tar.gz or .fq.tar.gz
# 3       seq databases nuc   .fas
# 4       seq db AA       .fas
# 5       assemblies      .fas
# 6       mapped assbl.   .bam or .sam
# 7       hmm profile     .hmm

#-------------------------------------------------------------------------------
IO_FOLDER = "data"
PARTIAL_SUFFIX = ".part"

#-------------------------------------------------------------------------------
def getUserFilename( username, filename ):
    return os.path.join( DATADIR, username, IO_FOLDER, filename )

#-------------------------------------------------------------------------------
def saveFile( filename, filedata ):
    dir = os.path.dirname( filename )
    if not os.path.isdir( dir ):
        os.makedirs( dir )

    with open( filename, 'w' ) as f:
        shutil.copyfileobj( filedata, f )

#-------------------------------------------------------------------------------
def linkDemoFile(username, demo_f):
    # Now only work for fastq files (f_type is set to 1)

    dir = os.path.join( config.DATADIR, username, IO_FOLDER )
    if not os.path.isdir( dir ):
        os.makedirs( dir )

    lpath = os.path.join( dir , demo_f )
    fpath = os.path.join( config.DEMO_DIR, demo_f )

    if not os.path.islink(lpath):
        os.symlink( fpath, lpath )

#-------------------------------------------------------------------------------
def clearFilePart( filename ):
    if os.path.isfile( filename + PARTIAL_SUFFIX ):
        os.remove( filename + PARTIAL_SUFFIX )

#-------------------------------------------------------------------------------
def saveFilePart( filename, filedata ):
    dir = os.path.dirname( filename )
    if not os.path.isdir( dir ):
        os.makedirs( dir )

    with open( filename + PARTIAL_SUFFIX, 'a' ) as f:
        shutil.copyfileobj( filedata, f )

#-------------------------------------------------------------------------------
def endFilePart( filename ):
    if os.path.isfile( filename + PARTIAL_SUFFIX ):
        shutil.move( filename + PARTIAL_SUFFIX, filename )

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
