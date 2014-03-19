#!/usr/bin/python

#-------------------------------------------------------------------------------
import web
from web.wsgiserver import CherryPyWSGIServer
import os.path
import sys
import json
import database
import data
import pipeline
import config

#-------------------------------------------------------------------------------
CherryPyWSGIServer.ssl_certificate = "cert/server.crt"
CherryPyWSGIServer.ssl_private_key = "cert/server.key"

web.config.debug = False

#-------------------------------------------------------------------------------
urls = (
    '/favicon.ico', 'Favicon',
    '/robots.txt', 'Robots',
    '/', 'Home',
    '/howto','Howto',
    '/run_job',"RunJob",
    '/faq','Faq',
    '/about', 'About',
    '/login', 'Login',
    '/setup', 'Setup',
    '/login_error', 'LoginError',
    '/logout', 'Logout',
    '/register', 'Register',
    '/ajax/me', 'AjaxMe',
    '/ajax/file', 'AjaxFiles',
    '/ajax/filepart', 'AjaxFileParts',
    '/ajax/job', 'AjaxJobs',
    '/ajax/job/(.*)', 'AjaxJob',
    '/ajax/jobname', 'AjaxJobName',
    '/job/(.*)', 'Job',
    '/file/(.*)/.*', 'File',
    '/manager', 'Manager',
    '/web/login', 'Login',
    '/web/register', 'Register',
    '/web/ajax/me', 'AjaxMe',
    '/web/ajax/file', 'AjaxFiles',
    '/web/ajax/filepart', 'AjaxFileParts',
    '/web/ajax/job', 'AjaxJobs',
    '/web/ajax/job/(.*)', 'AjaxJob',
    '/web/ajax/jobname', 'AjaxJobName',
    '/web/(.*)', 'WebRedirect',
)

#-------------------------------------------------------------------------------
app = web.application( urls, globals() )
store = web.session.DiskStore( 'sessions' )
session = web.session.Session( app, store, initializer={'login': 0, 'user': None} )

#-------------------------------------------------------------------------------
globals = {'version': config.VERSION }

#-------------------------------------------------------------------------------
def logged():
    return (session.login == 1)

#-------------------------------------------------------------------------------
def get_render():
    if logged():
        return web.template.render( 'templates/logged', base="layout", globals=globals )
    else:
        return web.template.render( 'templates/anom', base="layout", globals=globals )

#-------------------------------------------------------------------------------
def clearSession():
    session.login = 0
    session.user = None

#-------------------------------------------------------------------------------
class WebRedirect():
    def GET( self, name ):
        raise web.seeother( '/' + name )

#-------------------------------------------------------------------------------
class Favicon:
    def GET( self ):
        raise web.seeother('/static/favicon.ico')

#-------------------------------------------------------------------------------
class Robots:
    def GET( self ):
        raise web.seeother('/static/robots.txt')

#-------------------------------------------------------------------------------
class Home:
    def GET( self ):
        return get_render().main()

#-------------------------------------------------------------------------------
class Howto:
    def GET( self ):
        return get_render().howto()

#-------------------------------------------------------------------------------
class RunJob:
    def GET( self ):
        return get_render().run_job()

#-------------------------------------------------------------------------------
class Faq:
    def GET ( self ):
        return get_render().faq()
        
#-------------------------------------------------------------------------------
class About:
    def GET( self ):
        return get_render().about()

#-------------------------------------------------------------------------------
class Manager:
    def GET( self ):
        if logged():
            return get_render().manager()
        else:
            raise web.seeother('/')

#-------------------------------------------------------------------------------
class Setup:
    def GET( self ):
        if logged():
            return get_render().setup()
        else:
            raise web.seeother('/')

#-------------------------------------------------------------------------------
class Login:
    def GET( self ):
        raise web.seeother('/')

    def POST(self):
        try:
            name = web.input().user
            passwd = web.input().passwd
            if database.checkUser( name, passwd ):
                session.login = 1
                session.user = name
            else:
                clearSession()
        except:
            clearSession()

        if logged():
            raise web.seeother('/')
        else:
            raise web.seeother('/login_error')

#-------------------------------------------------------------------------------
class LoginError:
    def GET( self ):
        return get_render().login_error()

#-------------------------------------------------------------------------------
class Logout:
    def GET( self ):
        session.login = 0
        session.kill()
        raise web.seeother('/')

#-------------------------------------------------------------------------------
class Register:
    ##### UNDER DVPT #####
    def GET( self):
        return get_render().register()

    def PUT(self):

        try:
            name = web.input().user_name
            passwd = web.input().pwd
            if database.checkIfUserAvailable( name ):
                print "User available"
            else:
                print "User not available"
                
        except:
            clearSession()
        
#-------------------------------------------------------------------------------
class AjaxMe:
    def GET( self ):
        if logged():
            return json.dumps( {'username': session.user} )
        else:
            raise web.seeother('/')

    def PUT( self ):
        if logged():
            try:
                passwd = web.input().oldpass
                if not database.checkUser( session.user, passwd ):
                    return json.dumps( {'ok':False, 'msg': "invalid password" } )

                newpass = web.input().newpass
                repeatpass = web.input().repeatpass

                if newpass != repeatpass:
                    return json.dumps( {'ok':False, 'msg': "password check invalid" } )

                if database.changeUserPassword( session.user, newpass ):
                    return json.dumps( {'ok':True } )
                else:
                    return json.dumps( {'ok':False, 'msg': "password change error" } )

            except:
                print sys.exc_info()
                return json.dumps( {'ok':False, 'msg':"can't update user"} )

            return json.dumps( {'ok':False, 'msg':"unknown error"} )
        else:
            raise web.seeother('/')

#-------------------------------------------------------------------------------
class AjaxFiles:
    def GET( self ):
        if logged():
            web.header('Content-Type', 'application/json')
            x = web.input()
            try:
                files = []
                if x.has_key( 'filetype' ):
                    filetype = x['filetype']
                    files = database.getUserFilesWithType( session.user, int(filetype) )
                else:
                    files = database.getUserFiles( session.user )

                return json.dumps( {'files': files} )
            except:
                print sys.exc_info()
                web.debug( "can't get filelist" )

        else:
            raise web.seeother('/')

    def PUT( self ):
        if logged():
            try:
                x = web.input(myfile={})
                filename = data.getUserFilename( session.user, x['myfile'].filename )
                filetype = data.getFileType( x['myfile'].filename, x['myfiletype'] )
                data.saveFile( filename, x['myfile'].file )
                database.insertFileWithType( session.user, x['myfile'].filename, filetype )
            except:
                print sys.exc_info()
                web.debug( "can't save file" )

            return "OK"

        else:
            raise web.seeother('/')

#-------------------------------------------------------------------------------
class AjaxFileParts:
    def PUT( self ):
        if logged():
            try:
                x = web.input(myfile={})
                if x['status'] == "start":
                    filename = data.getUserFilename( session.user, x['myfilename'] )
                    data.clearFilePart( filename )
                elif x['status'] == "end":
                    filename = data.getUserFilename( session.user, x['myfilename'] )
                    filetype = data.getFileType( x['myfilename'], x['myfiletype'] )
                    data.endFilePart( filename )
                    database.insertFileWithType( session.user, x['myfilename'], filetype )
                elif x['status'] == "part":
                    filename = data.getUserFilename( session.user, x['myfilename'] )
                    data.saveFilePart( filename, x['myfile'].file )

            except:
                print sys.exc_info()
                web.debug( "can't save file" )

            return "OK"

        else:
            raise web.seeother('/')

#-------------------------------------------------------------------------------
class AjaxJobs:
    def GET( self ):
        if logged():
            web.header('Content-Type', 'application/json')
            jobs = database.getUserJobs( session.user )
            return json.dumps( {'jobs': jobs} )
        else:
            raise web.seeother('/')

    def POST( self ):
        if logged():
            x = web.input()
            print x
            try:
                pipeline.startJob( session.user, x )

            except:
                print sys.exc_info()
                web.debug( "can't start new job" )
                return json.dumps( {'ok':False, 'msg':"can't start new job"} )

            return json.dumps( {'ok':True} )
        else:
            raise web.seeother('/')

#-------------------------------------------------------------------------------
class AjaxJob:
    def DELETE( self, jobid ):
        try:
            if pipeline.cancelJob( session.user, jobid ):
                return json.dumps( {'ok':True} )
        except:
            print sys.exc_info()

        web.debug( "can't delete job " + str(jobid) )
        return json.dumps( {'ok':False, 'msg':"can't delete job"} )

#-------------------------------------------------------------------------------
class AjaxJobName:
    def GET( self ):
        raise web.seeother('/')

    def PUT( self ):
        if logged():
            x = web.input()
            try:
                database.changeJobName( x['jobid'], x['newname'] )
            except:
                print sys.exc_info()
                web.debug( "can't change job name" )
                return json.dumps( {'ok':False, 'msg':"can't change job name"} )

            return json.dumps( {'ok':True} )
        else:
            raise web.seeother('/')

#-------------------------------------------------------------------------------
class File:
    def GET( self, fileid ):
        if logged():
            if database.isFileAllowedFromUser( fileid, session.user ):
                filename = database.getFileFullName( fileid )
                with open( filename, "r" ) as f:
                    return f.read()
            else:
                return get_render().notallowed()
        else:
            raise web.seeother('/')

#-------------------------------------------------------------------------------
class Job:
    def GET( self, jobid ):
        if logged():
            if database.isJobFromUser( jobid, session.user ):
                jobinfo = database.getJobInfo( jobid )
                return get_render().job( jobinfo )
            else:
                return get_render().notallowed()
        else:
            raise web.seeother('/')

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    if config.USELOGFILE:
        fout = open( config.LOGFILE, 'a' )
        sys.stdout = fout
        sys.stderr = fout

    database.init()
    p = pipeline.run()
    app.run()
    p.terminate()

#-------------------------------------------------------------------------------
