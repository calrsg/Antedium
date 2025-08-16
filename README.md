<h1 align="center">Antedium</h1>

<p align="center">
  Remove the tedium of using Discord to chat
</p>

## About

Antedium is a Discord chat bot designed to remove tedious tasks caused by the arguably bloated platform, removing the need for users to do things such as fix popular social media links that don't embed properly by default.

## Installation

1) Download the codebase as a .zip file
2) Extract the contents to a location you'd like the bot to run
3) Create a Python venv inside of the new folder (use google for this c: )
4) Run main.py, which will generate a config.json file and immediately close
5) Enter your Discord bot token into the config.json file as bot_token
6) Run the bot again, which will now generate a log.json file

## Permissions

Antedium requires the following permissions on a per server basis:
- Send messages (for posting fixed links)
- Embed messages (for embedding fixed links)
- Manage messages (to delete the original poster's message after embedding)
- Read Message History (for intuitive replies)

Antedium requires the following permissions on a bot level:
- Privileged message content intent (reading all new messages)

## Usage

Once running, Antedium is a background process outside of bot owner commands. All new messages are parsed and checked for potential links, and if a match is found the fixed link is posted.

Any user can reply to a message the bot has posted, and the bot will notify the original person that posted the link as an intimediary for replying.
- This functionality can be turned off on a per-user basis with the /notifications command

The bot owner can use /all, /server <id>, and /user <id> to view the usage stats of the bot in various contexts. The information stored is highly limited and thus advanced searches (eg. instagram posts fixed x user in y server) cannot be executed. Searches such as (twitter posts by x user) or (instagram posts in y server) can be found, but the commands for these searches do not exist.

## User Privacy

**Antedium does not store the contents of any messages.** The only persistent storage used is for logging the amount of messages that have been modified, the users that post them, and the servers they are posted in. This is represented in an array of link types (Twitter, Instagram, etc), which each contain a list of users and servers paired with a number that represents how many times that type of social media link has been modified inside which was posted by the specified user or in the specified server.

Antedium will never store the contents of messages or any type of user information outside of the bare minimum required to collect basic usage data (see how much the bot is being used).

Running Antedium locally will result in local logs being created which are not shared online and can only be accessed by the host of the bot.

## Contribute

The easiest way to contribute is through adding link handlers, which are used to identify and process different social media links. 

* Using the interface in _linkhandlers/linkinterface.py_, new link handlers can be created by implementing the abstract properties.
* New link handlers need to be added to _cogs/linkfix.py_ to be used.

## Licence

This software is licensed under the [GNU General Public Licence 3.0](LICENCE) licence.
