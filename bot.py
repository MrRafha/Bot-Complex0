import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sqlite3

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
        obj = Objective(interaction.user, objetivo, mapa, unlock_time)
        objectives.append(obj)
        save_objective(interaction.user, objetivo, mapa, unlock_time)
        user_counts[interaction.user.id] = user_counts.get(interaction.user.id, 0) + 1
        save_user_count(interaction.user.id, user_counts[interaction.user.id])
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
    cursor.execute("DELETE FROM user_counts")
    conn.commit()
    await interaction.response.send_message("Ranking resetado com sucesso.")

# Evento chamado quando o bot está pronto
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    await tree.sync()  # Sincroniza os comandos slash com o Discord

# Inicializa o banco de dados SQLite
conn = sqlite3.connect("botdata.db")
cursor = conn.cursor()

# Cria as tabelas se não existirem
cursor.execute("""
CREATE TABLE IF NOT EXISTS objectives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT,
    name TEXT,
    map_name TEXT,
    unlock_time TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_counts (
    user_id INTEGER PRIMARY KEY,
    count INTEGER
)
""")
conn.commit()

# Funções para salvar e carregar dados do banco de dados
def save_objective(user, name, map_name, unlock_time):
    cursor.execute(
        "INSERT INTO objectives (user_id, user_name, name, map_name, unlock_time) VALUES (?, ?, ?, ?, ?)",
        (user.id, user.display_name, name, map_name, unlock_time.isoformat())
    )
    conn.commit()

def load_objectives():
    cursor.execute("SELECT user_id, user_name, name, map_name, unlock_time FROM objectives")
    rows = cursor.fetchall()
    objs = []
    for user_id, user_name, name, map_name, unlock_time in rows:
        user = type("User", (), {"id": user_id, "display_name": user_name})()
        objs.append(Objective(user, name, map_name, datetime.fromisoformat(unlock_time)))
    return objs

def clear_old_objectives():
    cursor.execute("DELETE FROM objectives WHERE unlock_time < ?", (datetime.now().isoformat(),))
    conn.commit()

def save_user_count(user_id, count):
    cursor.execute(
        "INSERT INTO user_counts (user_id, count) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET count=?",
        (user_id, count, count)
    )
    conn.commit()

def load_user_counts():
    cursor.execute("SELECT user_id, count FROM user_counts")
    return dict(cursor.fetchall())

# Carrega objetivos e contagem de usuários ao iniciar
clear_old_objectives()
objectives = load_objectives()
user_counts = load_user_counts()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Insira o token do seu bot abaixo
bot.run(TOKEN)