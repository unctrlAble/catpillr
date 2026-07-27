import os
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

BOT_OWNER_ID = 1499613581115789372

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# strip_after_prefix=True allows spaces like "ctplr. checkcatpillr"
bot = commands.Bot(command_prefix="ctplr.", strip_after_prefix=True, intents=intents)

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


def delete_user_count(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM catpillr_counts WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


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


@bot.event
async def on_command_error(ctx, error):
    # Ignore CommandNotFound errors to keep console logs clean
    if isinstance(error, commands.CommandNotFound):
        return
    raise error


# =========================================================
# CHECK COUNT COMMAND (Prefix & Slash - DM Enabled)
# =========================================================
@bot.command(name="checkcatpillr")
async def prefix_checkcatpillr(ctx, target: discord.User = None):
    target = target or ctx.author
    count = get_user_count(target.id)
    await ctx.send(f"🐛 {target.display_name} has {count} catpillr")


@bot.tree.command(name="checkcatpillr", description="check catpillr count for someone")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.describe(user="who to check")
async def checkcatpillr(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    count = get_user_count(user.id)
    await interaction.response.send_message(f"🐛 {user.display_name} has {count} catpillr")


# =========================================================
# GLOBAL TOTAL COMMAND (Prefix & Slash - DM Enabled)
# =========================================================
@bot.command(name="gcatpillr")
async def prefix_gcatpillr(ctx):
    grand_total = get_global_total()
    await ctx.send(f"🐛 global total: **{grand_total}** catpillr")


@bot.tree.command(name="gcatpillr", description="total global catpillrs collected")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def gcatpillr(interaction: discord.Interaction):
    grand_total = get_global_total()
    await interaction.response.send_message(f"🐛 global total: **{grand_total}** catpillr")


# =========================================================
# GLOBAL LEADERBOARD (Prefix & Slash - DM Enabled)
# =========================================================
def build_global_leaderboard():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, count FROM catpillr_counts ORDER BY count DESC LIMIT 10")
    top_users = cursor.fetchall()
    conn.close()

    if not top_users:
        return None

    embed = discord.Embed(title="🐛 Global Catpillr Leaderboard", color=discord.Color.green())
    leaderboard_text = ""
    for rank, (u_id, count) in enumerate(top_users, start=1):
        leaderboard_text += f"**#{rank}** <@{u_id}> — **{count}** catpillrs\n"

    embed.description = leaderboard_text
    return embed


@bot.command(name="gbcatpillr")
async def prefix_gbcatpillr(ctx):
    embed = build_global_leaderboard()
    if not embed:
        await ctx.send("nobody found any catpillrs yet lol")
        return
    await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


@bot.tree.command(name="gbcatpillr", description="top global catpillr collectors")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def gbcatpillr(interaction: discord.Interaction):
    embed = build_global_leaderboard()
    if not embed:
        await interaction.response.send_message("nobody found any catpillrs yet lol")
        return
    await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())


# =========================================================
# SERVER LEADERBOARD (Prefix & Slash)
# =========================================================
def build_server_leaderboard(guild):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, count FROM catpillr_counts ORDER BY count DESC")
    all_users = cursor.fetchall()
    conn.close()

    server_top = []
    for u_id, count in all_users:
        if guild.get_member(u_id):
            server_top.append((u_id, count))
            if len(server_top) == 10:
                break

    if not server_top:
        return None

    embed = discord.Embed(title=f"🐛 {guild.name} Catpillr Leaderboard", color=discord.Color.green())
    leaderboard_text = ""
    for rank, (u_id, count) in enumerate(server_top, start=1):
        leaderboard_text += f"**#{rank}** <@{u_id}> — **{count}** catpillrs\n"

    embed.description = leaderboard_text
    return embed


@bot.command(name="sbcatpillr")
async def prefix_sbcatpillr(ctx):
    if not ctx.guild:
        await ctx.send("❌ Server leaderboard only works inside a server, not in DMs!")
        return
    embed = build_server_leaderboard(ctx.guild)
    if not embed:
        await ctx.send("nobody in this server found any catpillrs yet lol")
        return
    await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


@bot.tree.command(name="sbcatpillr", description="top catpillr collectors in this server")
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
async def sbcatpillr(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Server leaderboard only works inside a server, not in DMs!", ephemeral=True)
        return
    embed = build_server_leaderboard(interaction.guild)
    if not embed:
        await interaction.response.send_message("nobody in this server found any catpillrs yet lol")
        return
    await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())


# =========================================================
# OWNER-ONLY DELETE (Prefix & Slash - DM Enabled)
# =========================================================
@bot.command(name="delete")
async def prefix_delete(ctx, target: discord.User):
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("❌ Only the bot owner can use this command.")
        return

    try:
        delete_user_count(target.id)
        await ctx.send(f"✅ Successfully wiped all stored data for **{target.name}** ({target.id}).")
    except Exception as e:
        print(f"Error deleting user data: {e}")
        await ctx.send(f"⚠️ Failed to wipe data for {target.name}.")


@prefix_delete.error
async def prefix_delete_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Usage: `ctplr.delete @user` or `ctplr. delete @user`")


@bot.tree.command(name="delete", description="wipes a user's catpillr data (owner only)")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.describe(user="user to wipe")
async def slash_delete(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message(
            "❌ Only the bot owner can use this command.",
            ephemeral=True
        )
        return

    try:
        delete_user_count(user.id)
        await interaction.response.send_message(
            f"✅ Successfully wiped all stored data for **{user.name}** ({user.id}).",
            ephemeral=True
        )
    except Exception as e:
        print(f"Error deleting user data: {e}")
        await interaction.response.send_message(
            f"⚠️ Failed to wipe data for {user.name}.",
            ephemeral=True
        )


bot.run(TOKEN)
