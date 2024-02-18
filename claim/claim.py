import discord
from discord.ext import commands

from core import checks
from core.checks import PermissionLevel


class ClaimThread(commands.Cog):
    """Allows supporters to claim thread by sending claim in the thread channel"""
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        check_reply.fail_msg = 'This thread has been claimed by another user.'
        self.bot.get_command('reply').add_check(check_reply)
        self.bot.get_command('areply').add_check(check_reply)
        self.bot.get_command('fareply').add_check(check_reply)
        self.bot.get_command('freply').add_check(check_reply)

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def claimthread(self, ctx):
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread is None:
            await self.db.insert_one({'thread_id': str(ctx.thread.channel.id), 'claimers': [str(ctx.author.id)]})
            await ctx.send('**' + ctx.author.username + '** has successfully claimed this thread.')
        else:
            await ctx.send('Thread is already claimed, please use `>overclaim` to take over.')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def addclaim(self, ctx, *, member: discord.Member):
        """Adds another user to the thread claimers"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread and str(ctx.author.id) in thread['claimers']:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$addToSet': {'claimers': str(member.id)}})
            await ctx.send('Successfully added **' + member.username + '** to the claimers.')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def removeclaim(self, ctx, *, member: discord.Member):
        """Removes a user from the thread claimers"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread and str(ctx.author.id) in thread['claimers']:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$pull': {'claimers': str(member.id)}})
            await ctx.send('Successfully removed **' + member.username + '** from claimers')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def uclaim(self, ctx):
        """Removes user from the thread claimers"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$pull': {'claimers': str(ctx.author.id)}})
            await ctx.send('Successfully unclaimed this thread. Feel free to claim now.')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def transferclaim(self, ctx, *, member: discord.Member):
        """Removes all users from claimers and gives another member all control over thread"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread and str(ctx.author.id) in thread['claimers']:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$set': {'claimers': [str(member.id)]}})
            await ctx.send('Successfully transferred the thread\'s ownership to **' + member.username + '**.')
    
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def oclaim(self, ctx):
        """Removes all users from claimers and gives user all control over thread"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$set': {'claimers': [str(ctx.author.id)]}})
            await ctx.send('**' + ctx.author.username + '** has successfully overclaimed this thread.')

    
    @checks.has_permissions(PermissionLevel.MODERATOR)
    @checks.thread_only()
    @commands.command()
    async def overrideaddclaim(self, ctx, *, member: discord.Member):
        """Allow mods to bypass claim thread check in add"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$addToSet': {'claimers': str(member.id)}})
            await ctx.send('Added to claimers')

    @checks.has_permissions(PermissionLevel.MODERATOR)
    @checks.thread_only()
    @commands.command()
    async def overridereply(self, ctx, *, msg: str=""):
        """Allow mods to bypass claim thread check in reply"""
        await ctx.invoke(self.bot.get_command('reply'), msg=msg)


async def check_reply(ctx):
    thread = await ctx.bot.get_cog('ClaimThread').db.find_one({'thread_id': str(ctx.thread.channel.id)})
    if thread:
        return ctx.author.bot or str(ctx.author.id) in thread['claimers']
    return True


async def setup(bot):
    await bot.add_cog(ClaimThread(bot))
