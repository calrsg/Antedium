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
        """Handle messages to check for fixable links."""
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
        handlers = await self.find_fixable_links(message)
        if len(handlers) != 0:
            fixed = ""
            fixed_links = []
            for handler in handlers:
                current_fixed = await self.fix_message(message, handler)
                fixed_links.append(current_fixed)
            # We read links top down so default message is reversed
            fixed_links.reverse()
            for link in fixed_links:
                link.strip()
                fixed += link + "\n"
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
        """Handle reaction to delete fixed links."""
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
        """
        Toggle the link fixer globally.
        Useful for toggling partial functionality of the cog.
        """
        if self.status:
            self.status = False
            await ctx.send("Link fixer disabled globally.")
        else:
            self.status = True
            await ctx.send("Link fixer enabled globally.")

    @commands.is_owner()
    @commands.hybrid_command(name="user", with_app_command=True, description="Get stats for links fixed for a user.")
    async def user(self, ctx, user: discord.Member = None, user_id: str = None):
        """Get stats for links fixed for a user."""
        target_id = None
        if user:
            target_id = user.id
            display_name = user.display_name
        elif user_id:
            try:
                user_id = int(user_id)
            except ValueError:
                return await ctx.send("User ID must be a number.")
            target_id = user_id
            display_name = f"User ID {user_id}"
        else:
            return await ctx.send("User ID must be passed in.")

        total_count = await self.log.get_all_user_stats(target_id)
        await ctx.send(f"{total_count} links fixed for {display_name}.")

    @commands.is_owner()
    @commands.hybrid_command(name="server", with_app_command=True, description="Get stats for links fixed in a server.")
    async def server(self, ctx, server_id: str):
        """Get stats for links fixed in a server."""
        try:
            server_id = int(server_id)
        except ValueError:
            return await ctx.send("Server ID must be a number.")
        
        # Try to get server name
        server = self.bot.get_guild(server_id)
        server_name = server.name if server else f"Unknown Server"
        
        total_count = await self.log.get_all_server_stats(server_id)
        await ctx.send(f"{total_count} links fixed in {server_name}.")

    @commands.is_owner()
    @commands.hybrid_command(name="all", with_app_command=True, description="Get stats for all links fixed.")
    async def all(self, ctx):
        """Get global stats for all links fixed."""
        await ctx.defer()

        stats = await self.log.get_global_stats()
        embed = discord.Embed(title="Link Stats", color=0x1DA1F2)
        embed.add_field(name="Total Links", value=stats.get('total_links_fixed', 0), inline=False)

        # Show top servers
        top_servers = stats.get('top_servers', [])[:5]
        server_list = []
        for sid, count in top_servers:
            try:
                server_id = int(sid) if isinstance(sid, str) else sid
                
                # More thorough guild search
                server = None
                for guild in self.bot.guilds:
                    if guild.id == server_id:
                        server = guild
                        break
                
                if server:
                    server_name = server.name
                else:
                    server_name = f"Unknown Server"
                server_list.append(f"{count} : {server_name}")
            except (ValueError, TypeError):
                server_list.append(f"{count} : Invalid Server")
        
        embed.add_field(
            name="Top Servers",
            value="\n".join(server_list) or "None",
            inline=False
        )

        # Show top users
        top_users = stats.get('top_users', [])[:5]
        user_list = []
        for uid, count in top_users:
            try:
                user_id = int(uid) if isinstance(uid, str) else uid
                
                # First try bot's user cache
                user = self.bot.get_user(user_id)
                if user:
                    user_name = f"{user.display_name} (@{user.name})"
                else:
                    # Search through all guild members
                    found_member = None
                    for guild in self.bot.guilds:
                        member = guild.get_member(user_id)
                        if member:
                            found_member = member
                            break
                    
                    if found_member:
                        user_name = f"{found_member.display_name} (@{found_member.name})"
                    else:
                        user_name = f"User Not Found (ID: {user_id})"
                
                user_list.append(f"{count} : {user_name}")
            except (ValueError, TypeError):
                user_list.append(f"{count} : Invalid User ID ({uid})")
        
        embed.add_field(
            name="Top Users",
            value="\n".join(user_list) or "None",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="notifications", with_app_command=True, description="Toggle reply notifications.")
    async def notifications(self, ctx):
        """
        Toggle reply notifications for the user.
        If the user has notifications enabled, they will receive a DM when someone replies to their fixed link.
        """
        cur = await self.log.get_ignored(ctx.author.id)
        if cur is False:
            await self.log.add_ignored(ctx.author.id)
            await ctx.author.send("You will no longer receive reply notifications.")
        else:
            await self.log.remove_ignored(ctx.author.id)
            await ctx.author.send("You will now receive reply notifications.")

    async def is_intuitive_reply(self, message):
        """
        Check if the message is a reply to a bot's fixed link message.
        
        Parameters
        ----------
        message : discord.Message
            The message to check for a reply.
        
        Returns
        -------
        discord.User or False
            The user who should receive the reply notification, or False if no notification is needed."""
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

        Parameters
        ----------
        message : str
            The message content to check for fixable links.
        
        Returns
        -------
        [LinkInterface]
        A list of link handlers that can fix the links in the message.
        """
        # Iterate over handlers
        handlers = []
        for handler in self.linkHandlers:
            # Return False if any handler finds a link to ignore (assumed pre-fixed URL)
            # FIXME: Multiple links in one message may cause issues
            # Search for valid links
            for link in handler.replace:
                if link in message.content:
                    # Only add if link is not prefixed
                    if not any(x in message.content for x in handler.ignore):
                        handlers.append(handler)
        return handlers

    async def fix_message(self, message: str, handler: LinkInterface):
        """
        Fix the message content by replacing links with the handler's link format.
        
        Parameters
        ----------
        message : str
            The message content to fix.
            
        handler : LinkInterface
            The link handler to use for fixing the message.
            
        Returns
        -------
        str or False
            The fixed message content with replaced links, or False if no links were fixed.
        """
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
    """
    Background task to periodically dump link logger data and update the bot's status.
    """
    def __init__(self, linkfix):
        self.linkfix = linkfix
        self.bot = linkfix.bot

    async def run(self):
        while True:
            await asyncio.sleep(self.bot.log_timer)

            if self.bot.status_count:
                await self.bot.change_presence(activity=discord.Game(name=f"{await self.linkfix.log.get_total_fixed()} fixed embeds"))
                
            await self.linkfix.log.dump()


