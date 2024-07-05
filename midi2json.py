
import os
import sys
import subprocess
import pip
import math
import threading
import time
import traceback
import json

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print(f'Usage: {sys.argv[0]} /path/to/file.json')
    print()
    print('Will write controller and program data to file.json as events are read.')
    sys.exit(1)

  json_file = sys.argv[1]
  json_data = dict()
  json_data['controller'] = dict()
  json_data['program'] = -1

  midi_events_proc = None
  while True:
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

        if not(midi_events_proc is None):
          try:
            midi_events_proc.kill()
            midi_events_proc = None
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
        for line in midi_events_proc.stdout: #.readlines():
          try:
            if not isinstance(line, str):
              line = line.decode('utf-8')
            line = line.strip()

            print(f'{line}', flush=True)

            tokens = [t for t in line.split() if len(f'{t}') > 0]
            change_made = False
            if 'Control change' in line:
              change_made = True
              controller = tokens[tokens.index('controller') + 1]
              value = tokens[tokens.index('value') + 1]

              try:
                json_data['controller'][controller] = int(value)
              except:
                json_data['controller'][controller] = float(value)
            elif 'Program change' in line:
              change_made = True
              program = int(tokens[tokens.index('program') + 1])
              json_data['program'] = program

            # finally write data
            if change_made:
              with open(json_file, 'w') as fd:
                json.dump(json_data, fd, indent=2, sort_keys=True)

          except:
            traceback.print_exc()


      else:
        print('No Midi devices detected!')

    except:
      traceback.print_exc()
      try:
        if not (midi_events_proc is None):
          midi_events_proc.kill()
          midi_events_proc = None
      except:
        traceback.print_exc()

    time.sleep(1.5)
