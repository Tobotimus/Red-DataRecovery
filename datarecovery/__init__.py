"""DataRecovery, a cog for recovering various data from channel history."""

from .datarecovery import DataRecovery
from redbot.core.bot import Red

def setup(bot: Red):
    bot.add_cog(DataRecovery())
