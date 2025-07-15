import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Configura os intents necessários para o bot funcionar
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Usado para comandos slash

# Armazenamento dos objetivos e contagem de usuários em memória
objectives = []      # Lista de objetivos adicionados
user_counts = {}     # Dicionário para contar quantos objetivos cada usuário adicionou

# Classe para representar um objetivo
class Objective:
    def __init__(self, user, name, map_name, unlock_time):
        self.user = user              # Usuário que adicionou o objetivo
        self.name = name              # Nome do objetivo
        self.map_name = map_name      # Nome do mapa
        self.unlock_time = unlock_time # Data/hora de liberação do objetivo

    def time_left(self):
        # Calcula o tempo restante até liberar o objetivo
        delta = self.unlock_time - datetime.now()
        return str(delta).split('.')[0] if delta.total_seconds() > 0 else "Liberado!"

# Comando /scout para adicionar um objetivo
@tree.command(name="scout", description="Adicione um objetivo para ser conquistado")
@app_commands.describe(objetivo="Nome do objetivo", mapa="Nome do mapa", tempo="Tempo restante (hh:mm)")
async def scout(interaction: discord.Interaction, objetivo: str, mapa: str, tempo: str):
    """
    Adiciona um objetivo diretamente, sem confirmação por reação.
    Exemplo de uso: /scout orb roxo longfen arms 01:45
    """
    try:
        hours, minutes = map(int, tempo.split(":"))
        unlock_time = datetime.now() + timedelta(hours=hours, minutes=minutes)
        objectives.append(Objective(interaction.user, objetivo, mapa, unlock_time))
        user_counts[interaction.user.id] = user_counts.get(interaction.user.id, 0) + 1
        await interaction.response.send_message(
            f"Objetivo '{objetivo}' adicionado para o mapa '{mapa}' e será liberado em {tempo}.", ephemeral=True
        )
    except Exception:
        await interaction.response.send_message("Formato inválido! Use o tempo como hh:mm", ephemeral=True)

# Comando /tracker para listar objetivos pendentes
@tree.command(name="tracker", description="Lista todos os objetivos pendentes")
async def tracker(interaction: discord.Interaction):
    """
    Lista todos os objetivos que ainda não foram liberados, mostrando timer e quem adicionou.
    """
    now = datetime.utcnow()
    pending = []
    for obj in objectives:
        if obj.unlock_time > datetime.now():
            # Converte unlock_time para UTC timestamp
            unlock_utc = obj.unlock_time.astimezone().timestamp()
            # Formata horário UTC
            horario_utc = obj.unlock_time.strftime("%H:%M UTC")
            # Timer Discord (relativo)
            timer_discord = f"<t:{int(unlock_utc)}:R>"
            # Nome do usuário
            user_name = obj.user.display_name if hasattr(obj.user, "display_name") else str(obj.user)
            pending.append(
                f"{obj.name} - {obj.map_name} - {horario_utc} - {timer_discord} - Timed by: {user_name}"
            )
    msg = "\n".join(pending) if pending else "Nenhum objetivo pendente."
    await interaction.response.send_message(msg)

# Comando /rank para mostrar ranking dos usuários
@tree.command(name="rank", description="Ranking dos usuários que mais listaram objetivos")
async def rank(interaction: discord.Interaction):
    """
    Mostra o ranking dos usuários que mais adicionaram objetivos.
    """
    if not user_counts:
        await interaction.response.send_message("Nenhum objetivo listado ainda.")
        return
    sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
    lines = []
    for idx, (user_id, count) in enumerate(sorted_users[:10], 1):
        user = await bot.fetch_user(user_id)
        lines.append(f"top {idx}: {user.mention} ({count} objetivos)")
    await interaction.response.send_message("\n".join(lines))

# Comando /RR para resetar o ranking (admin apenas)
@tree.command(name="rr", description="Reseta o ranking dos usuários (admin apenas)")
async def rr(interaction: discord.Interaction):
    """
    Reseta o ranking dos usuários. Apenas administradores podem usar.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Você não tem permissão para resetar o ranking.", ephemeral=True)
        return
    user_counts.clear()
    await interaction.response.send_message("Ranking resetado com sucesso.")

# Evento chamado quando o bot está pronto
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    await tree.sync()  # Sincroniza os comandos slash com o Discord

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Insira o token do seu bot abaixo
bot.run(TOKEN)