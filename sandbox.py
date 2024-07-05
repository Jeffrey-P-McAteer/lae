
import os
import sys
import subprocess
import pip

pkgs = os.path.join(os.path.dirname(__file__), 'sandbox-site-packages')
os.makedirs(pkgs, exist_ok=True)
sys.path.append(pkgs)


try:
  import gi
except:
  pip.main([
    'install', f'--target={pkgs}', 'PyGObject',
  ])
  import gi



def main(args=sys.argv):
  gi.require_version("Gtk", "4.0")
  from gi.repository import Gtk

  def on_activate(app):
      win = Gtk.ApplicationWindow(application=app)
      win.set_title('floatme')
      btn = Gtk.Button(label="Hello, World!")
      btn.connect('clicked', lambda x: win.close())
      win.set_child(btn)
      win.present()

  app = Gtk.Application(application_id='com.jmcateer.lae.sandbox')
  app.connect('activate', on_activate)
  app.run(None)



if __name__ == '__main__':
  main()


