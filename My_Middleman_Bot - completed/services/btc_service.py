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

async def setup(bot):
    await bot.add_cog(BTCService(bot))
