"""DataRecovery, a cog for recovering various data from channel history."""

import re
import logging
from collections import defaultdict
from datetime import datetime
from typing import Set, DefaultDict

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
        payday_re = re.compile(r'<@!?\d+> Here, take some credits. Enjoy! \(\+(\d+) credits!\)')
        slot_re = re.compile(r'\d+ → (\d+)!')
        balance_re = re.compile(r'<@!?\d+> Your balance is: (\d+)')
        cumulative_balances: DefaultDict[discord.Member, int] = defaultdict(lambda: 0)
        if bot_user is None:
            bot_user: discord.Member = ctx.guild.me
        # noinspection PyUnusedLocal
        message: discord.Message
        last_timestamp: datetime
        async with ctx.typing():
            async for message in channel.history(limit=num_messages):
                if message.author != bot_user:
                    continue
                content: str = message.content

                if not message.mentions:
                    continue

                gambler: discord.Member = message.mentions[0]
                if gambler in members_recovered:
                    continue

                payday_match = payday_re.search(content)
                if payday_match:
                    amount_paid = int(payday_match.group(1))
                    cumulative_balances[gambler] += amount_paid
                    LOGGER.debug(f'Added {amount_paid} to {gambler}\'s cumulative balance '
                                 f'(Now {cumulative_balances[gambler]}).')
                    last_timestamp = message.created_at
                    continue

                balance_match = balance_re.search(content)
                last_line = content.split('\n')[-1]
                slot_match = slot_re.search(last_line)
                if slot_match or balance_match:
                    if slot_match:
                        balance = int(slot_match.group(1)) + cumulative_balances[gambler]
                    else:
                        balance = int(balance_match.group(1)) + cumulative_balances[gambler]
                    await bank.set_balance(gambler, balance)
                    del cumulative_balances[gambler]
                    LOGGER.debug(f'Set {gambler}\'s balance to {balance}')
                    members_recovered.add(gambler)
                    last_timestamp = message.created_at
                    if len(members_recovered) >= num_accounts:
                        break
        last_timestamp = last_timestamp.strftime('%Y-%m-%d')
        LOGGER.debug('Now setting cumulative balances...')
        for gambler, balance in cumulative_balances.items():
            await bank.set_balance(gambler, balance)
            LOGGER.debug(f'Set {gambler}\'s balance to {balance}')

        LOGGER.info(f'Performed data recovery in {channel}, and set the balance of '
                    f'{len(members_recovered)} members. Data was recovered from messages '
                    f'dating back to {last_timestamp}.')
        await first.delete()
        await ctx.send(f'Done. Set the balance of {len(members_recovered)} members. '
                       f'Data was recovered from messages dating back to {last_timestamp}.')


'''Copyright (c) 2017, 2018 Tobotimus

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
