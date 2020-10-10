from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import mariadb
import os

token = os.environ['NERDOCALIREBOT_TOKEN']
mariadbUser = os.environ['NERDOCALIREBOT_MARIADB_USER']
mariadbPassword = os.environ['NERDOCALIREBOT_MARIADB_PASSWORD']
mariadbHost = os.environ['NERDOCALIREBOT_MARIADB_HOST']
mariadbPort = int(os.environ['NERDOCALIREBOT_MARIADB_PORT'])
mariadbDatabase = os.environ['NERDOCALIREBOT_MARIADB_DATABASE']

adminIds = list(map(lambda a: int(a), os.environ['NERDOCALIREBOT_ADMIN_USERIDS'].split(",")))

def connect_database(update = None, context = None):
    try:
        conn = mariadb.connect(
            user=mariadbUser,
            password=mariadbPassword,
            host=mariadbHost,
            port=mariadbPort,
            database=mariadbDatabase,
            autocommit=True
        )
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        if update != None and context != None:
            if update.message.from_user.id in adminIds:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Ho ricevuto un errore nel connettermi al database: {e}')
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'C''è stato un errore, riprova più tardi')



def chester_info(update, context):
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hey, probabilmente questo messaggio non ti interessa. In ogni caso, mi risulta che il tuo user id sia {user.id} e che tu mi stia scrivendo nella chat di id {update.effective_chat.id}')

def start(update, context):
    conn = connect_database(update, context)
    try:
        user = update.message.from_user
        cur = conn.cursor()
        cur.execute("SELECT nerdocalissianoId, name FROM nerdocalissiani WHERE telegramUserId = ?", (user.id,))
        trovato = False
        for (nerdocalissianoId, name) in cur:
            trovato = True
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hey {name}! Sono il bot delle nerdocalire. Il tuo id utente telegram è {user.id}, mentre il tuo nerdocalissianoId è {nerdocalissianoId}')
        if(not trovato):
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hey! Sono il bot delle nerdocalire. Il tuo id utente telegram è {user.id}. Sembra tu non sia ancora un nerdocalissiano. Per diventare un nerdocalissiano, mandami /join seguito dal tuo nickname senza spazi.')
    finally:
        conn.close()

def join(update, context):
    if(len(context.args) != 1):
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Dovresti scrivermi /join seguito dal tuo nickname. Il nickname non può contenere spazi')
        return
    else:
        conn = connect_database(update, context)
        try:
            user = update.message.from_user
            desiredNickname = context.args[0]
            cur = conn.cursor()
            cur.execute("SELECT nerdocalissianoId, name FROM nerdocalissiani WHERE telegramUserId = ?", (user.id,))
            trovato = False
            for (nerdocalissianoId, name) in cur:
                trovato = True
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Sei già un nerdocalissiano, il tuo nickname è {name} e il tuo nerdocalissianoId è {nerdocalissianoId}. Il tuo id utente telegram è {user.id}')
            if(not trovato):
                cur.execute("INSERT INTO nerdocalissiani (name, telegramUserId, telegramUsername) VALUES (?, ?, ?)", (desiredNickname, user.id, user.username))
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Complimenti! Ora sei un nerdocalissiano. Il tuo nerdocalissianoId è {cur.lastrowid}')
        finally:
            conn.close()
def saldo(update, context):
    conn = connect_database(update, context)
    try:
        user = update.message.from_user
        cur = conn.cursor()
        cur.execute("SELECT SUM(t.nerdocalire) FROM transactions t INNER JOIN nerdocalissiani n ON t.nerdocalissianoId = n.nerdocalissianoId WHERE n.telegramUserId = ?", (user.id,))
        res = cur.fetchone()
        if res[0] == None:
            curr = 0
        else:
            curr = res[0]
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Il tuo saldo è di {curr} nerdocalire')
    finally:
        conn.close()

def ottieni(update, context):
    conn = connect_database(update, context)
    try:
        user = update.message.from_user
        if(len(context.args) < 2):
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Dovresti scrivermi /ottieni seguito dal numero di nerdocalire e dalla ragione per cui vuoi ottenerle.')
            return
        else:
            nerdocalire = int(context.args[0])
            if nerdocalire <= 0:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Puoi ottenere solo quantità positive di nerdocalire')
                return
            reason = ' '.join(context.args[1:])
            cur = conn.cursor()
            cur.execute("INSERT INTO transactions (nerdocalissianoId, nerdocalire, reason, tdate) SELECT nerdocalissianoId, ?, ?, UTC_TIMESTAMP() FROM nerdocalissiani WHERE telegramUserId = ?", (nerdocalire, reason, user.id))
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Ti ho dato {nerdocalire} nerdocalire perché {reason}')
    finally:
        conn.close()
def spendi(update, context):
    user = update.message.from_user
    if(len(context.args) < 2):
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Dovresti scrivermi /spendi seguito dal numero di nerdocalire e dalla ragione per cui vuoi spenderle.')
        return
    else:
        conn = connect_database(update, context)
        try:
            nerdocalire = int(context.args[0])
            if nerdocalire <= 0:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Puoi spendere solo quantità positive di nerdocalire')
                return
            reason = ' '.join(context.args[1:])
            cur = conn.cursor()
            cur.execute("SELECT SUM(t.nerdocalire) FROM transactions t INNER JOIN nerdocalissiani n ON t.nerdocalissianoId = n.nerdocalissianoId WHERE n.telegramUserId = ?", (user.id,))
            curNerdocalire = cur.fetchone()
            actNerdocalire = 0
            if(curNerdocalire[0] != None):
                actNerdocalire = curNerdocalire[0]
            if(actNerdocalire - nerdocalire < 0):
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hai solo {actNerdocalire} nerdocalire, non puoi spenderne {nerdocalire}')
            else:
                cur.execute("INSERT INTO transactions (nerdocalissianoId, nerdocalire, reason, tdate) SELECT nerdocalissianoId, ?, ?, UTC_TIMESTAMP() FROM nerdocalissiani WHERE telegramUserId = ?", (-nerdocalire, reason, user.id))
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hai speso {nerdocalire} nerdocalire perché {reason}')
        finally:
            conn.close()
def storia(update, context):
    conn = connect_database(update, context)
    try:
        user = update.message.from_user
        s = "Queste sono le tue ultime 10 transazioni:"
        cur = conn.cursor()
        cur.execute("SELECT t.nerdocalire, t.reason, t.tdate FROM transactions t INNER JOIN nerdocalissiani n on t.nerdocalissianoId = n.nerdocalissianoId WHERE telegramUserId = ? ORDER BY transactionId DESC LIMIT 10", (user.id,))
        all = cur.fetchall()
        for (nerdocalire, reason, date) in all:
            s += f'\nIl giorno {date} hai {"speso" if nerdocalire < 0 else "ottenuto"} {abs(nerdocalire)} nerdocalire perché {reason}'
        context.bot.send_message(chat_id=update.effective_chat.id, text=s)
    finally:
        conn.close()
def karma(update, context):
    conn = connect_database(update, context)
    try:
        if(len(context.args) == 0):
            user = update.message.from_user
            cur = conn.cursor()
            cur.execute("SELECT karma FROM nerdocalissiani WHERE telegramUserId = ?", (user.id,))
            res = cur.fetchone()
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hai {res[0]} karma')
        else:
            user = update.message.from_user
            cur = conn.cursor()
            target = context.args[0]
            if target.startswith("@"):
                cur.execute("UPDATE nerdocalissiani SET karma = karma + 1 WHERE telegramUsername = ? AND telegramUserId <> ?", (target[1:], user.id))
            else:
                cur.execute("UPDATE nerdocalissiani SET karma = karma + 1 WHERE name = ? AND telegramUserId <> ?", (target, user.id))
            if cur.rowcount > 0:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hai dato un karma a {target}')
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Non ho trovato {target}')
    finally:
        conn.close()
def chisono(update, context):
    conn = connect_database(update, context)
    try:
        user = update.message.from_user
        cur = conn.cursor()
        cur.execute("SELECT name FROM nerdocalissiani WHERE telegramUserId = ?", (user.id,))
        val = cur.fetchone()
        if val[0] == None:
            nome = "uno sconosciuto"
        else:
            nome = val[0]
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Sei {nome}')
    finally:
        conn.close()
def skarma(update, context):
    conn = connect_database(update, context)
    try:
        user = update.message.from_user
        cur = conn.cursor()
        target = context.args[0]
        if target.startswith("@"):
            cur.execute("UPDATE nerdocalissiani SET karma = karma - 1 WHERE telegramUsername = ? AND telegramUserId <> ?", (target[1:], user.id))
        else:
            cur.execute("UPDATE nerdocalissiani SET karma = karma - 1 WHERE name = ? AND telegramUserId <> ?", (target, user.id))
        if cur.rowcount > 0:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hai skarmato {target}')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Non ho trovato {target}')
    finally:
        conn.close()
def ping(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'/pong')
    

    

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO)
updater = Updater(token = token, use_context = True)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('join', join))
dispatcher.add_handler(CommandHandler('saldo', saldo))
dispatcher.add_handler(CommandHandler('ottieni', ottieni))
dispatcher.add_handler(CommandHandler('spendi', spendi))
dispatcher.add_handler(CommandHandler('storia', storia))
dispatcher.add_handler(CommandHandler('karma', karma))
dispatcher.add_handler(CommandHandler('chisono', chisono))
dispatcher.add_handler(CommandHandler('skarma', skarma))
dispatcher.add_handler(CommandHandler('ping', ping))
dispatcher.add_handler(CommandHandler('chester_info', chester_info))

updater.start_polling()
