
Alfred Git Repos Workflow
=========================

Browse, search and open Git repositories from within Alfred.

![][demo]


Download
--------

Get the workflow from [GitHub releases][gh-releases].

Version 2 and later are only compatible with Alfred 3. If you're still using Alfred 2, please download version 1 instead.


Usage
-----

This workflow requires some configuration before use. See [Configuration](#configuration) for details.

- `repos [<query>]` — Show a list of your Git repos filtered by `<query>`
	+ `↩` — Open selected repo in `app_default` (see [configuration](#configuration))
	+ `⌘+↩` — Open selected repo in `app_cmd` (see [configuration](#configuration))
	+ `⌥+↩` — Open selected repo in `app_alt` (requires [configuration](#configuration))
	+ `^+↩` — Open selected repo in `app_ctrl` (requires [configuration](#configuration))
	+ `⇧+↩` — Open selected repo in `app_shift` (requires [configuration](#configuration))
	+ `fn+↩` — Open selected repo in `app_fn` (requires [configuration](#configuration))
- `reposettings` — Open `settings.json` in default JSON editor
- `reposupdate` — Force workflow to update its cached list of repositories. (By default, the list will only be updated—in the background—every 3 hours.)
- `reposhelp` — Open this file in your browser


Configuration
-------------

Before you can use this workflow, you have to configure one or more folders in which the workflow should search for Git repos. The workflow uses `find` to search for `.git` directories, so you shouldn't add *huge* directory trees to it, and use the `depth` option to restrict the search depth. Typically, a `depth` of `2` will be what you want (i.e. search within subdirectories of specified directory, but no lower). Add directories to search to the `search_dir` array in `settings.json` (see below).

**Note:** After (re-)configuration, run `reposupdate` to (re-)initialise the list of repos.

The default `settings.json` file looks like this:

```json
{
  "app_default": "Finder",               // ↩ to open in this/these app(s)
  "app_cmd": "Terminal",                 // ⌘+↩ to open in this/these app(s)
  "app_alt": null,                       // ⌥+↩ to open in this/these app(s)
  "app_ctrl": null,                      // ^+↩ to open in this/these app(s)
  "app_shift": null,                     // ⇧+↩ to open in this/these app(s)
  "app_fn": null,                        // fn+↩ to open in this/these app(s)
  "global_exclude_patterns": [],         // Exclude from all searches
  "search_dirs": [
    {
      "path": "~/delete/this/example",   // Path to search. ~/ is expanded
      "depth": 2,                        // Search subdirs of `path`
      "name_for_parent": 1,              // Name Alfred entry after parent of `.git`. 2 = grandparent of `.git` etc.
      "excludes": [                      // Excludes specific to this path
        "tmp",                           // Directories named `tmp`
        "bad/smell/*"                    // Subdirs of `bad/smell` directory
      ]
    }
  ]
}
```

This is my `settings.json`:

```json
{
  "app_alt": "iTerm",
  "app_cmd": "Finder",
  "app_ctrl": "SourceTree",
  "app_default": "Sublime Text",
  "app_fn": [
    "Sublime Text",
    "Finder",
    "SourceTree",
    "iTerm"
  ],
  "app_shift": "Browser",
  "global_exclude_patterns": [],
  "search_dirs": [
    {
      "path": "~/Code"
    },
    {
      "path": "~/Sites"
    }
  ]
}
```

**Note:** If you specify `Browser`, `Safari`, `Google Chrome`, `Webkit` or `Firefox` as an application, it will be passed the remote repo URL, not the local filepath. `Browser` will open the URL in your default browser.

You can also change the default update interval (3h) in the workflow's configuration sheet in Alfred Preferences. Change the `UPDATE_EVERY_MINS` workflow variable to suit your needs.


### Search Directories ###

Each entry in the `search_dirs` list must be a mapping.

Only `path` is required. `depth` will default to `2` if not specified. `excludes` are globbing patterns, like in `.gitignore`.

`name_for_parent` defaults to `1`, which means the entry in Alfred's results should be named after the directory containing the `.git` directory. If you want Alfred to show the name of the grandparent, set `name_for_parent` to `2` etc.

This is useful if your projects are structured, for example, like this and `src` is the actual repo:

```
Code
  Project_1
    src
    other_stuff
  Project_2
    src
    other_stuff
  …
  …
```

Set `name_for_parent` to `2`, and `Project_1`, `Project_2` etc. will be shown in Alfred, not `src`, `src`, `src`…


### Open in Applications ###

The applications specified by the `app_XYZ` options are all called using `open -a AppName path/to/directory`. You can configure any application that can open a directory in this manner. Some recommendations are Sublime Text, SourceTree, GitHub or iTerm.

The meta app `Browser` will open the repo's `remote/origin` URL in your default browser. Other recognised browsers are `Safari`, `Google Chrome`, `Firefox` and `WebKit`.

**Note:** As you can see from my `settings.json`, you can also set an `app_XYZ` value to an array of applications to open the selected repo in more than one app at once:

```
…
  "app_cmd": ["Finder", "Sublime Text", "SourceTree", "iTerm"],
…
```

You can also use `→` on a result to access Alfred's default File Actions menu.


License, Thanks
---------------

This workflow is released under the [MIT Licence][mit].

It uses the [Alfred-Workflow][aw] and [docopt][docopt] libraries (both MIT Licence).

The icon is by [Jason Long][jlong], from [git-scm.com][git], released under the [Creative Commons Attribution 3.0 Unported Licence][cc].


[aw]: https://github.com/deanishe/alfred-workflow
[cc]: http://creativecommons.org/licenses/by/3.0/
[demo]: https://raw.githubusercontent.com/deanishe/alfred-repos/master/demo.gif
[docopt]: http://docopt.org/
[gh-releases]: https://github.com/deanishe/alfred-repos/releases/latest
[git]: http://git-scm.com/downloads/logos
[jlong]: http://twitter.com/jasonlong
[mit]: http://opensource.org/licenses/MIT
[packal]: http://www.packal.org/workflow/git-repos
