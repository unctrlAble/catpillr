import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

catpillr_counts = {}

# Load triggers from triggers.txt file automatically
TRIGGERS = []
try:
  with open("triggers.txt", "r", encoding="utf-8") as f:
    text = f.read()
    TRIGGERS = text.split()
  print(f"Loaded {len(TRIGGERS)} triggers from triggers.txt")
except FileNotFoundError:
  print("WARNING: triggers.txt not found! Defaulting to basic triggers.")
  TRIGGERS = ["catpillr", "caterpillar", "🐛"]


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user}!")
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} slash command(s).")
  except Exception as e:
    print(e)


@bot.event
async def on_message(message):
  if message.author == bot.user or message.author.bot:
    return

  content_lower = message.content.lower()

  total_found = 0
  for trigger in TRIGGERS:
    total_found += content_lower.count(trigger.lower())

  if total_found > 0:
    user_id = message.author.id

    if user_id not in catpillr_counts:
      catpillr_counts[user_id] = 0
    catpillr_counts[user_id] += total_found

    current_count = catpillr_counts[user_id]
    username = message.author.display_name

    await message.channel.send(
        f"catpillr detected 🐛🐛🐛 {username} now has {current_count} catpillr"
        " 🐛🐛🐛"
    )

  await bot.process_commands(message)


@bot.tree.command(
    name="checkcatpillr", description="Check how many catpillrs someone has!"
)
@app_commands.describe(user="The user you want to check")
async def checkcatpillr(interaction: discord.Interaction, user: discord.Member):
  count = catpillr_counts.get(user.id, 0)
  await interaction.response.send_message(
      f"🐛 {user.display_name} has {count} catpillr(s)!"
  )


@bot.tree.command(
    name="gcatpillr",
    description="See the total global sum of all catpillrs collected!",
)
async def gcatpillr(interaction: discord.Interaction):
  grand_total = sum(catpillr_counts.values())
  await interaction.response.send_message(
      f"🐛🌍 Across all servers, there is a global total of **{grand_total}**"
      " catpillr(s) collected so far!"
  )


bot.run(TOKEN)
