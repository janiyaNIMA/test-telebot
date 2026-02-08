genaral format: /sudo [function] [-flags] [arguments]

function | flag | arguments | description
----------------------------------------
break | -a, --all | stop replying to all users. but admins can use and control the bot.
add | --admin <chat_id> | promote use to admin.
remove | --admin <chat_id> | remove admin with chat id.

send | -g, --group <group_name> -m, --message <message> | send message to all users or specific group.
send | -g, --group <group_name> | start a live relay session to a specific group.
send | -s, --stop | stop the active live relay session.

getusers | -a, --all | get all users.
getusers | -b, --banned | get banned users.
getusers | -l, --lang <language_code> | get users by language code.

mkgrp | -n, --name <group_name> | create user category for selective broadcasting.
rmgrp | -n, --name <group_name> | remove user category.

ban | - | <chat_id> | ban user from using the bot.
unban | - | <chat_id> | unban user.
setgrp | - | <chat_id> <group_name> | add user to a specific category/group.