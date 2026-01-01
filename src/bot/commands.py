"""Discord slash commands."""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from .stats import StatsManager


class StatCommands(commands.Cog):
    """Cog for stat commands."""

    def __init__(self, bot: commands.Bot, stats_manager: StatsManager):
        self.bot = bot
        self.stats = stats_manager

    @app_commands.command(name="stats", description="View your gaming statistics")
    async def stats_command(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View statistics for yourself or another user."""
        target_user = user or interaction.user

        await interaction.response.defer()

        player_stats = await self.stats.get_player_stats(target_user.id)

        if not player_stats or player_stats['total_playtime_seconds'] == 0:
            await interaction.followup.send(
                f"No playtime data found for {target_user.display_name}."
            )
            return

        # Create embed
        embed = discord.Embed(
            title=f"{player_stats['display_name'] or player_stats['username']} - Gaming Stats",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Total Playtime",
            value=f"{player_stats['total_playtime_readable']} ({player_stats['total_playtime_hours']}h)",
            inline=False
        )

        if player_stats['games']:
            top_games = "\n".join([
                f"{idx}. {game['name']} - {game['readable']}"
                for idx, game in enumerate(player_stats['games'][:5], 1)
            ])
            embed.add_field(name=f"Top {len(player_stats['games'][:5])} Games", value=top_games, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard", description="View the player leaderboard")
    async def leaderboard_command(self, interaction: discord.Interaction, limit: int = 10):
        """Display the player leaderboard."""
        if limit < 1 or limit > 25:
            await interaction.response.send_message("Limit must be between 1 and 25.", ephemeral=True)
            return

        await interaction.response.defer()

        leaderboard = await self.stats.get_leaderboard(limit)

        if not leaderboard:
            await interaction.followup.send("No leaderboard data available yet.")
            return

        # Create embed
        embed = discord.Embed(
            title="🏆 Player Leaderboard",
            description="Top players by total playtime",
            color=discord.Color.gold()
        )

        for entry in leaderboard:
            name = entry['display_name'] or entry['username']
            value = f"**{entry['readable']}** ({entry['hours']} hrs) • {entry['games_played']} games"

            # Add medal emoji for top 3
            if entry['rank'] == 1:
                medal = "🥇"
            elif entry['rank'] == 2:
                medal = "🥈"
            elif entry['rank'] == 3:
                medal = "🥉"
            else:
                medal = ""

            embed.add_field(name=f"{medal} #{entry['rank']} {name}", value=value, inline=False)

        embed.set_footer(text="LAN Party Stats")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="topgames", description="View the most played games")
    async def topgames_command(self, interaction: discord.Interaction, limit: int = 10):
        """Display the top games by playtime."""
        if limit < 1 or limit > 25:
            await interaction.response.send_message("Limit must be between 1 and 25.", ephemeral=True)
            return

        await interaction.response.defer()

        top_games = await self.stats.get_top_games(limit)

        if not top_games:
            await interaction.followup.send("No game data available yet.")
            return

        # Create embed
        embed = discord.Embed(
            title="🎮 Top Games",
            description="Most played games by total playtime",
            color=discord.Color.green()
        )

        for game in top_games:
            value = f"**{game['readable']}** ({game['hours']} hrs) • {game['unique_players']} players"
            embed.add_field(
                name=f"#{game['rank']} {game['name']}",
                value=value,
                inline=False
            )

        embed.set_footer(text="LAN Party Stats")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="game", description="View statistics for a specific game")
    async def game_command(self, interaction: discord.Interaction, game_name: str):
        """View statistics for a specific game."""
        await interaction.response.defer()

        game_stats = await self.stats.get_game_details(game_name)

        if not game_stats:
            await interaction.followup.send(f"No data found for game: {game_name}")
            return

        # Create embed
        embed = discord.Embed(
            title=game_stats['game_name'],
            color=discord.Color.purple()
        )

        embed.add_field(
            name="Total Playtime",
            value=f"**{game_stats['readable']}** ({game_stats['hours']} hours)",
            inline=True
        )
        embed.add_field(
            name="Players",
            value=str(game_stats['unique_players']),
            inline=True
        )

        if game_stats['players']:
            top_players = "\n".join([
                f"{idx}. {p['display_name'] or p['username']} - {p['readable']}"
                for idx, p in enumerate(game_stats['players'][:10], 1)
            ])
            embed.add_field(name="Top Players", value=top_players, inline=False)

        embed.set_footer(text="LAN Party Stats")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="toptracks", description="View the most listened Spotify tracks")
    async def toptracks_command(self, interaction: discord.Interaction, limit: int = 10):
        """Display the top Spotify tracks by listening time."""
        if limit < 1 or limit > 25:
            await interaction.response.send_message("Limit must be between 1 and 25.", ephemeral=True)
            return

        await interaction.response.defer()

        top_tracks = await self.stats.get_top_spotify_tracks(limit)

        if not top_tracks:
            await interaction.followup.send("No Spotify data available yet.")
            return

        # Create embed
        embed = discord.Embed(
            title="🎵 Top Spotify Tracks",
            description="Most listened tracks by total time",
            color=discord.Color.from_rgb(30, 215, 96)  # Spotify green
        )

        for track in top_tracks:
            value = f"**{track['artist']}** • {track['readable']} • {track['unique_listeners']} listeners"
            embed.add_field(
                name=f"#{track['rank']} {track['title']}",
                value=value,
                inline=False
            )

        embed.set_footer(text="LAN Party Stats")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spotify", description="View your Spotify listening statistics")
    async def spotify_command(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View Spotify statistics for yourself or another user."""
        target_user = user or interaction.user

        await interaction.response.defer()

        spotify_stats = await self.stats.get_user_spotify_stats(target_user.id)

        if not spotify_stats or spotify_stats['total_seconds'] == 0:
            await interaction.followup.send(
                f"No Spotify data found for {target_user.display_name}."
            )
            return

        # Create embed
        embed = discord.Embed(
            title=f"{target_user.display_name} - Spotify Stats",
            color=discord.Color.from_rgb(30, 215, 96)
        )

        embed.add_field(
            name="Total Listening Time",
            value=f"**{spotify_stats['readable']}** ({spotify_stats['hours']} hours)",
            inline=False
        )

        if spotify_stats['top_tracks']:
            top_tracks = "\n".join([
                f"{idx}. {t['title']} by {t['artist']} - {t['readable']}"
                for idx, t in enumerate(spotify_stats['top_tracks'][:5], 1)
            ])
            embed.add_field(name="Top 5 Tracks", value=top_tracks, inline=False)

        embed.set_footer(text="LAN Party Stats")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="overview", description="View server statistics overview")
    async def overview_command(self, interaction: discord.Interaction):
        """Display server statistics overview."""
        await interaction.response.defer()

        overview = await self.stats.get_overview_stats()

        # Create embed
        embed = discord.Embed(
            title="📈 Server Statistics Overview",
            description="Stats across all users",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🎮 Total Gaming Time",
            value=f"**{overview['total_game_readable']}** ({overview['total_game_hours']} hours)",
            inline=False
        )

        embed.add_field(
            name="🎵 Total Spotify Time",
            value=f"**{overview['total_spotify_readable']}** ({overview['total_spotify_hours']} hours)",
            inline=False
        )

        embed.add_field(
            name="Active Players",
            value=str(overview['unique_players']),
            inline=True
        )

        embed.add_field(
            name="Unique Games",
            value=str(overview['unique_games']),
            inline=True
        )

        embed.add_field(
            name="Unique Tracks",
            value=str(overview['unique_tracks']),
            inline=True
        )

        embed.set_footer(text="LAN Party Stats")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot, stats_manager: StatsManager):
    """Setup the stat commands cog."""
    await bot.add_cog(StatCommands(bot, stats_manager))