from typing import Optional, Set

from datetime import datetime as dt
from nextcord.ext import commands
from nextcord.abc import GuildChannel
from nextcord.ui import Button, View
from nextcord import Client, Interaction, SlashOption, ChannelType, ButtonStyle
from nextcord import Embed
import nextcord
import os


class HelpDropdown(nextcord.ui.Select):
    def __init__(self, help_command: "MyHelpCommand", options: list[nextcord.SelectOption]):
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)
        self._help_command = help_command

    async def callback(self, interaction: nextcord.Interaction):
        embed = (
            await self._help_command.cog_help_embed(self._help_command.context.bot.get_cog(self.values[0]))
            if self.values[0] != self.options[0].value
            else await self._help_command.bot_help_embed(self._help_command.get_bot_mapping())
        )
        await interaction.response.edit_message(embed=embed)


class HelpView(nextcord.ui.View):
    def __init__(self, help_command: "MyHelpCommand", options: list[nextcord.SelectOption], *,
                 timeout: Optional[float] = 120.0):
        super().__init__(timeout=timeout)
        button_url = Button(label = "Support Server", url = "https://discord.gg/AtSxMh7YAc")
        self.add_item(HelpDropdown(help_command, options))
        self.add_item(button_url)
        self._help_command = help_command

    async def on_timeout(self):
        # remove dropdown from message on timeout
        self.clear_items()
        await self._help_command.response.edit(view=self)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        return self._help_command.context.author == interaction.user

    @nextcord.ui.button(
        label = "",
        emoji = "🗑️",
        style = ButtonStyle.red
    )
    async def delete_button(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await self.on_timeout()


class MyHelpCommand(commands.MinimalHelpCommand):
    def get_command_signature(self, command):
        return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}"

    async def _cog_select_options(self) -> list[nextcord.SelectOption]:
        options: list[nextcord.SelectOption] = []
        options.append(nextcord.SelectOption(
            label="Home",
            emoji="🏠",
            description="Go back to the main menu.",
        ))

        for cog, command_set in self.get_bot_mapping().items():
            filtered = await self.filter_commands(command_set, sort=True)
            if not filtered:
                continue
            emoji = getattr(cog, "COG_EMOJI", None)
            options.append(nextcord.SelectOption(
                label=cog.qualified_name if cog else "No Category",
                emoji=emoji if cog else "❎",
                description=cog.description[:100] if cog and cog.description else None
            ))

        return options

    async def _help_embed(
            self, title: str, description: Optional[str] = None, mapping: Optional[str] = None,
            command_set: Optional[Set[commands.Command]] = None, set_author: bool = False
    ) -> Embed:
        embed = Embed(title=title, colour=nextcord.Colour.orange())
        embed.set_footer(text = f"Revoked by {self.context.author.name}", icon_url = self.context.author.avatar.url)
        if description:
            embed.description = description
        if set_author:
            avatar = self.context.bot.user.avatar or self.context.bot.user.default_avatar
            embed.set_author(name=self.context.bot.user.name, icon_url=avatar.url)
        if command_set:
            # show Help about all commands in the set
            filtered = await self.filter_commands(command_set, sort=True)
            for command in filtered:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command.short_doc or "...",
                    inline=False
                )
        elif mapping:
            # add a short description of commands in each cog
            for cog, command_set in mapping.items():
                filtered = await self.filter_commands(command_set, sort=True)
                if not filtered:
                    continue
                name = f"_{cog.qualified_name}_" if cog else "No category"
                emoji = getattr(cog, "COG_EMOJI", None)
                cog_label = f"{emoji} {name}" if emoji else name
                # \u2002 is an en-space
                cmd_list = "\u2002".join(
                    f"`{self.context.clean_prefix}{cmd.name}`" for cmd in filtered
                )
                value = (
                    f"_{cog.description}_\n{cmd_list}"
                    if cog and cog.description
                    else cmd_list
                )
                embed.add_field(name=cog_label, value=value)
        return embed

    async def bot_help_embed(self, mapping: dict) -> Embed:
        return await self._help_embed(
            title="Bot Help Command",
            description=self.context.bot.description,
            mapping=mapping,
            set_author=True,
        )

    async def send_bot_help(self, mapping: dict):
        embed = await self.bot_help_embed(mapping)
        cogs_folder = os.listdir("./cogs")
        cogs = []
        for i in cogs_folder:
            if i == "botconfig":
                break
            cogs.append(i)
        embed.set_thumbnail(url = self.context.bot.user.avatar.url)
        em_description = f":gear: **Commands:** `{len(self.context.bot.commands)}`\n:open_file_folder: **Cogs:** ``{len(cogs_folder)-1}``\n:projector: **Guilds:** ``{len(self.context.bot.guilds)}`` _({self.context.bot.config.config('prefix')}listguilds)_"
        em = Embed(title = "Information:", description=em_description, colour=nextcord.Colour.orange(), timestamp=dt.utcnow())
        #embed.add_field(name="Information:", value = f":gear: Commands: `{len(self.context.bot.commands)}`\n:open_file_folder: Cogs: ``{len(cogs_folder)-1}``\n:projector: Guilds: ``{len(self.context.bot.guilds)}``")
        options = await self._cog_select_options()
        embeds = [embed, em]
        self.response = await self.get_destination().send(embeds=embeds, view=HelpView(self, options))

    async def send_command_help(self, command: commands.Command):
        emoji = getattr(command.cog, "COG_EMOJI", None)
        embed = await self._help_embed(
            title=f"{emoji} _{command.qualified_name}_" if emoji else command.qualified_name,
            description=command.help,
            command_set=command.commands if isinstance(command, commands.Group) else None
        )
        
        await self.get_destination().send(embed=embed)

    async def cog_help_embed(self, cog: Optional[commands.Cog]) -> Embed:
        if cog is None:
            return await self._help_embed(
                title=f"_No category_",
                command_set=self.get_bot_mapping()[None]
            )
        emoji = getattr(cog, "COG_EMOJI", None)
        return await self._help_embed(
            title=f"{emoji} _{cog.qualified_name}_" if emoji else cog.qualified_name,
            description=cog.description,
            command_set=cog.get_commands()
        )

    async def send_cog_help(self, cog: commands.Cog):
        embed = await self.cog_help_embed(cog)
        await self.get_destination().send(embed=embed)

    # Use the same function as command Help for group Help
    send_group_help = send_command_help
