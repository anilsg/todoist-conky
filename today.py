#!/bin/env python

# ~/.config/conky/today.py
# Conky script to return Todoist tasks in the 'today' filter as display lines.
# Runs in ~/.config/conky/.
# Requires Todoist auth token in ~/.config/todoist.conf.
# Requires associated ~/.config/conky/conky.conf to call this script.
# This line will work but recommend refresh interval of 60 seconds or more, otherwise use execpi:
#  ${execp python ~/.config/conky/today.py}
# These are some appropriate colour definitions to use in the conky.conf:
#  color4 = 'CC5555',
#  color3 = 'EEAA55',
#  color2 = 'EEDD55',
#  color1 = 'AAAAAA',
#  color0 = '555555',
# Also caches the Todoist project names in ~/.config/conky/today.projects.json
#
# Anil Gulati
# 05/01/2018

import urllib.request as request
import urllib.parse as parse
import urllib.error as error # Seems that urllib.error.HTTPError is not following documentation.
import json
import textwrap
from os.path import expanduser

token = '' # Todoist personal API token for authentication will be fetched from ~/.config/todoist.conf.
projects_url = 'https://beta.todoist.com/API/v8/projects' # URL to retrieve project names, cached daily.
tasks_url = 'https://beta.todoist.com/API/v8/tasks' # URL to get task list, cached every minute.
prefix = '${goto 800}${font Noto Sans Mono:size=12}${alignr}' # Conky prefix required every line to ensure reliable alignment etc.
prefix4 = '${goto 800}${font Noto Sans Mono:size=12}${alignr}${color4}' # Conky prefix including error colour.
prefix18 = '${goto 800}${font Noto Sans Mono:size=18}${alignr}${color0}' # Conky prefix including error colour.
linelength = 50

try: # File may currently hold 40 character token only.
    with open(expanduser('~/.config/todoist.conf'), 'r') as cache: token = cache.read()
except Exception as e:
    print('{0}{1}: {2} [AUTH]'.format(prefix4, e.args[-1], e.args[0]))
    print('{0}{1}: {2} [AUTH]'.format(prefix4, 'No Todoist auth token in ~/.config/todoist.conf', 'FATAL'))
    exit() # Give up if the auth token is not available.

# Retrieve projects JSON from cache or server.
projects = '[]' # Default JSON projects list in case of failure (empty list).
try: # Try to read the project list from cache first to save a network request.
    with open(expanduser('~/config/conky/today.projects.json'), 'r') as cache:
        projects = cache.read() # Using cache if found.
except:
    try: # If cache not available retrieve project list and then cache it.
        dat = parse.urlencode({'token': token}) # Full projects list requires no other parameters than auth token.
        with request.urlopen('?'.join((projects_url, dat))) as res:
            if res.status != 200: raise OSError(res.status, res.msg) # OSError more reliable than urllib.error.HTTPError().
            projects = res.read().decode() # New JSON projects list available from server.
            with open(expanduser('~/.config/conky/today.projects.json'), 'w') as cache:
                cache.write(projects) # Save projects list in cache file.
                # TODO: Use __file__ or sys.argv[0] to locate and write cache next to script.
                # TODO: Cache this daily instead of once only by including date in cache filename.
                # TODO: Requires clean up like: ls today.projects.json.* | grep -v today.projects.json.YYYYMMDD | xargs rm
                # TODO: Maybe some ideas in https://pypi.python.org/pypi/simple_cache/0.35
    except Exception as e:
        print('{0}{1}: {2} [PROJECTS]'.format(prefix4, e.args[-1], e.args[0]))

# Convert projects from JSON list of objects to a Python mapping from project id to project name.
projects = json.loads(projects) # Convert JSON to Python list of projects.
projects = dict((proj['id'], proj['name']) for proj in projects) # Convert list to project_id: project_name mapping.
# projects is potentially an empty dict under some error conditions.

# Retrieve selected tasks list from cache (not yet implemented) or server using selected filter (today).
try: # Always try the server first to get an up to date list.
    dat = parse.urlencode({'token': token, 'filter': 'today'})
    with request.urlopen('?'.join((tasks_url, dat))) as res: # Request list of tasks.
        if res.status != 200: raise OSError(res.status, res.msg) # urllib.error.HTTPError() doesn't follow documentation.
        dat = json.loads(res.read().decode()) # Convert json task list to python list of dicts.
    dat.sort(key=lambda t: projects.get(t['project_id'], '')) # Secondary sort on project name.
    dat.sort(key=lambda t: t['priority'], reverse=True) # Stable sort primary key is priority.
    wrapper = textwrap.TextWrapper(expand_tabs=False, placeholder=' ...') # Reusable instance is more efficient.
    if not dat: # No tasks found.
        color = '${color0}' # Intended to be a greyed out / low contrast colour.
        print(''.join(('${voffset -60}', prefix18, 'NO TASKS'))) # Deliver single line to Conky for display.
    else:
        for task in dat: # For all tasks found.
            color = str(task['priority']).join(('${color', '}')) # Conky colour directive using priority number e.g. ${color4}.
            project = ' [{0}]'.format(projects.get(task['project_id'], 'unknown')) # ' [Project Name]'.
            wrapper.max_lines = None # Put line limit back to unrestricted.
            wrapper.width = linelength # Set to standard width and break to find line 1.
            lines = wrapper.wrap(task['content']) or ['<no task description>'] # No content wraps to empty list.
            line1 = lines[0] # Take the first one off the top for output line 1.
            if len(lines) == 1:
                print(''.join((prefix, color, line1, project))) # Deliver single line to Conky for display.
                continue # Next task.
            elif len(lines) > 2: # Look for last line to display as "First line" " ... " "Last line".
                lines = ' '.join(lines[1:]) # Rejoin all the other lines for finding the last line.
                wrapper.max_lines = 1 # Use the line limit to return 1 line, width will still be linelength as last set.
                lines = wrapper.wrap(lines[::-1]) # Wrap the reverse string to put the last line first.
                line2 = lines[0][::-1] # Take the first line, which is really the last line, and reverse it back to normal.
            else: # Otherwise split two lines into two equal length lines.
                lines = ' '.join(lines) # Put the two lines back together.
                wrapper.width = len(line1) # Start at the maximum possible necessary line length.
                while len(wrapper.wrap(lines)) == 2: wrapper.width -= 1 # Look for shortest line length that will wrap to 2 lines.
                wrapper.width += 1 # Put it back to the shortest line length that worked.
                line1, line2 = wrapper.wrap(lines)
            print(''.join((prefix, color, line1, project))) # Display 1st line with project name.
            print(''.join((prefix, color, line2, ' ' * len(project)))) # 2nd line with blank indent instead of project name.
except Exception as e: # On error report.
    # TODO: Store task list in cache file and report old information from cache when server not available.
    # TODO: When reporting task list from cache display as color0 to indicate off-line.
    print('{0}{1}: {2} [TASKS]'.format(prefix4, e.args[-1], e.args[0])) # args doesn't always have 2 items.


