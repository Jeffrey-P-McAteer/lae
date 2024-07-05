
import os
import sys
import subprocess
import pip
import math
import threading
import time
import traceback

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


try:
  import cairo
except:
  pip.main([
    'install', f'--target={pkgs}', 'pycairo',
  ])
  import cairo

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
GLib.threads_init()



m = {
  'x': 0,
  'y': 0,
  'want_exit': False,
  # dictionaries of MIDI device names, we write current values here when aseqdump reports changes
  'controller': dict(),
  'program': dict(),
}


def read_midi_data_t():
  global m

  while not m['want_exit']:
    try:
      # List all MIDI devices w/ `aconnect -i`
      midi_devices = subprocess.check_output(['aconnect', '-i']).decode('utf-8')
      midi_client_num = -1
      for line in midi_devices.splitlines():
        if not line.startswith('client '):
          continue
        if not 'card=' in line: # w/o card= this indicates a software midi device
          continue
        midi_client_num = int( ''.join( c for c in line.split()[1] if c.isdigit() ) )


      if midi_client_num >= 0:
        print(f'Listening to MIDI client number {midi_client_num}')

        if 'midi_events_proc' in m:
          try:
            m['midi_events_proc'].kill()
          except:
            traceback.print_exc()

        midi_events_proc = subprocess.Popen(
          #['aseqdump', '-p', f'{midi_client_num}'],
          ['stdbuf', '-oL', '-eL', '--',
            'aseqdump', '-p', f'{midi_client_num}'],
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
          shell=False,
          text=True,
          bufsize=1,
        )
        m['midi_events_proc'] = midi_events_proc
        for line in midi_events_proc.stdout.readlines():
          try:
            if not isinstance(line, str):
              line = line.decode('utf-8')
            line = line.strip()

            print(f'{line}', flush=True)

            tokens = [t for t in line.split() if len(f'{t}') > 0]
            if 'Control change' in tokens:
              controller = tokens[tokens.index('controller') + 1]
              value = tokens[tokens.index('value') + 1]

              try:
                m['controller'][controller] = int(value)
              except:
                m['controller'][controller] = float(value)

          except:
            traceback.print_exc()


      else:
        print('No Midi devices detected!')

    except:
      traceback.print_exc()
    time.sleep(2.5)

  print('Exiting read_midi_data_t')



def on_draw(w, cr, width, height, user_data=None):
  global m
  # Cr is a https://pycairo.readthedocs.io/en/latest/reference/context.html

  cr.set_source_rgb(1, 1, 0)
  cr.arc(320 + m['x'], 240 + m['y'],100, 0, 2*math.pi)
  cr.fill_preserve()

  cr.set_source_rgb(0, 0, 0)
  cr.stroke()

  cr.arc(280 + m['x'], 210 + m['y'],20, 0, 2*math.pi)
  cr.arc(360 + m['x'], 210 + m['y'],20, 0, 2*math.pi)
  cr.fill()

  cr.set_line_width(10)
  cr.set_line_cap(cairo.LINE_CAP_ROUND)
  cr.arc(320 + m['x'], 240 + m['y'], 60, math.pi/4, math.pi*3/4)
  cr.stroke()


def on_app_activate(app):
  win = Gtk.ApplicationWindow(application=app)
  win.set_title('floatme')
  win.set_default_size(640, 480)

  da = Gtk.DrawingArea() # See https://docs.gtk.org/gtk4/class.DrawingArea.html
  #da.connect('draw', on_draw)
  da.set_draw_func(on_draw)
  win.set_child(da)

  win.present()

def main(args=sys.argv):
  global m

  midi_t = threading.Thread(target=read_midi_data_t, args=())
  midi_t.daemon = True
  midi_t.start()

  app = Gtk.Application(application_id='com.jmcateer.lae.sandbox')
  app.connect('activate', on_app_activate)
  app.run(None)

  m['want_exit'] = True
  if 'midi_events_proc' in m:
    m['midi_events_proc'].kill()



if __name__ == '__main__':
  main()


