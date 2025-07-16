# Discord Objective Tracker Bot

Um bot para Discord que permite aos usuários adicionar objetivos, acompanhar o tempo restante para cada objetivo e visualizar o ranking dos usuários mais ativos.

## Funcionalidades

- `/scout objetivo mapa tempo`: Adiciona um objetivo (ex: `/scout orb roxo longfen arms 01:45`)
- `/tracker`: Lista todos os objetivos pendentes, mostrando timer e quem adicionou.
- `/rank`: Mostra o ranking dos usuários que mais adicionaram objetivos.
- `/rr`: Reseta o ranking dos usuários (apenas administradores).

## Como usar

1. Instale as dependências:
   ```bash
   pip install -U discord.py
   ```

2. Configure o bot no [Discord Developer Portal](https://discord.com/developers/applications) e obtenha o token.

3. Insira o token no arquivo `bot.py`:
   ```python
   bot.run("SEU_TOKEN_AQUI")
   ```

4. Execute o bot:
   ```bash
   python bot.py
   ```

## Observações

- funções futuras podem ser adicionadas então lembre-se de manter seu download atualizado.

---

Feito por Rafhael Hanry (ChampionOfPiaui)
