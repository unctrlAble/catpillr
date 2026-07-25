import os
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "catpillr.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS catpillr_counts (
            user_id INTEGER PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)
  conn.commit()
  conn.close()


def get_user_count(user_id: int) -> int:
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT count FROM catpillr_counts WHERE user_id = ?", (user_id,)
  )
  row = cursor.fetchone()
  conn.close()
  return row[0] if row else 0


def add_user_count(user_id: int, amount: int) -> int:
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO catpillr_counts (user_id, count)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET count = count + ?
    """,
      (user_id, amount, amount),
  )
  conn.commit()

  cursor.execute(
      "SELECT count FROM catpillr_counts WHERE user_id = ?", (user_id,)
  )
  new_count = cursor.fetchone()[0]
  conn.close()
  return new_count


def get_global_total() -> int:
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("SELECT SUM(count) FROM catpillr_counts")
  total = cursor.fetchone()[0]
  conn.close()
  return total if total else 0


init_db()

TRIGGERS = []
try:
  with open("triggers.txt", "r", encoding="utf-8") as f:
    text = f.read()
    TRIGGERS = text.split()
  print(f"loaded {len(TRIGGERS)} triggers")
except FileNotFoundError:
  print("triggers.txt missing, using defaults")
  TRIGGERS = ["catpillr", "caterpillar", "🐛"]


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user}")
  try:
    synced = await bot.tree.sync()
    print(f"synced {len(synced)} commands")
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
    current_count = add_user_count(message.author.id, total_found)
    username = message.author.display_name

    await message.channel.send(
        f"catpillr detected 🐛🐛🐛 {username} now has {current_count} catpillr"
        " 🐛🐛🐛"
    )

  await bot.process_commands(message)


@bot.tree.command(
    name="checkcatpillr", description="check catpillr count for someone"
)
@app_commands.describe(user="who to check")
async def checkcatpillr(interaction: discord.Interaction, user: discord.Member):
  count = get_user_count(user.id)
  await interaction.response.send_message(
      f"🐛 {user.display_name} has {count} catpillr"
  )


@bot.tree.command(
    name="gcatpillr", description="total global catpillrs collected"
)
async def gcatpillr(interaction: discord.Interaction):
  grand_total = get_global_total()
  await interaction.response.send_message(
      f"🐛 global total: **{grand_total}** catpillr"
  )


@bot.tree.command(
    name="gbcatpillr", description="top global catpillr collectors"
)
async def gbcatpillr(interaction: discord.Interaction):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT user_id, count FROM catpillr_counts ORDER BY count DESC LIMIT 10"
  )
  top_users = cursor.fetchall()
  conn.close()

  if not top_users:
    await interaction.response.send_message(
        "nobody found any catpillrs yet lol"
    )
    return

  leaderboard_text = "🐛 **global catpillr leaderboard** 🐛\n\n"
  for rank, (u_id, count) in enumerate(top_users, start=1):
    leaderboard_text += f"**#{rank}** <@{u_id}> — **{count}**\n"

  await interaction.response.send_message(leaderboard_text)


@bot.tree.command(
    name="sbcatpillr", description="top catpillr collectors in this server"
)
async def sbcatpillr(interaction: discord.Interaction):
  if not interaction.guild:
    await interaction.response.send_message(
        "this command only works inside a server!"
    )
    return

  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  # Fetch all users sorted by count
  cursor.execute(
      "SELECT user_id, count FROM catpillr_counts ORDER BY count DESC"
  )
  all_users = cursor.fetchall()
  conn.close()

  server_top = []
  for u_id, count in all_users:
    # Only keep users who belong to this server
    if interaction.guild.get_member(u_id):
      server_top.append((u_id, count))
      if len(server_top) == 10:
        break

  if not server_top:
    await interaction.response.send_message(
        "nobody in this server found any catpillrs yet lol"
    )
    return

  leaderboard_text = (
      f"🐛 **{interaction.guild.name} catpillr leaderboard** 🐛\n\n"
  )
  for rank, (u_id, count) in enumerate(server_top, start=1):
    leaderboard_text += f"**#{rank}** <@{u_id}> — **{count}**\n"

  await interaction.response.send_message(leaderboard_text)


bot.run(TOKEN)
