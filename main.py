import discord
from discord import app_commands, utils
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

server_name = "Your Server Name"

bot_id = 1208950394043236383

server_id = 1208868393265135636

unregistered_role_id = 1208871478389510245
staff_role_id = 1208929592493088818
name_approval_role_id = 1208955791302860870

emoji_log_channel_id = 1208946529763594250
name_approval_channel_id = 1208930976261214328
message_log_channel_id = 1208965568800096306
on_voice_chat_join_channel_id = 1208971148541304862
on_voice_chat_leave_channel_id = 1208972664220426250
registration_room_id = 1208929467645304842
unregistered_chat_id = 1208929329975791676
support_call_channel_id = 1208934748647325736
support_waiting_channel_id = 1208933993031016459
welcome_channel_id = 1208939073989779486
goodbye_channel_id = 1208939099839402034

class ticket_launcher(discord.ui.View):
    global server_name
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 600, commands.BucketType.member)
    
    @discord.ui.button(label="Create Ticket!", style=discord.ButtonStyle.blurple, custom_id="ticket_button")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        interaction.message.author = interaction.user
        retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
        if retry: return await interaction.response.send_message(f"Slow down! Try again in {round(retry, 1)} seconds!", ephemeral=True)
        ticket = utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.name.lower().replace(' ', '-')}-{interaction.user.discriminator}")
        if ticket is not None: await interaction.response.send_message(f"You already have an open ticket. {ticket.mention}!", ephemeral=True)
        else:
            if type(client.ticket_mod) is not discord.Role: 
                client.ticket_mod = interaction.guild.get_role(staff_role_id)
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True, attach_files=True, embed_links=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True), 
                client.ticket_mod: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True, attach_files=True, embed_links=True),
            }
            try: channel = await interaction.guild.create_text_channel(name=f"ticket-{interaction.user.name}-{interaction.user.discriminator}", overwrites=overwrites, reason=f"Ticket for {interaction.user}")
            except: return await interaction.response.send_message("Ticket creation failed, ensure you have `manage_channels` permission!", ephemeral=True)
            await channel.send(f"{client.ticket_mod.mention}, {interaction.user.mention} created a ticket.", view=main())
            await interaction.response.send_message(f"I created your ticket in {channel.mention}!", ephemeral=True)

class confirm(discord.ui.View):
    global server_name
    def __init__(self) -> None:
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red, custom_id="confirm")
    async def confirm_button(self, interaction, button):
        try: await interaction.channel.delete()
        except: await interaction.response.send_message("Channel deletion failed, ensure you have `manage_channels` permission!", ephemeral=True)

class main(discord.ui.View):
    global server_name
    def __init__(self) -> None:
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close")
    async def close(self, interaction, button):
        embed = discord.Embed(title="Are you sure you want to close the ticket?", color=discord.Colour.blurple())
        await interaction.response.send_message(embed=embed, view=confirm(), ephemeral=True)

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.blurple, custom_id="transcript")
    async def transcript(self, interaction, button):
        await interaction.response.defer()
        if os.path.exists(f"{interaction.channel.id}.md"):
            return await interaction.followup.send("A transcript is already being generated!", ephemeral=True)
        with open(f"{interaction.channel.id}.md", 'a', encoding='utf-8') as f:  # UTF-8 encoding specified
            f.write(f"# Transcript of {interaction.channel.name}:\n\n")
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                created = datetime.strftime(message.created_at, "%m/%d/%Y at %H:%M:%S")
                if message.edited_at:
                    edited = datetime.strftime(message.edited_at, "%m/%d/%Y at %H:%M:%S")
                    f.write(f"{message.author} on {created}: {message.clean_content} (Edited at {edited})\n")
                else:
                    f.write(f"{message.author} on {created}: {message.clean_content}\n")
            generated = datetime.now().strftime("%m/%d/%Y at %H:%M:%S")
            f.write(f"\n*Generated at {generated} by {client.user}*\n*Date Formatting: MM/DD/YY*\n*Time Zone: UTC*")
        with open(f"{interaction.channel.id}.md", 'rb') as f:
            await interaction.followup.send(file=discord.File(f, f"{interaction.channel.name}.md"))
        os.remove(f"{interaction.channel.id}.md")

class aclient(discord.Client):
    global server_name
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.synced = False  # we use this so the bot doesn't sync commands more than once
        self.added = False
        self.ticket_mod = staff_role_id

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:  # check if slash commands have been synced 
            await tree.sync(guild=discord.Object(id=server_id))  # guild specific: leave blank if global (global registration can take 1-24 hours)
            self.synced = True
        if not self.added:
            self.add_view(ticket_launcher())
            self.add_view(main())
            self.added = True
        print(f"We have logged in as {self.user}.")

client = aclient()
tree = app_commands.CommandTree(client)

@tree.command(guild=discord.Object(id=server_id), name='ticket', description='Creates a ticket system.')  # guild specific slash command
@app_commands.default_permissions(manage_guild=True)
@app_commands.checks.cooldown(3, 60, key=lambda i: (i.guild_id))
@app_commands.checks.bot_has_permissions(manage_channels=True)
async def ticketing(interaction: discord.Interaction):
    embed = discord.Embed(title="Click to create a ticket!", color=discord.Colour.blue())
    await interaction.channel.send(embed=embed, view=ticket_launcher())
    await interaction.response.send_message("Ticket system started!", ephemeral=True)

@tree.command(guild=discord.Object(id=server_id), name='close', description="Closes the ticket")  # guild specific slash command
@app_commands.checks.bot_has_permissions(manage_channels=True)
async def close(interaction: discord.Interaction):
    if "ticket-for-" in interaction.channel.name:
        embed = discord.Embed(title="Are you sure you want to close this ticket?", color=discord.Colour.blurple())
        await interaction.response.send_message(embed=embed, view=confirm(), ephemeral=True)
    else: await interaction.response.send_message("This is not a ticket!", ephemeral=True)

@tree.command(guild=discord.Object(id=server_id), name='add', description="Adds a user to the ticket")  # guild specific slash command
@app_commands.describe(user="This user wants to add you to the ticket")
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.cooldown(3, 20, key=lambda i: (i.server_id, i.user.id))
@app_commands.checks.bot_has_permissions(manage_channels=True)
async def add(interaction: discord.Interaction, user: discord.Member):
    if "ticket-for-" in interaction.channel.name:
        await interaction.channel.set_permissions(user, view_channel=True, send_messages=True, attach_files=True, embed_links=True)
        await interaction.response.send_message(f"{user.mention} was successfully added to the ticket. {interaction.user.mention}!")
    else: await interaction.response.send_message("This is not a ticket!", ephemeral=True)

@tree.command(guild=discord.Object(id=server_id), name='remove', description="Removes a user from the ticket")  # guild specific slash command
@app_commands.describe(user="This user wants to remove you from the ticket.")
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.cooldown(3, 20, key=lambda i: (i.server_id, i.user.id))
@app_commands.checks.bot_has_permissions(manage_channels=True)
async def remove(interaction: discord.Interaction, user: discord.Member):
    if "ticket-for-" in interaction.channel.name:
        if type(client.ticket_mod) is not discord.Role: client.ticket_mod = interaction.guild.get_role(staff_role_id)
        if client.ticket_mod not in interaction.user.roles:
            return await interaction.response.send_message("You do not have permission for this!", ephemeral=True)
        if client.ticket_mod not in user.roles:
            await interaction.channel.set_permissions(user, overwrite=None)
            await interaction.response.send_message(f"{user.mention} was successfully removed from the ticket. {interaction.user.mention}!", ephemeral=True)
        else: await interaction.response.send_message(f"{user.mention} is a moderator!", ephemeral=True)
    else: await interaction.response.send_message("This is not a ticket!", ephemeral=True)

@tree.command(guild=discord.Object(id=server_id), name='transcript', description='Creates a transcript.')  # guild specific slash command
async def transcript(interaction: discord.Interaction): 
    if "ticket-for-" in interaction.channel.name:
        await interaction.response.defer()
        if os.path.exists(f"{interaction.channel.id}.md"):
            return await interaction.followup.send("A transcript is already being generated!", ephemeral=True)
        with open(f"{interaction.channel.id}.md", 'a') as f:
            f.write(f"# Transcript of {interaction.channel.name}:\n\n")
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                created = datetime.strftime(message.created_at, "%m/%d/%Y at %H:%M:%S")
                if message.edited_at:
                    edited = datetime.strftime(message.edited_at, "%m/%d/%Y at %H:%M:%S")
                    f.write(f"{message.author} on {created}: {message.clean_content} (Edited at {edited})\n")
                else:
                    f.write(f"{message.author} on {created}: {message.clean_content}\n")
            generated = datetime.now().strftime("%m/%d/%Y at %H:%M:%S")
            f.write(f"\n*Generated at {generated} by {client.user}*\n*Date Formatting: MM/DD/YY*\n*Time Zone: UTC*")
        with open(f"{interaction.channel.id}.md", 'rb') as f:
            await interaction.followup.send(file=discord.File(f, f"{interaction.channel.name}.md"))
        os.remove(f"{interaction.channel.id}.md")
    else: await interaction.response.send_message("This is not a ticket!", ephemeral=True)

@tree.context_menu(name="Open a Ticket", guild=discord.Object(id=server_id))
@app_commands.default_permissions(manage_guild=True)
@app_commands.checks.cooldown(3, 20, key=lambda i: (i.server_id, i.user.id))
@app_commands.checks.bot_has_permissions(manage_channels=True)
async def open_ticket_context_menu(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    ticket = utils.get(interaction.guild.text_channels, name=f"ticket-{user.name.lower().replace(' ', '-')}-{user.discriminator}")
    if ticket is not None: await interaction.followup.send(f"{user.mention} already has a ticket at {ticket.mention}!", ephemeral=True)
    else:
        if type(client.ticket_mod) is not discord.Role: 
            client.ticket_mod = interaction.guild.get_role(staff_role_id)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True, attach_files=True, embed_links=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True), 
            client.ticket_mod: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True, attach_files=True, embed_links=True),
        }
        try: channel = await interaction.guild.create_text_channel(name=f"ticket-for-{user.name}-{user.discriminator}", overwrites=overwrites, reason=f"Ticket created by {interaction.user} for {user}.")
        except: return await interaction.followup.send("Ticket creation failed, ensure you have `manage_channels` permission!", ephemeral=True)
        await channel.send(f"{interaction.user.mention} created a ticket for {user.mention}!", view=main())   
        await interaction.followup.send(f"I created a ticket for you in {channel.mention}!", ephemeral=True)

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        return await interaction.response.send_message(error, ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        return await interaction.response.send_message(error, ephemeral=True)
    else:
        await interaction.response.send_message("An error occurred!", ephemeral=True)
        raise error

@client.event
async def on_ready():
    global tree
    await tree.sync(guild=discord.Object(id=server_id))
    print("Bot is ready.")

@client.event
async def on_reaction_add(reaction: discord.Reaction, member: discord.Member):
    global client, emoji_log_channel_id, name_approval_channel_id, name_approval_role_id, bot_id, server_id, staff_role_id
    global server_name
    server = client.get_guild(server_id)
    emote = reaction.emoji
    emoteownername = member.name
    emoteowner = member
    emoteowneravatar = member.avatar
    emoteownerid = member.id
    channel = reaction.message.channel
    messageowner = reaction.message.author
    message = reaction.message
    channelid = reaction.message.channel.id
    emoji_log_channel = client.get_channel(emoji_log_channel_id)
    name_approval_role = server.get_role(name_approval_role_id)
    staff_role = server.get_role(staff_role_id)
    embed = discord.Embed(title="Emoji Log", color=0x90EE90)
    embed.set_thumbnail(url=emoteowneravatar)
    embed.set_footer(text=server_name)
    embed.add_field(name="Emoji:", value=emote, inline=False)
    embed.add_field(name="Emoji Clicked By:", value=emoteownername, inline=False)
    embed.add_field(name="Emoji Clicker ID:", value=emoteownerid, inline=False)
    embed.add_field(name="Channel Where Emoji Was Clicked:", value=channel.mention, inline=False)
    embed.add_field(name="Channel ID Where Emoji Was Clicked:", value=channelid, inline=False)
    await emoji_log_channel.send(embed=embed)
    if channelid == name_approval_channel_id:
        await message.add_reaction("✅")
    if channelid == name_approval_channel_id and emote == "✅":
        if emoteowner.id == bot_id:
            print("The bot tried to approve.")
        elif staff_role in emoteowner.roles:
            await messageowner.add_roles(name_approval_role)
            await message.author.edit(nick=f"{message.content.title()}")
            await message.author.send("Your IC name request has been approved, you can now enter the server.")
            print(f"Approval successful, approval role given to {messageowner.name}")
        else:
            print(f"Someone tried to approve but didn't have the role. {emoteowner.name}")
    if channelid == name_approval_channel_id and emote == "❎":
        if emoteownerid == bot_id:
            print("The bot tried to reject")
        else:
            await message.author.send("Your IC name request was rejected, please enter it again.")

@client.event
async def on_member_join(member: discord.Member):
    global welcome_channel_id
    global goodbye_channel_id
    global unregistered_role_id
    global client
    global server_id
    global server_name
    server = client.get_guild(server_id)
    welcome_channel = server.get_channel(welcome_channel_id)
    goodbye_channel = server.get_channel(goodbye_channel_id)
    unregistered_role = server.get_role(unregistered_role_id)
    embed = discord.Embed(title="Someone joined the server.", color=0x90EE90)
    embed.set_thumbnail(url=member.avatar)
    embed.set_footer(text=server_name)
    embed.add_field(name=f"Someone joined the server:", value=member.mention, inline=False)
    embed.add_field(name="Account creation date:", value=member.created_at.date(), inline=False)
    embed.add_field(name="Server join date:", value=member.joined_at.date(), inline=False)
    await member.add_roles(unregistered_role)
    await welcome_channel.send(embed=embed)
    await member.send(f"Welcome 👋")

@client.event
async def on_member_remove(member: discord.Member):
    global welcome_channel_id
    global goodbye_channel_id
    global unregistered_role_id
    global client
    global server_id
    global server_name
    server = client.get_guild(server_id)
    goodbye_channel = server.get_channel(goodbye_channel_id)
    embed = discord.Embed(title="Someone left the server.", color=0x90EE90)
    embed.set_thumbnail(url=member.avatar)
    embed.set_footer(text=server_name)
    embed.add_field(name=f"Someone left the server:", value=member.mention, inline=False)
    embed.add_field(name="Account creation date:", value=member.created_at.date(), inline=False)
    embed.add_field(name="Server join date:", value=member.joined_at.date(), inline=False)
    await goodbye_channel.send(embed=embed)

@client.event
async def on_message(message: discord.Message):
    global client, emoji_log_channel_id, name_approval_channel_id, name_approval_role_id, bot_id, support_waiting_channel_id
    global client
    global server_id
    global message_log_channel_id
    global support_call_channel_id
    global server_name
    server = client.get_guild(server_id)
    support_waiting_channel = server.get_channel(support_waiting_channel_id)
    support_call_channel = server.get_channel(support_call_channel_id)
    name_approval_channel = server.get_channel(name_approval_channel_id)
    message_log_channel = server.get_channel(message_log_channel_id)
    embed = discord.Embed(title="Message Log", color=0x90EE90)
    embed.set_thumbnail(url=message.author.avatar)
    embed.set_footer(text=server_name)
    embed.add_field(name="Message content:", value=message.content, inline=False)
    embed.add_field(name="Message author name:", value=message.author.name, inline=False)
    embed.add_field(name="Message author ID:", value=message.author.id, inline=False)
    embed.add_field(name="Message channel:", value=message.channel.mention, inline=False)
    embed.add_field(name="Message channel ID:", value=message.channel.id, inline=False)
    embed.add_field(name="Account creation date:", value=message.author.created_at.date(), inline=False)
    embed.add_field(name="Server join date:", value=message.author.joined_at.date(), inline=False)
    if message.author.id == bot_id:
        if message.channel.id != support_call_channel.id or message.channel.id != support_waiting_channel.id:
            return
        else:
            print("The bot sent a message in support_call_channel.")
    else:
        await message_log_channel.send(embed=embed)
    if message.channel.id == name_approval_channel_id:
        await message.add_reaction("✅")
        await message.add_reaction("❎")

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    global on_voice_chat_leave_channel_id
    global on_voice_chat_join_channel_id
    global server_id
    global client
    global registration_room_id
    global unregistered_chat_id
    global staff_role_id
    global server_name
    server = client.get_guild(server_id)
    on_voice_chat_join_channel = server.get_channel(on_voice_chat_join_channel_id)
    on_voice_chat_leave_channel = server.get_channel(on_voice_chat_leave_channel_id)
    registration_room = server.get_channel(registration_room_id)
    unregistered_chat = server.get_channel(unregistered_chat_id)
    staff_role = server.get_role(staff_role_id)
    if before.channel is None and after.channel is not None:
        if after.channel.id == registration_room.id:
            registration_arrived = discord.Embed(title="Registration Arrived", color=0x90EE90)
            registration_arrived.set_thumbnail(url=member.avatar)
            registration_arrived.set_footer(text=server_name)
            registration_arrived.add_field(name="Registration room:", value=after.channel.mention, inline=False)
            registration_arrived.add_field(name="Registration room ID:", value=after.channel.id, inline=False)
            registration_arrived.add_field(name="Name of the person who joined the registration room:", value=member.name, inline=False)
            registration_arrived.add_field(name="ID of the person who joined the registration room:", value=member.id, inline=False)
            registration_arrived.add_field(name="Account creation date:", value=member.created_at.date(), inline=False)
            registration_arrived.add_field(name="Server join date:", value=member.joined_at.date(), inline=False)
            await unregistered_chat.send(staff_role.mention)
            await unregistered_chat.send(embed=registration_arrived)
        embed_joined = discord.Embed(title="Voice channel log", color=0x90EE90)
        embed_joined.set_thumbnail(url=member.avatar)
        embed_joined.set_footer(text=server_name)
        embed_joined.add_field(name="Joined channel:", value=after.channel.mention, inline=False)
        embed_joined.add_field(name="Joined channel ID:", value=after.channel.id, inline=False)
        embed_joined.add_field(name="Name of the person who joined the channel:", value=member.name, inline=False)
        embed_joined.add_field(name="ID of the person who joined the channel:", value=member.id, inline=False)
        embed_joined.add_field(name="Account creation date:", value=member.created_at.date(), inline=False)
        embed_joined.add_field(name="Server join date:", value=member.joined_at.date(), inline=False)
        await on_voice_chat_join_channel.send(embed=embed_joined)
    elif before.channel is not None and after.channel is None:
        embed_left = discord.Embed(title="Voice channel log", color=0x90EE90)
        embed_left.set_thumbnail(url=member.avatar)
        embed_left.set_footer(text=server_name)
        embed_left.add_field(name="Left channel:", value=before.channel.mention, inline=False)
        embed_left.add_field(name="Left channel ID:", value=before.channel.id, inline=False)
        embed_left.add_field(name="Name of the person who left the channel:", value=member.name, inline=False)
        embed_left.add_field(name="ID of the person who left the channel:", value=member.id, inline=False)
        embed_left.add_field(name="Account creation date:", value=member.created_at.date(), inline=False)
        embed_left.add_field(name="Server join date:", value=member.joined_at.date(), inline=False)
        await on_voice_chat_leave_channel.send(embed=embed_left)

@tree.command(name="call-support", description="Calls someone to the support waiting room.", guild=discord.Object(id=server_id))
async def call_support(interaction: discord.Interaction, person: discord.Member, reason: str):
    global staff_role_id
    global support_call_channel_id
    global client
    global server
    global support_waiting_channel_id
    global server_name
    server = client.get_guild(server_id)
    staff_role = server.get_role(staff_role_id)
    support_call_channel = server.get_channel(support_call_channel_id)
    support_waiting_channel = server.get_channel(support_waiting_channel_id)
    if staff_role in interaction.user.roles:
        embed = discord.Embed(title=f"{interaction.user.name} called {person.name} to support", color=0x90EE90)
        embed.set_thumbnail(url=person.avatar)
        embed.set_footer(text=server_name)
        embed.add_field(name="Support waiting room:", value=support_waiting_channel.mention, inline=False)
        embed.add_field(name="Support call channel:", value=support_call_channel.mention, inline=False)
        embed.add_field(name="Support calling staff:", value=interaction.user.name, inline=False)
        embed.add_field(name="Support calling staff ID:", value=interaction.user.id, inline=False)
        embed.add_field(name="Called person:", value=person.mention, inline=False)
        embed.add_field(name="Called person's ID:", value=person.id, inline=False)
        embed.add_field(name="Reason for call:", value=f"``{reason}``", inline=False)
        embed.add_field(name="Account creation date:", value=person.created_at.date(), inline=False)
        embed.add_field(name="Server join date:", value=person.joined_at.date(), inline=False)
        await support_call_channel.send(person.mention)
        await support_call_channel.send(embed=embed)
        await person.send(f"You have been called to support. https://discord.com/channels/1208868393265135636/1208933993031016459 \n\nReason for call: ``{reason}``")
        await interaction.response.send_message(f"Success, {person.name} has been called to support.", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

client.run(os.getenv('DISCORD_BOT_TOKEN'))
