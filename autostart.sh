###
# window manager

xhost +local:

xmodmap -e "keycode 109 = Delete"
# map caps lock key to esc
xmodmap -e "remove lock = Caps_Lock"
xmodmap -e "keycode 0x42 = Escape"

test -f /usr/bin/autocutsel && /usr/bin/autocutsel -selection CLIPBOARD -fork
test -f /usr/bin/autocutsel && /usr/bin/autocutsel -selection PRIMARY -fork

$HOME/bin/set_random_wallpaper.zsh
$HOME/bin/touchpad auto
$HOME/bin/start.osd.server
$HOME/bin/start.osd.mail &
$HOME/bin/start.lineakd

# x-www-browser &
sudo -H -u surf /home/surf/bin/exec /usr/bin/opera &

sleep 2 
$HOME/bin/start.mail
$HOME/bin/start.loggers
$HOME/bin/start.irssi
$HOME/bin/pal_mail.zsh &

