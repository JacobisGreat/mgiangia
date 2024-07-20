import discord
from discord.ext import commands
from discord.ui import Button, View
import requests

class InvoicePasteButtonView(View):
    def __init__(self, amount, address):
        super().__init__(timeout=None)
        self.amount = amount
        self.address = address

    @discord.ui.button(label="Paste", style=discord.ButtonStyle.primary, custom_id="invoice_paste")
    async def paste_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"{self.address}", ephemeral=False)
        await interaction.followup.send(f"{self.amount:.6f} BTC", ephemeral=False)
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

class BTCService(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_final_steps(self, channel, amount, sending_user, receiving_user):
        await self.send_confirmed_amount(channel, amount, sending_user, receiving_user)
        await self.send_payment_invoice(channel, amount, sending_user)
        await self.send_waiting_transaction(channel)

    async def send_confirmed_amount(self, channel, amount, sending_user, receiving_user):
        confirmed_amount_embed = discord.Embed(
            title="Confirmed Amount",
            description="> The following amount has been confirmed by both parties",
            color=3667300
        )
        confirmed_amount_embed.add_field(name="USD Amount", value=f"`${float(amount):.2f} Bitcoin`", inline=True)
        await channel.send(content=f"{sending_user.mention} {receiving_user.mention}", embed=confirmed_amount_embed)

    async def send_payment_invoice(self, channel, amount, sending_user):
        exchange_rate = await self.fetch_exchange_rate("bitcoin")
        total_amount = float(amount) / exchange_rate

        payment_invoice_embed = discord.Embed(
            title="📥 Payment Invoice",
            description=f"> {sending_user.mention} Please send the funds as part of the deal to the Middleman address specified below.\n> To ensure the validation of your payment, please copy and paste the amount provided.",
            color=3667300
        )
        payment_invoice_embed.add_field(name="Bitcoin Address", value="`bc1qdrlc5ljk3flz6nnwkk7rahskxxfqk5waye54cf`", inline=False)
        payment_invoice_embed.add_field(name="Bitcoin Amount", value=f"`{total_amount:.6f} BTC`", inline=False)
        payment_invoice_embed.add_field(name="USD Amount", value=f"`${float(amount):.2f} Bitcoin`", inline=False)
        payment_invoice_embed.set_footer(text=f"Exchange Rate: 1 BTC = ${exchange_rate:.2f} USD")
        payment_invoice_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1153826027714379866/1175266184933937212/bitcoin-btc-badge-5295535-4414740.png")
        await channel.send(content=f"{sending_user.mention}", embed=payment_invoice_embed, view=InvoicePasteButtonView(total_amount, "bc1qdrlc5ljk3flz6nnwkk7rahskxxfqk5waye54cf"))

    async def send_waiting_transaction(self, channel):
        waiting_transaction_embed = discord.Embed(
            description="<a:Loading:1263637705347305482> Waiting for transaction...",
            color=14737371
        )
        await channel.send(embed=waiting_transaction_embed)

    async def fetch_exchange_rate(self, crypto):
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[crypto]['usd']

class AmountConfirmationBTCView(View):
    def __init__(self, channel, amount, sending_user, receiving_user, bot):
        super().__init__(timeout=None)
        self.channel = channel
        self.amount = amount
        self.sending_user = sending_user
        self.receiving_user = receiving_user
        self.correct_responses = set()
        self.correct_response_messages = []
        self.bot = bot

    @discord.ui.button(label="Correct", style=discord.ButtonStyle.success, custom_id="amount_correct_btc")
    async def correct_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in self.correct_responses:
            await interaction.response.send_message("You have already confirmed.", ephemeral=True)
            return

        self.correct_responses.add(interaction.user.id)
        response_message = await self.send_correct_response_message(interaction)

        if self.sending_user.id in self.correct_responses and self.receiving_user.id in self.correct_responses:
            await interaction.message.delete()  # Delete the "Amount Confirmation" embed
            await self.delete_correct_response_messages()
            await self.send_final_confirmation(interaction)
            await interaction.response.defer()
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

    async def send_final_confirmation(self, interaction):
        confirmed_amount_embed = discord.Embed(
            title="Confirmed Amount",
            description="> The following amount has been confirmed by both parties",
            color=3667300
        )
        confirmed_amount_embed.add_field(name="USD Amount", value=f"`${float(self.amount):.2f} Bitcoin`", inline=True)
        await self.channel.send(content=f"{self.sending_user.mention} {self.receiving_user.mention}", embed=confirmed_amount_embed)

        payment_invoice_embed = discord.Embed(
            title="📥 Payment Invoice",
            description=f"> {self.sending_user.mention} Please send the funds as part of the deal to the Middleman address specified below.\n> To ensure the validation of your payment, please copy and paste the amount provided.",
            color=3667300
        )
        payment_invoice_embed.add_field(name="Bitcoin Address", value="`bc1qdrlc5ljk3flz6nnwkk7rahskxxfqk5waye54cf`", inline=False)
        payment_invoice_embed.add_field(name="Bitcoin Amount", value=f"`{float(self.amount):.6f} BTC`", inline=False)
        payment_invoice_embed.add_field(name="USD Amount", value=f"`${float(self.amount):.2f} Bitcoin`", inline=False)
        payment_invoice_embed.set_footer(text="Exchange Rate: 1 BTC = $3423.86 USD")
        payment_invoice_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1153826027714379866/1175266184933937212/bitcoin-btc-badge-5295535-4414740.png")
        await self.channel.send(content=f"{self.sending_user.mention}", embed=payment_invoice_embed)

        waiting_transaction_embed = discord.Embed(
            description="<a:Loading:1263637705347305482> Waiting for transaction...",
            color=14737371
        )
        await self.channel.send(embed=waiting_transaction_embed)

    @discord.ui.button(label="Incorrect", style=discord.ButtonStyle.danger, custom_id="amount_incorrect_btc")
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
            # Ensure amount is a valid decimal number
            try:
                amount = float(amount)
                await self.handle_amount_confirmation(channel, amount)
            except ValueError:
                await channel.send(embed=discord.Embed(description="Invalid amount entered. Please enter a valid decimal number.", color=15608876))
        except:
            await channel.send(embed=discord.Embed(description="You have run out of time!", color=15608876))

    async def handle_amount_confirmation(self, channel, amount):
        amount_confirmation_embed = discord.Embed(
            title="Amount Confirmation",
            description=f"Are we expected to receive {amount} USD?",
            color=15975211
        )
        view = AmountConfirmationBTCView(channel, amount, self.sending_user, self.receiving_user, self.bot)
        await channel.send(embed=amount_confirmation_embed, view=view)

async def setup(bot):
    await bot.add_cog(BTCService(bot))
