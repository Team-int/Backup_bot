from discord.ext import commands as cmd
import traceback
import sys
from datetime import timedelta

from utils import formatter


em = formatter.embed_message


basic_formatter = {
    cmd.MissingRequiredArgument: "You forgot to define the argument **{error.param.name}**. "
                                 "Use `{ctx.config.prefix}help {ctx.command.qualified_name}` for more information.",
    cmd.NoPrivateMessage: "DM에서는 이 명령어를 사용할수가 없어요.",
    cmd.DisabledCommand: "해당 명령어가 **비활성화** 되어 있네요.",
    cmd.NotOwner: "This command can **only** be used by **the owner** of this bot."
}

ignore = [cmd.CommandNotFound, cmd.TooManyArguments]
catch_all = [cmd.CommandError]


class Errors(cmd.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cmd.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        catch_all = True

        if not isinstance(error, cmd.CommandOnCooldown):
            try:
                ctx.command.reset_cooldown(ctx)
            except AttributeError:
                pass

        for error_cls in ignore:
            if isinstance(error, error_cls):
                return

        for error_cls, format in basic_formatter.items():
            if isinstance(error, error_cls):
                await ctx.send(**em(format.format(error=error, ctx=ctx), type="error"))
                return

        if isinstance(error, cmd.BotMissingPermissions):
            await ctx.send(**em(f"봇 **권한**이 충분하지 않네요. 서버 설정 => 역할 에 가서`{', '.join(error.missing_perms)}` 를 허용하세요.", type="error"))
            return

        if isinstance(error, cmd.MissingPermissions):
            await ctx.send(**em(f"당신의 **권한**이 충분하지 않네요. 서버 설정 => 역할 에 가서`{', '.join(error.missing_perms)}`를 허용하세요.", type="error"))
            return

        if isinstance(error, cmd.CommandOnCooldown):
            await ctx.send(**ctx.em(
                f"이 명령어가 현재 **쿨 따운** 중입니다. `{str(timedelta(seconds=error.cooldown.per)).split('.')[0]}`.\n"
                f"잠시만 기다려 보실레요? `{str(timedelta(seconds=error.retry_after)).split('.')[0]}`.",
                type="error")
            )
            return

        if isinstance(error, cmd.BadUnionArgument):
            # cba
            pass

        if isinstance(error, cmd.BadArgument):
            if 'Converting to "' in str(error):
                converters = {
                    "int": "number"
                }
                conv = str(error).split('"')[1]
                parameter = str(error).split('"')[3]
                await ctx.send(**em(
                    f"The value you passed to **{parameter}** is not a valid **{converters.get(conv, conv)}**.",
                    type="error"
                ))
                return

            if '" not found' in str(error):
                conv = str(error).split(" ")[0]
                value = str(error).split('"')[1]
                await ctx.send(**em(
                    f"**No {conv} found** that fits the value `{value}`.",
                    type="error"
                ))
                return

        if catch_all:
            if isinstance(error, cmd.CommandError):
                await ctx.send(**em(str(error), type="error"))

            else:
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                error_message = traceback.format_exception(type(error), error, error.__traceback__)
                try:
                    await ctx.send(**em(error_message[:1900], type="unex_error"))

                except:
                    pass


def setup(bot):
    bot.add_cog(Errors(bot))
