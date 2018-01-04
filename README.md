<!-- vim: set ft=markdown spell: -->

# Conky config for displaying Todoist task list.

No installation is provided.
This repo just supplies the files required for placement in ``~/.config/conky``.

## Files

### conky.conf

- This is an unremarkable ``conky.conf`` used with this set up.
- The ``conky.conf`` file is expected in ``~/.config/conky/conky.conf``.
- This conf file also displays some minimal host stats and local and world times.
- The config includes directives to call the ``today.py`` script.
- Frequency of requests is once per minute.
- The config is designed for 1920 x 1080 screen.

### today.py

- The ``today.py`` script fetches project and task data from todoist.com and returns as conky directives.
- ``today.py`` should be kept in ``~/.config/conky/``
- ``today.py`` looks for the Todoist auth token in ``~/.config/todoist.conf``. Moving other configurables into this file is planned.

### today.projects.json

- The ``today.py`` script creates this file to cache the projects list initially retrieved from todoist.com.
- If your projects list changes you will need to delete this cache file to enable the new list to be retrieved.
- A daily automatic refresh of the projects list is planned but not yet implemented.

## Features

- The selected filtered (today) list of tasks is presented in the Conky window.
- Tasks are presented with a (possibly truncated) description (content) and project name.
- Tasks are displayed in colours according to priority.
- Tasks are sorted by priority and secondarily sorted by project name.
- Significant errors are reported, combined with the task list if possible.
- Projects list is cached. To refresh the projects list delete the cache file.
- Off-line access is planned retrieving from most recent cache.
- When off-line, tasks will be listed greyed out to indicate non-live status.
- When task content is too long lines are truncated and wrapped into at most 2 lines.

