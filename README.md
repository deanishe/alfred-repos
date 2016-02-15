
# Alfred Git Repos Workflow #

Browse, search and open Git repositories from within Alfred.

![](https://raw.githubusercontent.com/deanishe/alfred-repos/master/demo.gif "")

## Download ##

Get the workflow from [GitHub](https://github.com/deanishe/alfred-repos/releases/latest) or [Packal](http://www.packal.org/workflow/git-repos).

## Usage ##

This workflow requires some configuration before use. See [Configuration](#configuration) for details.

- `repos [<query>]` — Show a list of your Git repos filtered by `<query>`
	+ `↩` — Open selected repo in `app_1` (see [configuration](#configuration))
	+ `⌘+↩` — Open selected repo in `app_2` (see [configuration](#configuration))
	+ `⌥+↩` — Open selected repo in `app_3` (requires [configuration](#configuration))
	+ `^+↩` — Open selected repo in `app_4` (requires [configuration](#configuration))
	+ `⇧+↩` — Open selected repo in `app_5` (requires [configuration](#configuration))
	+ `fn+↩` — Open selected repo in `app_6` (requires [configuration](#configuration))
- `reposettings` — Open `settings.json` in default JSON editor
- `reposupdate` — Force workflow to update its cached list of repositories. (By default, the list will only be updated—in the background—every 3 hours.)
- `reposhelp` — Open this file in your browser

## Configuration ##

Before you can use this workflow, you have to configure one or more folders in which the workflow should search for Git repos. The workflow uses `find` to search for `.git` directories, so you shouldn't add *huge* directory trees to it, and use the `depth` option to restrict the search depth. Typically, a `depth` of `2` will be what you want (i.e. search within subdirectories of specified directory, but no lower). Add directories to search to the `search_dir` array in `settings.json` (see below).

**Note:** After (re-)configuration, run `reposupdate` to (re-)initialise the list of repos.

The default `settings.json` file looks like this:

```
{
  "app_1": "Finder",             // ↩ to open in this/these app(s)
  "app_2": "Terminal",           // ⌘+↩ to open in this/these app(s)
  "app_3": null,                 // ⌥+↩ to open in this/these app(s)
  "app_4": null,                 // ^+↩ to open in this/these app(s)
  "app_5": null,                 // ⇧+↩ to open in this/these app(s)
  "app_6": null,                 // fn+↩ to open in this/these app(s)
  "global_exclude_patterns": [],      // Exclude from all searches
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

```
{
  "app_1": "Finder",
  "app_2": ["Finder", "Sublime Text", "SourceTree", "iTerm"],
  "app_3": "Sublime Text",
  "app_4": "SourceTree",
  "app_5": "iTerm",
  "app_6": "GitHub",
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

**Note:** If you specify `Safari`, `Google Chrome` or `Firefox` as an application, it will be passed the remote repo URL, not the local filepath.

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

The applications specified by the `app_N` options are all called using `open -a AppName path/to/directory`. You can configure any application that can open a directory in this manner. Some recommendations are Sublime Text, SourceTree, GitHub or iTerm.

**Note:** As you can see from my `settings.json`, you can also set an `app_N` value to a list of applications to open the selected repo in more than one app at once:

```
…
  "app_2": ["Finder", "Sublime Text", "SourceTree", "iTerm"],
…
```

You can also use `→` on a result to access Alfred's default File Actions menu.

## License, Thanks ##

This workflow is released under the [MIT Licence](http://opensource.org/licenses/MIT).

It uses the [Alfred-Workflow](https://github.com/deanishe/alfred-workflow) and [docopt](http://docopt.org/) libraries (both MIT Licence).

The icon is by [Jason Long](http://twitter.com/jasonlong), from [git-scm.com](http://git-scm.com/downloads/logos), released under the [Creative Commons Attribution 3.0 Unported Licence](http://creativecommons.org/licenses/by/3.0/).
