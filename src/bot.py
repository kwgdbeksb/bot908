import asyncio
import os
from datetime import datetime, timezone
from collections import deque
import discord
from discord.ext import commands
from discord import app_commands

from config import load_config
from utils.logger import setup_logger
import wavelink


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # allow reading messages in group chats
        config = load_config()
        super().__init__(
            command_prefix=commands.when_mentioned_or("!", ">"),
            intents=intents,
            application_id=config.app_id,
            status=discord.Status.dnd,
            activity=discord.Activity(type=discord.ActivityType.watching, name="you from the shadows"),
        )
        self.logger = setup_logger()
        self.config = config
        self.owner_id = self.config.owner_id
        # Track last-set presence for accurate confirmations
        self.presence_status: discord.Status = discord.Status.dnd
        self.presence_activity: discord.BaseActivity | None = discord.Activity(
            type=discord.ActivityType.watching, name="you from the shadows"
        )
        # Track bot start time for uptime metrics
        self.start_time: datetime = datetime.now(timezone.utc)
        # Internal flag to avoid duplicate per-guild syncs
        self._synced_per_guild: bool = False
        # Owner DM notifications
        self._owner_dm_task: asyncio.Task | None = None
        self._startup_dm_sent: bool = False
        # DM relay: track target user IDs whose DMs should be forwarded to owner
        self.dm_relay_targets: set[int] = set()
        # In-memory audit log entries (rolling buffer)
        self.audit_log_entries: deque[dict] = deque(maxlen=2000)

    async def setup_hook(self):
        """Setup hook called when the bot is starting up."""
        self.logger.info("🚀 Starting bot setup hook...")
        
        # Initialize Wavelink nodes
        try:
            nodes = [
                wavelink.Node(
                    uri=f"http://{self.config.lavalink_host}:{self.config.lavalink_port}",
                    password=self.config.lavalink_password,
                    identifier="main",
                    retries=3,
                    heartbeat=30.0,
                )
            ]
            await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)
            self.logger.info("🎵 Wavelink nodes connected successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect Wavelink nodes: {e}")
            # Continue without Wavelink - music commands will handle this gracefully

        # Load all cogs
        cogs_to_load = [
            "cogs.general",
            "cogs.tictactoe", 
            "cogs.blackjack",
            "cogs.football",
            "cogs.music",
            "jishaku",  # Development/debugging cog
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                self.logger.info(f"✅ Loaded cog: {cog}")
            except Exception as e:
                self.logger.error(f"❌ Failed to load cog {cog}: {e}")

        # Start Wavelink health check task
        self._wavelink_health_task = asyncio.create_task(self._wavelink_health_check())
        
        self.logger.info("✅ Bot setup hook completed")

    async def close(self):
        """Clean shutdown of the bot."""
        self.logger.info("🔄 Bot is shutting down...")
        
        # Cancel health check task
        if hasattr(self, '_wavelink_health_task'):
            self._wavelink_health_task.cancel()
            
        # Cancel owner DM task
        if self._owner_dm_task:
            self._owner_dm_task.cancel()
            
        # Disconnect all Wavelink players
        try:
            for guild in self.guilds:
                try:
                    player = wavelink.Pool.get_node().get_player(guild.id)
                    if player:
                        await player.disconnect(force=True)
                        self.logger.info(f"🎵 Disconnected player for guild {guild.name}")
                except Exception as e:
                    self.logger.warning(f"🎵 Error disconnecting player for guild {guild.name}: {e}")
        except Exception as e:
            self.logger.error(f"❌ Error during player cleanup: {e}")
            
        # Close Wavelink pool
        try:
            await wavelink.Pool.close()
            self.logger.info("🎵 Wavelink pool closed")
        except Exception as e:
            self.logger.warning(f"🎵 Error closing Wavelink pool: {e}")
            
        await super().close()
        self.logger.info("✅ Bot shutdown completed")

    async def _wavelink_health_check(self):
        """Periodic health check for Wavelink nodes."""
        while not self.is_closed():
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check if we have any nodes
                if not wavelink.Pool.nodes:
                    self.logger.warning("🎵 No Wavelink nodes available, attempting reconnection...")
                    try:
                        nodes = [
                            wavelink.Node(
                                uri=f"http://{self.config.lavalink_host}:{self.config.lavalink_port}",
                                password=self.config.lavalink_password,
                                identifier="main",
                                retries=3,
                                heartbeat=30.0,
                            )
                        ]
                        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)
                        self.logger.info("🎵 Wavelink nodes reconnected successfully")
                    except Exception as e:
                        self.logger.error(f"❌ Failed to reconnect Wavelink nodes: {e}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in Wavelink health check: {e}")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """Called when a Wavelink node is ready."""
        self.logger.info(f"🎵 Wavelink node {payload.node.identifier} is ready!")
        self.logger.info(f"🎵 Node stats: {payload.node.stats}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Called when a track starts playing."""
        player = payload.player
        track = payload.track
        
        if hasattr(player, 'text_channel') and player.text_channel:
            try:
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"**{track.title}**\nby {track.author}",
                    color=discord.Color.green()
                )
                
                if hasattr(track, 'uri') and track.uri:
                    embed.add_field(name="Source", value=f"[Link]({track.uri})", inline=True)
                    
                if track.length:
                    duration = f"{track.length // 60000}:{(track.length // 1000) % 60:02d}"
                    embed.add_field(name="Duration", value=duration, inline=True)
                    
                embed.set_footer(text=f"Requested in {player.channel.name if hasattr(player, 'channel') else 'Unknown'}")
                
                await player.text_channel.send(embed=embed)
                
            except Exception as e:
                self.logger.error(f"❌ Error sending now playing message: {e}")

    async def on_ready(self):
        """Called when the bot is ready."""
        self.logger.info(f"🤖 {self.user} is ready and online!")
        self.logger.info(f"🆔 Bot ID: {self.user.id}")
        self.logger.info(f"🏠 Connected to {len(self.guilds)} guilds")
        
        # Log guild information
        for guild in self.guilds:
            self.logger.info(f"  📍 {guild.name} (ID: {guild.id}) - {guild.member_count} members")
        
        # Sync commands based on configuration
        try:
            if self.config.sync_global:
                # Global sync - commands available in all guilds
                self.logger.info("🔄 Syncing commands globally...")
                synced = await self.tree.sync()
                self.logger.info(f"✅ Synced {len(synced)} global commands")
            else:
                # Guild-specific sync - faster for development
                if self.config.guild_id and not self._synced_per_guild:
                    guild = discord.Object(id=self.config.guild_id)
                    self.logger.info(f"🔄 Syncing commands for guild {self.config.guild_id}...")
                    synced = await self.tree.sync(guild=guild)
                    self.logger.info(f"✅ Synced {len(synced)} commands for guild {self.config.guild_id}")
                    self._synced_per_guild = True
                else:
                    self.logger.info("ℹ️ Guild sync already completed or no guild ID configured")
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to sync commands: {e}")

        # Send startup notification to owner
        if not self._startup_dm_sent:
            self._owner_dm_task = asyncio.create_task(self._send_startup_dm())
            
        # Optional: Auto-play feature (uncomment if desired)
        # asyncio.create_task(self._attempt_auto_play())

    async def _send_startup_dm(self):
        """Send a startup notification to the bot owner."""
        try:
            await asyncio.sleep(2)  # Brief delay to ensure bot is fully ready
            
            owner = await self.fetch_user(self.owner_id)
            if owner:
                embed = discord.Embed(
                    title="🤖 Bot Started Successfully",
                    description=f"**{self.user.name}** is now online and ready!",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="📊 Status",
                    value=f"• Connected to **{len(self.guilds)}** guilds\n• Loaded **{len(self.cogs)}** cogs\n• Latency: **{round(self.latency * 1000)}ms**",
                    inline=False
                )
                
                # Add guild list if not too many
                if len(self.guilds) <= 10:
                    guild_list = "\n".join([f"• {guild.name}" for guild in self.guilds])
                    embed.add_field(name="🏠 Connected Guilds", value=guild_list, inline=False)
                
                embed.set_footer(text=f"Bot ID: {self.user.id}")
                embed.set_thumbnail(url=self.user.display_avatar.url)
                
                await owner.send(embed=embed)
                self.logger.info(f"📨 Startup notification sent to owner {owner.name}")
                self._startup_dm_sent = True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to send startup DM to owner: {e}")

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global error handler for application commands."""
        self.logger.error(f"❌ App command error in {interaction.command.name if interaction.command else 'unknown'}: {error}")
        
        # Create user-friendly error message
        if isinstance(error, app_commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"Please wait {error.retry_after:.1f} seconds before using this command again.",
                color=discord.Color.orange()
            )
        elif isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="🚫 Missing Permissions",
                description="You don't have the required permissions to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Command Error",
                description="An error occurred while executing the command. Please try again later.",
                color=discord.Color.red()
            )
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"❌ Failed to send error message: {e}")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global error handler for prefix commands."""
        self.logger.error(f"❌ Prefix command error in {ctx.command.name if ctx.command else 'unknown'}: {error}")
        
        # Create user-friendly error message
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="🚫 Missing Permissions",
                description="You don't have the required permissions to use this command.",
                color=discord.Color.red()
            )
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"Please wait {error.retry_after:.1f} seconds before using this command again.",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="❌ Command Error",
                description="An error occurred while executing the command. Please try again later.",
                color=discord.Color.red()
            )
        
        try:
            await ctx.send(embed=embed)
        except Exception as e:
            self.logger.error(f"❌ Failed to send error message: {e}")

    async def _attempt_auto_play(self):
        """Optional auto-play feature - plays a default song on startup."""
        try:
            await asyncio.sleep(10)  # Wait for bot to be fully ready
            
            # Find a guild with a voice channel
            for guild in self.guilds:
                if guild.voice_channels:
                    # Try to find a channel with members
                    for channel in guild.voice_channels:
                        if len(channel.members) > 0:
                            # Found a channel with members, attempt to join and play
                            try:
                                player = await channel.connect(cls=wavelink.Player)
                                
                                # Search for a default song
                                tracks = await wavelink.Playable.search("lofi hip hop")
                                if tracks:
                                    await player.play(tracks[0])
                                    self.logger.info(f"🎵 Auto-play started in {guild.name} - {channel.name}")
                                    return
                                    
                            except Exception as e:
                                self.logger.warning(f"🎵 Auto-play failed for {guild.name}: {e}")
                                continue
                                
        except Exception as e:
            self.logger.error(f"❌ Auto-play error: {e}")


async def main():
    """Main function to run the bot."""
    bot = Bot()
    
    try:
        await bot.start(bot.config.token)
    except KeyboardInterrupt:
        print("\n🔄 Received interrupt signal, shutting down gracefully...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()
        print("✅ Bot shutdown completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")