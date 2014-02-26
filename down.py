#!/usr/bin/python

#-------------------------------------------------------------------------------
import web
from web.wsgiserver import CherryPyWSGIServer
import config

#-------------------------------------------------------------------------------
CherryPyWSGIServer.ssl_certificate = "cert/server.crt"
CherryPyWSGIServer.ssl_private_key = "cert/server.key"

web.config.debug = False

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
