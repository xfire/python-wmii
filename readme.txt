python-wmii v0.4
================
configure and script the wmii window manager the python way

Copyright (C) 2007 Rico Schiekel (fire at downgra dot de)


license
-------
GPL


requirements
------------
   - python 2.4 or greater
   - wmii 3.6-rc2 or greater


install
-------
just extract the contents of the directory from the source archive to 
your wmii configuation directory (e.g. $HOME/.wmii-3.5).


configuration
-------------
using this scripts, you configure and script wmii complete in python. normal
configuration tasks don't require much python knowledge.

I tried to follow 2 principles

   - DRY don't repeat yourself
   - KISS keep it sweet and simple (mostly for the user)

### default key bindings ###
    Mod4-1..9               switch to view (1..9)
    Mod4-Shift-1..9         add current client to view
    Mod4-Control-1..9       set current client to view

    Mod4-F1..F4             switch to names views (mail, browser, irssi, logs)
    Mod4-Shift-F1..F4       add current client to view
    Mod4-Control-F1..F4     set current client to view

    Mod4-Shift-Up/k         focus a window above the one current focused
    Mod4-Shift-Down/j       focus a window below the one current focused
    Mod4-Shift-Left/h       focus a window left the one current focused
    Mod4-Shift-Right/l      focus a window right the one current focused

    Mod4-Control-Up/k       move the current window up
    Mod4-Control-Down/j     move the current window down
    Mod4-Control-Left/h     move the current window left
    Mod4-Control-Right/l    move the current window right

    Mod4-Right              switch to the previous view in the list
    Mod4-Left               switch to the next view in the list

    Mod4-Space              jump to scratchpad or back from scratchpad
    Mod4-Shift-Space        add current client to scratchpad
    Mod4-Control-Space      set current client to scratchpad

    Mod4-f                  toggle between managed and floating layer
    Mod4-Shift-f            move to managed or floating layer

    Mod4-Shift-t            prompt for tag to add it to current client
    Mod4-Control-t          prompt for tag to set it to current client

    Mod4-Shift-u            remove current client from view
    Mod4-Control-u          remove all other tags from current client except current view

    Mod4-s                  switch to stacked column mode
    Mod4-d                  switch to default column mode
    Mod4-m                  switch to max column mode

    Mod4-Control-c          kill current client

    Mod4-Return             start an terminal
    Mod4-Shift-Return       start an root terminal
    Mod4-F12                lock screen using slock

    Mod4-p                  ask for an application and execute it
    Mod4-a                  ask for an action and execute it

### basic configuration ###
most of the configuration (except event handling) is done by editing the
file `config.py`. there you set colors, fonts, tag rules and col rules. it's
mostly self-explanatory.

#### tag mapping ####
there is a special feature called tag mapping, which maps real tag names to
an display name. this means, the real name of the tag is e.g. `02_browser`,
but displayed in your tag list is only `browser`. this is very usefull, if
you would enforce special sorting of the tags.
e.g.

    without tag mapping: browser, irssi, mail, ...

    with tag mapping: mail, browser, irssi, ...
    using these real tag names: 01_mail, 02_browser, 03_irssi, ...

all event handler expect to get real tag names. so use the functions

    t2d(tagname) - return the display name for the given tag
    d2t(displayname) - return the tag name for the given display name

to convert your input correctly.

### event mapping ###
event mappings are defined in the file `events.py`.
there is an array, `EVENTS`, which can be defined and extended using the
`patterns` function. this function take as much as desired tuples as parameters.
each tuple must have first the regex to match or a callable object which returns 
the regex. the second object in the tuple must be the event handler.
at least there can be one dictionary with parameters for the event handler.
e.g

    EVENTS += patterns(
        (r'REGEX', my_handler),
        (MKey('a'), other_handler, dict(param_1 = 1000, param_2 = 'foo')),
    )

the return value of the `patterns` function can easily added to the EVENTS array.

event handler for keys must be created using `Key` and `MKey`, to register the
keys correctly in wmii.
`MKey` is an enhancement which register an event handler for MODKEY-Key.

to get an idea, best take a look in the provided `events.py`.

### event handler ###
an event handler is a function or an callable object, which receive at least
one parameter.
e.g.

    def my_handler(event, myparam):
        print 'received event: %s' % event

    class other_handler(object):
        def __init__(self, myparam):
            self.__myparam = myparam
        def __call__(self, event):
            print 'other_handler: %s - %s' % (event, self.__myparam)

    EVENTS += patterns(
        (r'^.*$', my_handler()),
        (r'^.*$', other_handler('foo')),
    )

if you want to write your own event handlers, best look into 
`utils/event_handler.py`.

#### default event handlers ####
    view:               switch to a view.
    next_view:          switch to next view. (excluding scratchpad)
    prev_view:          switch to previous view. (excluding scratchpad)
    add_tag:            add tag to current client. other tag settings are 
                        preserved.
    set_tag:            set tag to current client. other tag settings are 
                        overwritten.
    remove_tag:         remove tag from current client.
    select:             focus client in given direction. (direction will 
                        autodetect h/j/k/l/up/down/left/right on 
                        specified key)
    SelectSet:          define all four directions for `select`
    send:               send client to given direction. (direction will 
                        autodetect h/j/k/l/up/down/left/right on 
                        specified key)
    SendSet:            define all four directions for `send`
    colmode:            set column mode (default, max, stacked).
    toggle:             toggle layer managed - floating.
    send_toggle:        send current client to mangaged or floating.
    toggle_scratchpad:  warp to scratch pad or back to previous view.
    kill:               kill current client.
    quit:               quit wmii.
    execute:            execute cmd. if cmd is callable, first call cmd 
                        to get application path.
    fwrap:              warp calls to functions with arguments. both 
                        unnamed and named arguments are supported.
    call:               use callable event_source object to find proper 
                        event in event map.
    call_dmenu:         simple wrapper for easier menu generation.
    dmenu:              use dmenu to get an item from a list.
    tag_create:         add left bar entry on tag creation.
    tag_destroy:        destroy left bar entry on tag deletion.
    tag_focus:          set bar focus colors if a tag is focused.
    tag_unfocus:        set bar normal colors if a tag is unfocused.

#### default generators ####
    application_generator:  generate list of applications available in $PATH
    tag_generator:          generate list of available tags

### status bar ###
the statusbar reads plugins from `statusbar` subdirectory and call periodical
the `update()` function, which every statusbar plugin must 
implement.
each plugin must implement an `interval()` function, which return the interval
in seconds, in which the `update()` function is called.

the return value of the `update()` function can be `None`, indicating that no 
update should be done, or it must be an tuple containing the color and the 
string to display.

sorting is achieved by using the plugins filename. so `66_load.py` will be
displayed left of `77_cpu.py`, and so on.


code
----
you can check out the current developer version using 
[mercurial](http://www.selenic.com/mercurial/).

    hg clone http://downgra.de/hg/python-wmii

if you want to send me your ideas and changes, append the following steps:

   1. configure mercurial with your name and email address
      (<http://hgbook.red-bean.com/hgbookch2.html#x6-400002.7>)
   2. `hg clone http://downgra.de/hg/python-wmii`
   3. apply your changes
   4. commit your changes (goto step 3 if necessary)
   5. use patchbombs `hg email` to send the changes to <mailto:wmii@downgra.de>
      (`hg email -a -f <your@mail.addr> -t wmii@downgra.de`)

changelog
---------
please take a look [here](http://downgra.de/hg/python-wmii)

