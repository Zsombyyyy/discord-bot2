import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import os
from dotenv import load_dotenv

# .env betöltése
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    print("⚠️ Nincs DISCORD_TOKEN beállítva a .env fájlban!")
    exit(1)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Beállítások
WELCOME_CHANNEL_ID = 1376575912098926695
LEAVE_CHANNEL_ID = 1387959145327628502
WELCOME_ROLE_ID = 1376573308274872401

# Bot készen áll
@bot.event
async def on_ready():
    print(f'A bot bejelentkezett: {bot.user}')

# Új tag belépése
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    role = member.guild.get_role(WELCOME_ROLE_ID)
    if channel:
        embed = discord.Embed(
            title=f"Üdvözlünk a szerveren, {member.name}! 🎉",
            description=f"Kedves {member.mention}, örülünk, hogy itt vagy! 🌟",
            color=discord.Color.green()
        )
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)
        embed.set_footer(text=f"{member.guild.name} - Jó szórakozást kívánunk!")
        await channel.send(embed=embed)
    if role:
        await member.add_roles(role)

# Tag kilépése
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LEAVE_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title=f"{member.name} elhagyta a szervert 😢",
            description="Reméljük, egyszer visszatérsz hozzánk! 👋",
            color=discord.Color.red()
        )
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)
        embed.set_footer(text=f"{member.guild.name}")
        await channel.send(embed=embed)

# Némített védelem hangcsatornában
@bot.event
async def on_voice_state_update(member, before, after):
    mute_role = get(member.guild.roles, name="Némított")
    if mute_role in member.roles and after.channel is not None:
        await member.move_to(None)
        try:
            await member.send("❌ Nem csatlakozhatsz hangcsatornához, amíg némítva vagy!")
        except:
            pass

# Üzenetküldési némítás kezelése
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    mute_role = get(message.guild.roles, name="Némított")
    if mute_role in message.author.roles:
        try:
            await message.delete()
            try:
                await message.author.send(f"❌ Némítva vagy, így nem írhatsz üzenetet a(z) **{message.guild.name}** szerveren.")
            except:
                pass
        except:
            pass
        return

    await bot.process_commands(message)

# Időformátum parszoló (pl. 10s, 5m, 2h, 1d)
def parse_duration(duration_str):
    if len(duration_str) < 2:
        return None
    unit = duration_str[-1].lower()
    amount_str = duration_str[:-1]
    if not amount_str.isdigit():
        return None
    amount = int(amount_str)
    return {
        's': amount,
        'm': amount * 60,
        'h': amount * 3600,
        'd': amount * 86400
    }.get(unit, None)

# !help parancs
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📘 Parancsok", color=discord.Color.blue())
    embed.add_field(name="!ban @felhasználó [indok]", value="🚫 Kitiltja a megadott felhasználót.", inline=False)
    embed.add_field(name="!kick @felhasználó [indok]", value="👢 Kirúgja a megadott felhasználót.", inline=False)
    embed.add_field(name="!mute @felhasználó", value="🔇 Némítja a felhasználót.", inline=False)
    embed.add_field(name="!tempmute @felhasználó idő", value="⏳ Ideiglenesen némít.", inline=False)
    embed.add_field(name="!unmute @felhasználó", value="🔈 Feloldja a némítást.", inline=False)
    embed.add_field(name="!embed <cím> <leírás>", value="📧 Egy egyéni beágyazott üzenetet küld.", inline=False)
    embed.add_field(name="!temprole @felhasználó @szerep idő", value="⏳ Ideiglenesen ad szerepet.", inline=False)
    embed.add_field(name="!clear [szám]", value="🧹 Üzenetek törlése.", inline=False)
    await ctx.send(embed=embed)

# !ban parancs
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.send(f"🚫 Kitiltottak téged a(z) **{ctx.guild.name}** szerverről.\nIndok: {reason or 'Nincs megadva'}")
    except:
        pass
    await member.ban(reason=reason)
    await ctx.send(f'🚫 {member.mention} kitiltva. Indok: {reason or "Nincs megadva"}')

# !kick parancs
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.send(f"👢 Kikaptak téged a(z) **{ctx.guild.name}** szerverről.\nIndok: {reason or 'Nincs megadva'}")
    except:
        pass
    await member.kick(reason=reason)
    await ctx.send(f'👢 {member.mention} kirúgva. Indok: {reason or "Nincs megadva"}')

# !mute parancs
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    mute_role = get(ctx.guild.roles, name="Némított")
    if not mute_role:
        mute_role = await ctx.guild.create_role(name="Némított")
        for channel in ctx.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False)
    await member.add_roles(mute_role)
    try:
        await member.send(f"🔇 Le lettél némítva a(z) **{ctx.guild.name}** szerveren. Nem írhatsz ezen a szerveren.")
    except:
        pass
    await ctx.send(f'🔇 {member.mention} némítva lett.')

# !tempmute parancs
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member: discord.Member, duration_str: str = None):
    mute_role = get(ctx.guild.roles, name="Némított")
    if not mute_role:
        mute_role = await ctx.guild.create_role(name="Némított")
        for channel in ctx.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False)

    if not duration_str:
        await ctx.send("❗ Adj meg időt! Pl.: 10s, 5m, 2h, 1d")
        return

    duration = parse_duration(duration_str)
    if duration is None:
        await ctx.send("❗ Hibás időformátum! (pl. 10s, 5m, 2h, 1d)")
        return

    await member.add_roles(mute_role)
    try:
        await member.send(f"🔇 Le lettél némítva a(z) **{ctx.guild.name}** szerveren {duration_str} időtartamra. Nem írhatsz ezen a szerveren.")
    except:
        pass
    await ctx.send(f'⏳ {member.mention} némítva lett {duration_str} időtartamra.')
    await asyncio.sleep(duration)
    if mute_role in member.roles:
        await member.remove_roles(mute_role)
        try:
            await member.send(f"🔈 A némításod lejárt a(z) **{ctx.guild.name}** szerveren.")
        except:
            pass
        await ctx.send(f'⏰ {member.mention} némítása lejárt.')

@tempmute.error
async def tempmute_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❗ Kérlek, jelölj meg egy felhasználót és add meg az időt!")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Nincs jogosultságod ehhez.")

# !unmute parancs
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    mute_role = get(ctx.guild.roles, name="Némított")
    if mute_role in member.roles:
        await member.remove_roles(mute_role)
        try:
            await member.send(f"🔈 Feloldották a némításod a(z) **{ctx.guild.name}** szerveren.")
        except:
            pass
        await ctx.send(f'🔈 {member.mention} némítása feloldva.')
    else:
        await ctx.send(f'⚠️ {member.mention} nincs némítva.')

# !embed parancs (egyéni cím és leírás, szerver ikon beállítással)
@bot.command()
async def embed(ctx, title: str = None, *, description: str = None):
    if not title or not description:
        await ctx.send("❗ Használat: `!embed <cím> <leírás>`\nPl.: `!embed Frissítés! Új funkció érkezett!`")
        return

    embed = discord.Embed(title=title, description=description, color=discord.Color.purple())
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)

    await ctx.send(embed=embed)

# !temprole parancs
@bot.command()
@commands.has_permissions(manage_roles=True)
async def temprole(ctx, member: discord.Member, role: discord.Role, duration_str: str = None):
    if not duration_str:
        await ctx.send("❗ Adj meg időt! Pl.: 10s, 5m, 2h, 1d")
        return

    duration = parse_duration(duration_str)
    if duration is None:
        await ctx.send("❗ Hibás időformátum! (pl. 10s, 5m, 2h, 1d)")
        return

    await member.add_roles(role)
    await ctx.send(f'⏳ {member.mention} megkapta a(z) {role.name} szerepet {duration_str} időtartamra.')
    await asyncio.sleep(duration)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f'⏰ {member.mention} elvesztette a(z) {role.name} szerepet.')

# !clear parancs
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 {len(deleted)} üzenet törölve.", delete_after=5)

# Hibaüzenetek magyarul
@ban.error
@kick.error
@mute.error
@unmute.error
@temprole.error
@clear.error
async def permission_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Nincs jogosultságod ehhez a parancshoz.")
    elif isinstance(error, commands.MissingRequiredArgument):
        param = error.param.name
        if param == "member":
            await ctx.send("❗ Adj meg egy felhasználót! (@felhasználó)")
        elif param == "role":
            await ctx.send("❗ Adj meg egy szerepet! (@szerep)")
        elif param == "duration":
            await ctx.send("❗ Adj meg egy időt! (pl. 10s, 5m, 2h, 1d)")
    else:
        await ctx.send(f"Hiba történt: {error}")

# Nem létező parancs kezelése
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Nincs ilyen parancs vagy elírtad!")
    else:
        # Más hibák kezelése opcionális
        pass

bot.run(TOKEN)
