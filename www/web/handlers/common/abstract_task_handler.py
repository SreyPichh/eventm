import webapp2
import json

class AbstractTaskHandler(webapp2.RequestHandler):
    def render_json_response(self, ctx):
        self.response.headers['Content-Type'] = 'application/json'
        #self.response.headers['X-Frame-Options'] = 'GOFORIT'
        self.response.out.write(json.dumps(ctx))
        