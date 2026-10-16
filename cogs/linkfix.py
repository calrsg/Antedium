import asyncio

import discord
from discord.ext import commands
from linkhandlers.rewrite import build_reply, default_handlers, rewrite
from linklogging.linklogger import LinkLogger


class LinkFix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status = True
        self.log = LinkLogger()
        self.user_cache = {}  # New user cache dictionary
        self.bot.loop.create_task(self.init_log())
        self.linkHandlers = default_handlers()

    async def init_log(self):
        await self.log.load()
        await self.cache_users()

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
                f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}\n")

        # Check for fixable links
        results = await rewrite(message.content, self.linkHandlers)
        # Every handler may have failed to resolve a usable link
        if len(results) != 0:
            print(message.content)
            for result in results:
                await self.log.update(message.guild.id, message.author.id, len(result.links), result.handler.name)
            fixed = build_reply(results)
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
    @commands.command(name="toggle", description="Toggle link fixer.")
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
    @commands.command(name="user", description="Get stats for links fixed for a user.")
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
    @commands.command(name="server", description="Get stats for links fixed in a server.")
    async def server(self, ctx, server_id: str):
        """Get stats for links fixed in a server."""
        try:
            server_id = int(server_id)
        except ValueError:
            return await ctx.send("Server ID must be a number.")
        
        # Try to get server name
        server = self.bot.get_guild(server_id)
        server_name = server.name if server else "Unknown Server"
        
        total_count = await self.log.get_all_server_stats(server_id)
        await ctx.send(f"{total_count} links fixed in {server_name}.")

    @commands.is_owner()
    @commands.command(name="all", description="Get stats for all links fixed.")
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
                server = self.bot.get_guild(server_id)
                server_name = server.name if server else "Unknown Server"
                server_list.append(f"{count} : {server_name}")
            except (ValueError, TypeError):
                server_list.append(f"{count} : Invalid Server")
        
        embed.add_field(
            name="Top Servers",
            value="\n".join(server_list) or "None",
            inline=False
        )

        # Show top users using the cache
        top_users = stats.get('top_users', [])[:5]
        user_list = []
        for uid, count in top_users:
            try:
                user_id = int(uid) if isinstance(uid, str) else uid
                
                # Use the user cache
                if user_id in self.user_cache:
                    user_info = self.user_cache[user_id]
                    user_name = f"{user_info['display_name']} (@{user_info['name']})"
                else:
                    # If not in cache, try to fetch directly
                    try:
                        user = await self.bot.fetch_user(user_id)
                        user_name = f"{user.display_name} (@{user.name})"
                        # Add to cache for future use
                        self.user_cache[user_id] = {
                            "display_name": user.display_name,
                            "name": user.name
                        }
                    except discord.HTTPException:
                        user_name = f"User ID: {user_id}"
            
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

    async def cache_users(self):
        """Cache users from the log data."""
        print("Caching users from log data...")
        # Get all unique user IDs from the log data
        user_ids = set()
        for handler_name in [handler.name for handler in self.linkHandlers]:
            if handler_name in self.log.data:
                users = self.log.data[handler_name].get("users", {})
                user_ids.update(users.keys())
    
        # Fetch user information for each ID
        cached_count = 0
        for user_id in user_ids:
            try:
                user_id = int(user_id)
                # Try to fetch user (works without members intent)
                try:
                    user = await self.bot.fetch_user(user_id)
                    self.user_cache[user_id] = {
                        "display_name": user.display_name,
                        "name": user.name
                    }
                    cached_count += 1
                except discord.NotFound:
                    # User not found, add a placeholder
                    self.user_cache[user_id] = {
                        "display_name": "Unknown User",
                        "name": f"{user_id}"
                    }
            except Exception as e:
                print(f"Error caching user {user_id}: {e}")
    
        print(f"Successfully cached {cached_count} users.")

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


