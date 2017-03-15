# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webapp2


# class MainPage(webapp2.RequestHandler):
#     def get(self):
#         self.response.headers['Content-Type'] = 'text/plain'
#         self.response.write('Hello, World!Hey I have changed something here also')

# class NewsPage(webapp2.RequestHandler):
# 	def get(self):
# 		self.response.headers['Content-Type'] = 'text/plain'
# 		self.response.write('from news this is hot news')

# class Home(webapp2.RequestHandler):
#     def get(self):
#         self.response.headers['Content-Type'] = 'text/plain'
#         self.response.write('test all')



app = webapp2.WSGIApplication([
    ('/', MainPage),('/news', NewsPage),('/test', Home)
], debug=True)


