#!/usr/bin/python

#-------------------------------------------------------------------------------
import web
import sys
from web.wsgiserver import CherryPyWSGIServer
import config

#-------------------------------------------------------------------------------
CherryPyWSGIServer.ssl_certificate = config.SERVER_CRT
CherryPyWSGIServer.ssl_private_key = config.SERVER_KEY

web.config.debug = config.WEB_DEBUG

#-------------------------------------------------------------------------------
urls = (
    '/favicon.ico', 'Favicon',
    '/(.*)', 'Home',
)

#-------------------------------------------------------------------------------
app = web.application( urls, globals() )

#-------------------------------------------------------------------------------
globals = {'version': config.VERSION }

#-------------------------------------------------------------------------------
def get_render():
    return web.template.render( 'templates/anom', base="down", globals=globals )

#-------------------------------------------------------------------------------
class Favicon:
    def GET( self ):
        raise web.seeother('/static/favicon.ico')

#-------------------------------------------------------------------------------
class Home:
    def GET( self, uri ):
        return get_render().d_main()

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    if config.USELOGFILE:
        fout = open( config.LOGFILE, 'a' )
        sys.stdout = fout
        sys.stderr = fout

    app.run()

#-------------------------------------------------------------------------------
