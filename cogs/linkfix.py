import asyncio

import discord
from discord.ext import commands
import re
from linkhandlers.linkinterface import LinkInterface
from linkhandlers.tiktoklink import TiktokLink
from linkhandlers.twitterlink import TwitterLink
from linkhandlers.instagramlink import InstagramLink
from linklogging.linklogger import LinkLogger

class LinkFix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status = True
        self.log = LinkLogger()
        self.bot.loop.create_task(self.init_log())
        self.linkHandlers = [TwitterLink(), InstagramLink(), TiktokLink()]

    async def init_log(self):
        await self.log.load()

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore if function turned off or message author is a bot
        if message.author.bot or not self.status:
            return

        # Intuitive replies
        intuitive_reply = await self.is_intuitive_reply(message)
        if not intuitive_reply:
            pass
        else:
            await intuitive_reply.send(
                f"{message.author.display_name} replied to your link in {message.guild.name}: "
                f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}\n"
                f"If you want to disable these reminders, use the command /remind.")

        # Check for potential fixable links
        handler = await self.find_fixable_links(message)
        if handler != False:
            fixed = await self.fix_message(message, handler)
            try:
                await asyncio.sleep(0.4)
                await message.edit(suppress=True)
            except discord.Forbidden:
                fixed = ":prohibited: I don't have permission to supress embeds in the message I am replying to, please give me the `Manage Messages` permission to avoid clutter.\n"
            try:
                new_msg = await message.reply(fixed, mention_author=False)
                await new_msg.add_reaction("❌")
            except discord.Forbidden:
                return
            
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        # If replied to message is by the reaction user, and if the reaction emoji is for deleting
        try:
            target = reaction.message.reference.resolved.author.id
        except AttributeError:
            return
        if target == user.id and reaction.emoji == "❌":
            await reaction.message.delete()
            await user.send(f"You deleted a link I fixed in {reaction.message.guild.name}.")

    @commands.is_owner()
    @commands.hybrid_command(name="toggle", with_app_command=True, description="Toggle link fixer.")
    async def toggle(self, ctx):
        if self.status:
            self.status = False
            await ctx.send("Link fixer disabled globally.")
        else:
            self.status = True
            await ctx.send("Link fixer enabled globally.")

    @commands.is_owner()
    @commands.hybrid_command(name="user", with_app_command=True, description="Get stats for links fixed for a user.")
    async def user(self, ctx, user: discord.Member = None, user_id: int = None):
        # Use the logger's get_user_stats method
        target_id = None
        if user:
            target_id = user.id
            display_name = user.display_name
        elif user_id:
            target_id = user_id
            display_name = f"User ID {user_id}"
        else:
            return await ctx.send("User ID must be passed in.")

        total_count = await self.log.get_all_user_stats(target_id)
        await ctx.send(f"{total_count} links fixed for {display_name}.")

    @commands.is_owner()
    @commands.hybrid_command(name="server", with_app_command=True, description="Get stats for links fixed in a server.")
    async def server(self, ctx, server_id: int):
        # Use the logger's get_server_stats method
        total_count = await self.log.get_all_server_stats(server_id)
        await ctx.send(f"{total_count} links fixed in server matching ID {server_id}.")

    @commands.is_owner()
    @commands.hybrid_command(name="all", with_app_command=True, description="Get stats for all links fixed.")
    async def all(self, ctx):
        # Use the logger's get_global_stats method
        stats = await self.log.get_global_stats()
        embed = discord.Embed(title="Link Fix Stats", color=0x1DA1F2)
        embed.add_field(name="Total Links Fixed", value=stats['total_links_fixed'], inline=False)

        # Show top servers
        top_servers = stats.get('top_servers', [])[:5]
        embed.add_field(
            name="Top Servers Fixed",
            value="\n".join([f"{count} : Server ID {sid}" for sid, count in top_servers]) or "None",
            inline=False
        )

        # Show top users
        top_users = stats.get('top_users', [])[:5]
        embed.add_field(
            name="Top Users Fixed",
            value="\n".join([f"{count} : User ID {uid}" for uid, count in top_users]) or "None",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="remind", with_app_command=True, description="Toggle ignoring reply reminders.")
    async def remind(self, ctx):
        cur = await self.log.get_ignored(ctx.author.id)
        if cur is False:
            await self.log.add_ignored(ctx.author.id)
            await ctx.author.send("You will no longer receive reply reminders.")
        else:
            await self.log.remove_ignored(ctx.author.id)
            await ctx.author.send("You will now receive reply reminders.")

    async def is_intuitive_reply(self, message):
        # Ignore bot messages
        if message.author.bot:
            return False
        # Check if the replied to message is context message
        if message.reference and message.reference.resolved:
            search = message.reference.resolved
            # If it's not a bot message, return False
            if not search.author.bot:
                return False
            # If the replied to message is not replying to another message, return False
            if not search.reference:
                return False
            # Check if the bot message has any fixed link formats from any handlers
            is_fixed = any(link in search.content for link in (handler.link for handler in self.linkHandlers))
            # Handle bot not being able to load resolved reference, force load message that we know exists
            target = await search.channel.fetch_message(search.reference.message_id)
            if target and is_fixed != -1:
                user = await self.bot.fetch_user(int(target.author.id))
                # Check if the user has disabled reminders, and if the user is not replying to their own fixed tweet
                if not await self.log.get_ignored(user.id) and user.id != message.author.id:
                    return user
        return False

    async def find_fixable_links(self, message: str):
        """
        Preliminary check for links that may match link handlers.
        """
        # Iterate over handlers
        for handler in self.linkHandlers:
            # Return False if any handler finds a link to ignore (assumed pre-fixed URL)
            # FIXME: Multiple links in one message may cause issues
            for link in handler.ignore:
                if link in message.content:
                    return False
            # Search for valid links
            for link in handler.replace:
                if link in message.content:
                    return handler
        # False if no valid links found
        return False

    async def fix_message(self, message: str, handler: LinkInterface):
        print(message.content)
        new_content = ""
        # Use handler regex to identify links
        urls = re.findall(handler.pattern, message.content)
        new_urls = []
        # Count of links fixed for logging (deprecate in future?)
        log_count = 0
        for url in urls:
            # Check if the selected URL has spoiler tags
            spoiler = await spoiler_check(message.content)
            # Rebuild the URL from the regex match
            # FIXME: This probably breaks with diff formats eg. Insta TikTok
            new_url = ""
            for i in url:
                print(i)
                new_url += i
            
            for link in handler.replace:
                # If the link is in the URL and not in the ignore list, replace
                if link in new_url and not any([x in url for x in handler.ignore]):
                    new_url = new_url.replace(link, handler.link)
                    # Remove www. if present
                    new_url = new_url.replace("www.", "")
                    # Add spoiler tags for links originally spoilered
                    if spoiler:
                        new_url = "||" + new_url + "||"
                    # Update log count
                    if handler.status is not None:
                        new_url += "\n" + handler.status
                    log_count += 1
                    # Append
                    new_content += f"{new_url}\n"
                    new_urls.append(new_url)

        # Return if any links were fixed
        if len(urls) > 0:
            await self.log.update(message.guild.id, message.author.id, log_count, handler.name)
            return new_content
        
        return False

async def spoiler_check(message):
    """
    Check if the message contains spoiler tags.
    
    
    Parameters
    ----------
    message : str
        The message content to check for spoiler tags.
    
    Returns
    -------
    bool
        True if the message contains spoiler tags, False otherwise.
    """
    split = message.split("||")
    if len(split) >= 2:
        return True
    return False

async def setup(bot):
    linkfix = LinkFix(bot)
    await bot.add_cog(linkfix)
    bg = BackgroundTimer(linkfix)
    bot.loop.create_task(bg.run())

class BackgroundTimer:
    def __init__(self, linkfix):
        self.linkfix = linkfix
        self.bot = linkfix.bot

    async def run(self):
        while True:
            await asyncio.sleep(60)
            await self.linkfix.log.dump()

