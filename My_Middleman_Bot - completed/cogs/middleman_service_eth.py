import discord
from discord.ext import commands
from discord.ui import Button, View

class RoleSelectionETHView(View):
    def __init__(self, last_embed_message, bot):
        super().__init__(timeout=None)
        self.last_embed_message = last_embed_message
        self.sending_user = None
        self.receiving_user = None
        self.bot = bot

    @discord.ui.button(label="Sending", style=discord.ButtonStyle.primary, custom_id="role_sending_eth")
    async def sending_button(self, interaction: discord.Interaction, button: Button):
        await self.handle_role_selection(interaction, "sending")

    @discord.ui.button(label="Receiving", style=discord.ButtonStyle.success, custom_id="role_receiving_eth")
    async def receiving_button(self, interaction: discord.Interaction, button: Button):
        await self.handle_role_selection(interaction, "receiving")

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.danger, custom_id="role_reset_eth")
    async def reset_button(self, interaction: discord.Interaction, button: Button):
        self.sending_user = None
        self.receiving_user = None
        await self.update_embed()
        await interaction.response.defer()

    async def handle_role_selection(self, interaction, role):
        if role == "sending":
            if self.sending_user or interaction.user == self.receiving_user:
                await interaction.response.defer()
                return
            self.sending_user = interaction.user
        else:
            if self.receiving_user or interaction.user == self.sending_user:
                await interaction.response.defer()
                return
            self.receiving_user = interaction.user
        await self.update_embed()
        await interaction.response.defer()
        await self.check_roles_complete()

    async def update_embed(self):
        embed = self.last_embed_message.embeds[0]
        embed.set_field_at(0, name="Sending Ethereum", value=self.sending_user.mention if self.sending_user else "`None`", inline=True)
        embed.set_field_at(1, name="Receiving Ethereum", value=self.receiving_user.mention if self.receiving_user else "`None`", inline=True)
        await self.last_embed_message.edit(embed=embed)

    async def check_roles_complete(self):
        if self.sending_user and self.receiving_user:
            confirmation_embed = discord.Embed(
                title="Confirmed Role Identities",
                description="Both users have confirmed their roles within this deal.",
                color=3667300
            )
            confirmation_embed.add_field(name="Sending Ethereum", value=self.sending_user.mention, inline=True)
            confirmation_embed.add_field(name="Receiving Ethereum", value=self.receiving_user.mention, inline=True)
            await self.disable_buttons()
            view = ConfirmationETHView(self.last_embed_message, self.sending_user, self.receiving_user, self.bot)
            await self.last_embed_message.channel.send(embed=confirmation_embed, view=view)

    async def disable_buttons(self):
        for item in self.children:
            item.disabled = True
        await self.last_embed_message.edit(view=self)

class ConfirmationETHView(View):
    def __init__(self, role_embed_message, sending_user, receiving_user, bot):
        super().__init__(timeout=None)
        self.role_embed_message = role_embed_message
        self.sending_user = sending_user
        self.receiving_user = receiving_user
        self.correct_responses = set()
        self.correct_response_messages = []
        self.bot = bot

    @discord.ui.button(label="Correct", style=discord.ButtonStyle.success, custom_id="confirm_correct_eth")
    async def correct_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in self.correct_responses:
            await interaction.response.send_message("You have already confirmed.", ephemeral=True)
            return

        self.correct_responses.add(interaction.user.id)
        response_message = await self.send_correct_response_message(interaction)

        if self.sending_user.id in self.correct_responses and self.receiving_user.id in self.correct_responses:
            await self.handle_final_confirmation(interaction)
        else:
            await interaction.response.defer()

    async def send_correct_response_message(self, interaction):
        response_embed = discord.Embed(
            description=f"{interaction.user.mention} has responded with **'Correct'**",
            color=3667300
        )
        response_message = await interaction.channel.send(embed=response_embed)
        self.correct_response_messages.append(response_message)
        return response_message

    async def handle_final_confirmation(self, interaction):
        await self.delete_correct_response_messages()
        await interaction.message.delete()  # Delete the "Amount Confirmation" embed

        eth_service = self.bot.get_cog("ETHService")
        if eth_service:
            await eth_service.send_final_steps(self.role_embed_message.channel, self.amount, self.sending_user, self.receiving_user)

    @discord.ui.button(label="Incorrect", style=discord.ButtonStyle.danger, custom_id="confirm_incorrect_eth")
    async def incorrect_button(self, interaction: discord.Interaction, button: Button):
        await self.role_embed_message.delete()
        await interaction.message.delete()
        await self.delete_correct_response_messages()
        await self.send_new_role_selection_embed(interaction.channel)

    async def delete_correct_response_messages(self):
        for msg in self.correct_response_messages:
            await msg.delete()

    async def send_new_role_selection_embed(self, channel):
        new_embed = discord.Embed(
            title="Role Selection",
            description="Please select one of the following buttons that corresponds to your role in this deal. Once selected, both users must confirm to proceed.",
            color=3667300
        )
        new_embed.add_field(name="Sending Ethereum", value="`None`", inline=True)
        new_embed.add_field(name="Receiving Ethereum", value="`None`", inline=True)
        new_message = await channel.send(embed=new_embed)
        new_view = RoleSelectionETHView(last_embed_message=new_message, bot=self.bot)
        await new_message.edit(view=new_view)

class AmountConfirmationETHView(View):
    def __init__(self, channel, amount, sending_user, receiving_user, bot):
        super().__init__(timeout=None)
        self.channel = channel
        self.amount = amount
        self.sending_user = sending_user
        self.receiving_user = receiving_user
        self.correct_responses = set()
        self.correct_response_messages = []
        self.bot = bot

    @discord.ui.button(label="Correct", style=discord.ButtonStyle.success, custom_id="amount_correct_eth")
    async def correct_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in self.correct_responses:
            await interaction.response.send_message("You have already confirmed.", ephemeral=True)
            return

        self.correct_responses.add(interaction.user.id)
        response_message = await self.send_correct_response_message(interaction)

        if self.sending_user.id in self.correct_responses and self.receiving_user.id in self.correct_responses:
            await self.finalize_confirmation(interaction)
        else:
            await interaction.response.defer()

    async def send_correct_response_message(self, interaction):
        response_embed = discord.Embed(
            description=f"{interaction.user.mention} has responded with **'Correct'**",
            color=3667300
        )
        response_message = await interaction.channel.send(embed=response_embed)
        self.correct_response_messages.append(response_message)
        return response_message

    async def finalize_confirmation(self, interaction):
        await self.delete_correct_response_messages()
        await interaction.message.delete()  # Delete the "Amount Confirmation" embed
        await self.send_final_steps(interaction)

    async def send_final_steps(self, interaction):
        eth_service = self.bot.get_cog("ETHService")
        if eth_service:
            await eth_service.send_final_steps(self.channel, self.amount, self.sending_user, self.receiving_user)

    @discord.ui.button(label="Incorrect", style=discord.ButtonStyle.danger, custom_id="amount_incorrect_eth")
    async def incorrect_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await self.delete_correct_response_messages()
        await self.send_amount_request_embed(interaction.channel)

    async def delete_correct_response_messages(self):
        for msg in self.correct_response_messages:
            await msg.delete()

    async def send_amount_request_embed(self, channel):
        amount_request_embed = discord.Embed(
            title="Deal Amount",
            description="Please state the amount we are expected to receive in USD. (eg. 100.59)",
            color=3667300
        )
        await channel.send(content=f"{self.sending_user.mention}", embed=amount_request_embed)

        def check(m):
            return m.author == self.sending_user and m.channel == channel

        try:
            response = await self.bot.wait_for('message', check=check, timeout=300)
            amount = response.content.strip()
            await self.handle_amount_confirmation(channel, amount)
        except asyncio.TimeoutError:
            await channel.send(embed=discord.Embed(description="You have run out of time!", color=15608876))

    async def handle_amount_confirmation(self, channel, amount):
        amount_confirmation_embed = discord.Embed(
            title="Amount Confirmation",
            description=f"Are we expected to receive {amount} USD?",
            color=15975211
        )
        view = AmountConfirmationETHView(channel, amount, self.sending_user, self.receiving_user, self.bot)
        await channel.send(embed=amount_confirmation_embed, view=view)

async def setup(bot):
    await bot.add_cog(RoleSelectionETHView(bot))
