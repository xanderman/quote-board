import cgi
import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db


class Quote(db.Model):
  author = db.StringProperty(required=False, multiline=False)
  text = db.StringProperty(required=True, multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)
  contributor = db.UserProperty(required=True)
  public = db.BooleanProperty(required=True)


def GetLoginUrl(handler):
  if users.get_current_user():
    return (users.create_logout_url(handler.request.uri), 'Logout')
  else:
    return (users.create_login_url(handler.request.uri), 'Login')


class Public(webapp.RequestHandler):
  def get(self):
    """Render the public quotes page."""
    quotes = Quote.gql('WHERE public = :1 ORDER BY date DESC', True)

    url, url_linktext = GetLoginUrl(self)

    template_values = {
      'active': 'public',
      'quotes': quotes,
      'url': url,
      'url_linktext': url_linktext,
      'butter': self.request.get('butter'),
    }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))


class Mine(webapp.RequestHandler):
  def get(self):
    """Render the private quotes page."""
    if not users.get_current_user():
      self.redirect('/?butter=You must be logged in to see your quotes')

    url, url_linktext = GetLoginUrl(self)
    quotes = Quote.gql('WHERE contributor = :1 ORDER BY date DESC',
        users.get_current_user())

    template_values = {
      'active': 'mine',
      'quotes': quotes,
      'url': url,
      'url_linktext': url_linktext,
      'butter': self.request.get('butter'),
    }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))


class Create(webapp.RequestHandler):
  def get(self):
    """Render the create page."""
    self.CheckUserPerms()

    url, url_linktext = GetLoginUrl(self)
    template_values = {
      'active': 'edit',
      'quote': None,
      'action': '/create',
      'url': url,
      'url_linktext': url_linktext,
    }
    path = os.path.join(os.path.dirname(__file__), 'edit.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    """Save the new quote."""
    self.CheckUserPerms()

    contributor = users.get_current_user()
    author = self.request.get('author') or None # Save blank author as anonymous
    text = self.request.get('text')
    if self.request.get('public'):
      public = True
    else:
      public = False
    quote = Quote(contributor=contributor, author=author, text=text, public=public)
    quote.put()
    self.redirect('/?butter=Your quote has been saved')

  def CheckUserPerms(self):
    if not users.get_current_user():
      self.redirect('/?butter=You must be logged in to submit a quote')


class Edit(webapp.RequestHandler):
  def get(self):
    """Render the edit page."""
    quote = Quote.get(self.request.get('key'))
    self.CheckUserPerms(quote)
    template_values = {
      'active': 'edit',
      'quote': quote,
      'action': '/edit',
    }
    path = os.path.join(os.path.dirname(__file__), 'edit.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    """Save the edited quote."""
    quote = Quote.get(self.request.get('key'))
    self.CheckUserPerms(quote)
    if quote.contributor == users.get_current_user():
      quote.author = self.request.get('author')
      quote.text = self.request.get('text')
      if self.request.get('public'):
        quote.public = True
      else:
        quote.public = False
      quote.put()
      butter = 'Your quote has been saved.'
    else:
      butter = 'You can only edit your quotes.'
    self.redirect('/?butter=%s' % butter)

  def CheckUserPerms(self, quote):
    contributor = quote.contributor
    if not users.get_current_user() == contributor:
      self.redirect('/?butter=You do not own that quote')


application = webapp.WSGIApplication(
                                     [('/', Public),
                                      ('/public', Public),
                                      ('/mine', Mine),
                                      ('/create', Create),
                                      ('/edit', Edit)],
                                     debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
