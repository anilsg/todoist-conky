#!/bin/env python

import os.path as path
import urllib.request as request
import urllib.parse as parse
import urllib.error as error # Seems that urllib.error.HTTPError is not following documentation.
import json

token = '' # Todoist personal API token for authentication will be fetched from ~/.config/todoist.conf.
projects_url = 'https://beta.todoist.com/API/v8/projects' # URL to retrieve project names, cached daily.
tasks_url = 'https://beta.todoist.com/API/v8/tasks' # URL to get task list, cached every minute.
prefix = '${goto 800}${font Noto Sans Mono:size=12}${alignr}' # Conky prefix required every line to ensure reliable alignment etc.
prefix4 = '${goto 800}${font Noto Sans Mono:size=12}${alignr}${color4}' # Conky prefix including error colour.

try: # File may currently hold 40 character token only.
    with open(path.expanduser('~/.config/todoist.conf'), 'r') as cache: token = cache.read()
except Exception as e:
    print('{0}{1}: {2} [AUTH]'.format(prefix4, e.args[-1], e.args[0]))
    print('{0}{1}: {2} [AUTH]'.format(prefix4, 'No Todoist auth token in ~/.config/todoist.conf', 'FATAL'))
    exit() # Give up if the auth token is not available.

# Retrieve projects JSON from cache or server.
projects = '[]' # Default JSON projects list in case of failure (empty list).
try: # Try to read the project list from cache first to save a network request.
    with open(path.expanduser('~/config/conky/today.projects.json'), 'r') as cache:
        projects = cache.read() # Using cache if found.
except:
    try: # If cache not available retrieve project list and then cache it.
        dat = parse.urlencode({'token': token}) # Full projects list requires no other parameters than auth token.
        with request.urlopen('?'.join((projects_url, dat))) as res:
            if res.status != 200: raise OSError(res.status, res.msg) # OSError more reliable than urllib.error.HTTPError().
            projects = res.read().decode() # New JSON projects list available from server.
            with open(path.expanduser('~/.config/conky/today.projects.json'), 'w') as cache:
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
    for task in dat:
        color = str(task['priority']).join(('${color', '}')) # Conky colour directive using priority number e.g. ${color4}.
        project = projects.get(task['project_id'], 'unknown') # Project name if available.
        print('{0}{1}{2} [{3}]'.format(prefix, color, task['content'], project)) # Deliver finished line to Conky for display.
        # TODO: Truncate display lines to 50 chars or so, wrap onto at most 2 lines, indicate missing content with ...

except Exception as e: # On error report.
    # TODO: Store task list in cache file and report old information from cache when server not available.
    # TODO: When reporting task list from cache display as color0 to indicate off-line.
    print('{0}{1}: {2} [TASKS]'.format(prefix4, e.args[-1], e.args[0])) # args doesn't always have 2 items.


