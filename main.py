import nextcord, json
from nextcord.ext import commands, tasks
from modules.console import Logger

intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents, help_command=None)

@bot.event
async def on_ready():
    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching,name="orders"), status=nextcord.Status.idle)
    update_queue.start()
    Logger.info(f"Logged in as {bot.user}")

with open("./data/config.json") as f:
    config = json.load(f)

queue = []
messageID = None

try:
    with open("./data/queue.json", "r") as f:
        data = json.load(f)
        if data:
            queue = data.get("queue", [])
            queue_message_id = data.get("queue_message_id")
except FileNotFoundError:
    pass

def save_data():
    data = {"queue": queue, "queue_message_id": queue_message_id}
    with open("./data/queue.json", "w") as f:
        json.dump(data, f)

@tasks.loop(seconds=5)
async def update_queue():
    global queue_message_id
    guild = bot.get_guild(config["guildID"])
    channel = guild.get_channel(config["channelID"])

    embed = nextcord.Embed(title=f"{config['serverName']}・Queue", description="", color=9807270)
    embed.set_thumbnail(url=config["serverIcon"])
    embed.set_footer(text=config["serverName"], icon_url=config["serverIcon"])
    
    if queue:
        for index, person in enumerate(queue, start=1):
            if index == 1:
                description = f"✅ #{index}: {person['name']} - {person.get('description', '')}\n"
            else:
                description += f"⏳ #{index}: {person['name']} - {person.get('description', '')}\n"
        embed.description = description
    else:
        embed.description = "> Queue is currently empty."

    if queue_message_id:
        try:
            msg = await channel.fetch_message(queue_message_id)
            await msg.edit(embed=embed)
        except nextcord.NotFound:
            queue_message_id = None
    if not queue_message_id:
        msg = await channel.send(embed=embed)
        queue_message_id = msg.id
        save_data()

@bot.slash_command(name="addorder", description="Adds user to queue.")
async def addorder(ctx, name: nextcord.Member, description: str = None):
    member_roles = [role.id for role in ctx.user.roles]
    if config["roleID"] in member_roles:
        if description is None:
            queue.append({"name": name.display_name})
        else:
            queue.append({"name": name.display_name, "description": description})
        save_data()
        embed = nextcord.Embed(title="✅ Success!", description=f"> Successfully added {name.display_name} to the queue.", color=nextcord.Colour.green())
        Logger.info(f"Successfully added {name.display_name} to the queue.")
        await ctx.send(embed=embed)
    else:
        embed = nextcord.Embed(title="🤡 Fail!", description=f"> You do not have the required role to use this command.", color=nextcord.Colour.red())
        Logger.error(f"{ctx.user} tried adding an order.")
        await ctx.send(embed=embed)

@bot.slash_command(name="bumporder", description="Bumps an order in the queue.")
async def bumporder(ctx, order_id: int, bump_count: int):
    member_roles = [role.id for role in ctx.user.roles]
    if config["roleID"] in member_roles:
        if 1 <= order_id <= len(queue):
            for _ in range(bump_count):
                if order_id - 1 > 0:
                    queue[order_id - 1], queue[order_id - 2] = queue[order_id - 2], queue[order_id - 1]
                    order_id -= 1
            save_data()
            embed = nextcord.Embed(title="✅ Success!", description=f"> Successfully bumped order in the queue.", color=nextcord.Colour.green())
            await ctx.send(embed=embed, ephemeral=True)
            Logger.info(f"{ctx.user} successfully bumped an order.")
            await update_queue()
        else:
            embed = nextcord.Embed(title="❌ Fail!", description=f"> Failed to bump user in queue, order id not found.", color=nextcord.Colour.red())
            await ctx.send(embed=embed, ephemeral=True)
            Logger.error(f"{ctx.user} tried bumping an invalid order.")
    else:
        embed = nextcord.Embed(title="🤡 Fail!", description=f"> You do not have the required role to use this command.", color=nextcord.Colour.red())
        await ctx.send(embed=embed)
        Logger.error(f"{ctx.user} tried bumping an order.")

@bot.slash_command(name="completeorder", description="Removes a user from queue.")
async def completeorder(ctx, order_id: int):
    member_roles = [role.id for role in ctx.user.roles]
    if config["roleID"] in member_roles:
        if 1 <= order_id <= len(queue):
            removed_member = queue.pop(order_id - 1)
            save_data()
            embed = nextcord.Embed(title="✅ Success!", description=f"> Successfully removed {removed_member['name']} from the queue.", color=nextcord.Colour.green())
            await ctx.send(embed=embed, ephemeral=True)
            await update_queue()
            Logger.info(f"{ctx.user} successfully removed {removed_member['name']} from the queue.")
        else:
            embed = nextcord.Embed(title="❌ Fail!", description=f"> Failed to remove user from queue, order id not found.", color=nextcord.Colour.red())
            await ctx.send(embed=embed, ephemeral=True)
            Logger.error(f"{ctx.user} tried completing an invalid order.")
    else:
        embed = nextcord.Embed(title="🤡 Fail!", description=f"> You do not have the required role to use this command.", color=nextcord.Colour.red())
        await ctx.send(embed=embed)
        Logger.error(f"{ctx.user} tried completing an order.")

@bot.slash_command(name="clearqueue", description="Clears the entire queue.")
async def clearqueue(ctx):
    member_roles = [role.id for role in ctx.user.roles]
    if config["roleID"] in member_roles:
        queue.clear()
        save_data()
        embed = nextcord.Embed(title="✅ Success!", description="> Successfully cleared the queue.", color=nextcord.Colour.green())
        await ctx.send(embed=embed, ephemeral=True)
        await update_queue()
        Logger.info(f"{ctx.user} successfully removed cleared the queue.")
    else:
        embed = nextcord.Embed(title="🤡 Fail!", description=f"> You do not have the required role to use this command.", color=nextcord.Colour.red())
        await ctx.send(embed=embed)
        Logger.error(f"{ctx.user} tried clearing the queue.")

bot.run(config["botToken"])