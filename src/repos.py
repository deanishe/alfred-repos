#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-04
#

"""repos.py [options] [<query>] [<appnum>] [<path>]

Find, open and search Git repos on your system.

Usage:
    repos.py [<query>]
    repos.py (-e|--edit)
    repos.py --helpfile
    repos.py --update
    repos.py --open <appnum> <path>

Options:
    --update        Update database of Git repos
    --open          Open path in specified app
    -e, --edit      Open settings file
    -h, --help      Show this message
    --helpfile      Open included help file

"""

from __future__ import print_function, unicode_literals

import sys
import os
import subprocess

from workflow import Workflow, ICON_WARNING, ICON_INFO
from workflow.background import is_running, run_in_background

__version__ = '1.1'


# How often to check for new/updated repos
UPDATE_INTERVAL = 3600 * 3  # 3 hours

# GitHub repo for self-updating
GITHUB_UPDATE_CONF = {'github_slug': 'deanishe/alfred-repos'}

# GitHub Issues
HELP_URL = 'https://github.com/deanishe/alfred-repos/issues'

# Icon shown if a newer version is available
ICON_UPDATE = 'update-available.png'


DEFAULT_SETTINGS = {
    'search_dirs': [{
        'path': '~/delete/this/example',
        'depth': 2,
        'name_for_parent': 1,
        'excludes': ['tmp', 'bad/smell/*']
    }],
    'global_exclude_patterns': [],
    'app_1': 'Finder',
    'app_2': 'Terminal',
    'app_3': None,
    'app_4': None,
    'app_5': None,
    'app_6': None,
}

# Will be populated later
log = None


def join_english(items):
    """Join a list of unicode objects with commas and/or 'and'"""
    if isinstance(items, unicode):
        return items
    if len(items) == 1:
        return '{}'.format(items[0])
    elif len(items) == 2:
        return ' and '.join(items)
    last = items.pop()
    return ', '.join(items) + ' and {}'.format(last)


def main(wf):
    from docopt import docopt

    # Handle arguments
    # ------------------------------------------------------------------
    args = docopt(__doc__, wf.args)

    log.debug('args: {}'.format(args))

    query = args.get('<query>')
    path = args.get('<path>')
    appnum = args.get('<appnum>')
    if appnum:
        appnum = int(appnum)

    apps = {}
    for i in range(1, 7):
        app = wf.settings.get('app_{}'.format(i))
        if isinstance(app, list):
            app = app[:]
        apps[i] = app

    if not apps.get(1):  # Things will break if this isn't set
        apps[1] = 'Finder'

    # Alternate actions
    # ------------------------------------------------------------------
    if appnum and path:
        app = apps.get(appnum)
        if app is None:
            print('App {} not set. Use `reposettings`'.format(appnum))
            return 0
        else:
            if not isinstance(app, list):
                app = [app]
            for a in app:
                subprocess.call(['open', '-a', a, path])
            return 0

    elif args.get('--edit'):
        subprocess.call(['open', wf.settings_path])
        return 0

    elif args.get('--update'):
        run_in_background('update', ['/usr/bin/python', 'update.py'])
        return 0

    # Notify user if update is available
    # ------------------------------------------------------------------
    if wf.update_available:
        v = wf.cached_data('__workflow_update_status', max_age=0)['version']
        log.info('Newer version ({}) is available'.format(v))
        wf.add_item('Version {} is available'.format(v),
                    'Use `workflow:update` to install',
                    icon=ICON_UPDATE)

    # Try to search git repos
    # ------------------------------------------------------------------
    search_dirs = wf.settings.get('search_dirs', [])

    # Can't do anything with no directories to search
    if not search_dirs or wf.settings == DEFAULT_SETTINGS:
        wf.add_item("You haven't configured any directories to search",
                    'Use `reposettings` to edit your configuration',
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Load data, update if necessary
    if not wf.cached_data_fresh('repos', max_age=UPDATE_INTERVAL):
        run_in_background('update', ['/usr/bin/python', 'update.py'])

    repos = wf.cached_data('repos', max_age=0)

    # Show appropriate warning/info message if there are no repos to
    # show/search
    # ------------------------------------------------------------------
    if not repos:
        if is_running('update'):
            wf.add_item('Initialising database of repos…',
                        'Should be done in a few seconds',
                        icon=ICON_INFO)
        else:
            wf.add_item('No known git repos',
                        'Check your settings with `reposettings`',
                        icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Check if cached data is old version
    # ------------------------------------------------------------------
    if isinstance(repos[0], basestring):
        run_in_background('update', ['/usr/bin/python', 'update.py'])
        wf.add_item('Updating format of repos database…',
                    'Should be done in a few seconds',
                    icon=ICON_INFO)
        wf.send_feedback()
        return 0

    # Perform search and send results to Alfred
    # ------------------------------------------------------------------

    # Set modifier subtitles
    modifier_subtitles = {}
    i = 2
    for mod in ('cmd', 'alt', 'ctrl', 'shift', 'fn'):
        if not apps.get(i):
            modifier_subtitles[mod] = (
                'App {} not set. Use `reposettings` to set it.'.format(i))
        else:
            modifier_subtitles[mod] = 'Open in {}'.format(join_english(apps[i]))
        i += 1

    # Total number of repos
    repo_count = len(repos)

    if query:
        repos = wf.filter(query, repos,
                          lambda t: t[0],
                          min_score=30)
        log.debug('{}/{} repos matching `{}`'.format(len(repos),
                                                     repo_count,
                                                     query))

    if not repos:
        wf.add_item('No matching repos found', icon=ICON_WARNING)

    for name, path in repos:
        log.debug('`{}` @ `{}`'.format(name, path))
        subtitle = (path.replace(os.environ['HOME'], '~') +
                    '  //  Open in {}'.format(join_english(apps[1])))
        wf.add_item(name,
                    subtitle,
                    modifier_subtitles=modifier_subtitles,
                    arg=path,
                    uid=path,
                    valid=True,
                    type='file',
                    icon='icon.png')

    wf.send_feedback()
    return 0


if __name__ == '__main__':
    wf = Workflow(default_settings=DEFAULT_SETTINGS,
                  update_settings=GITHUB_UPDATE_CONF,
                  help_url=HELP_URL)
    log = wf.logger
    sys.exit(wf.run(main))
