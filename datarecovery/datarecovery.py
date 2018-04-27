"""DataRecovery, a cog for recovering various data from channel history."""

import re
import logging
from typing import Set

import discord
from discord.ext import commands
from redbot.core import checks, bank

LOGGER = logging.getLogger('red.datarecovery')


# noinspection PyIncorrectDocstring
class DataRecovery:
    """Recover data from channel history."""

    @commands.group()
    @checks.is_owner()
    async def recover(self, ctx: commands.Context):
        """Recover data from this channel."""
        if not ctx.invoked_subcommand:
            await ctx.send_help()

    @recover.command()
    @commands.guild_only()
    async def economy(self, ctx: commands.Context,
                      num_accounts: int = 100,
                      num_messages: int = 1000,
                      bot_user: discord.Member = None):
        """Recover economy data.

        Warning
        -------
        This command can take quite a long time to complete.

        Arguments
        ---------
        num_accounts : Optional[int]
            Number of accounts to recover. Defaults to 100. If there is not
            enough data in the channel to recover this many accounts, it will
            recover as much as it can.
        num_messages : Optional[int]
            Number of messages to read through in the channel history. Defaults
            to 1000. The higher the number of messages, the longer this operation
            will take.
        bot_user : Optional[discord.Member]
            The bot who ran the slot machines. Defaults to me.

        """
        first: discord.Message = await ctx.send('*Recovering economy data, please standby...*')
        channel: discord.TextChannel = ctx.channel
        members_recovered: Set[discord.Member] = set()
        pattern = re.compile(r'\d+ → (\d+)!')
        if bot_user is None:
            bot_user: discord.Member = ctx.guild.me
        # noinspection PyUnusedLocal
        message: discord.Message
        async with ctx.typing():
            async for message in channel.history(limit=num_messages):
                if message.author != bot_user:
                    continue
                if not message.mentions:
                    continue
                gambler: discord.Member = message.mentions[0]
                if gambler in members_recovered:
                    continue
                content: str = message.content
                last_line = content.split('\n')[-1]
                balance_str = pattern.search(last_line)
                if balance_str and message.mentions:
                    balance = int(balance_str.group(1))
                    await bank.set_balance(gambler, balance)
                    LOGGER.debug(f'Set {gambler}\'s balance to {balance}')
                    members_recovered.add(gambler)
                    if len(members_recovered) >= num_accounts:
                        break
        LOGGER.info(f'Performed data recovery in {channel}, and set the balance of '
                    f'{len(members_recovered)} members.')
        await first.delete()
        await ctx.send(f'Done. Set the balance of {len(members_recovered)} members.')
