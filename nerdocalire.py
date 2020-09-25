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

try:
    conn = mariadb.connect(
        user=mariadbUser,
        password=mariadbPassword,
        host=mariadbHost,
        port=mariadbPort,
        database=mariadbDatabase,
        autocommit=True
    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")

def start(update, context):
    user = update.message.from_user
    cur = conn.cursor()
    cur.execute("SELECT nerdocalissianoId, name FROM nerdocalissiani WHERE telegramUserId = ?", (user.id,))
    trovato = False
    for (nerdocalissianoId, name) in cur:
        trovato = True
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hey {name}! Sono il bot delle nerdocalire. Il tuo id utente telegram è {user.id}, mentre il tuo nerdocalissianoId è {nerdocalissianoId}')
    if(not trovato):
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hey! Sono il bot delle nerdocalire. Il tuo id utente telegram è {user.id}. Sembra tu non sia ancora un nerdocalissiano. Per diventare un nerdocalissiano, mandami /join seguito dal tuo nickname senza spazi.')

def join(update, context):
    if(len(context.args) != 1):
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Dovresti scrivermi /join seguito dal tuo nickname. Il nickname non può contenere spazi')
        return
    else:
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
def saldo(update, context):
    user = update.message.from_user
    cur = conn.cursor()
    cur.execute("SELECT SUM(t.nerdocalire) FROM transactions t INNER JOIN nerdocalissiani n ON t.nerdocalissianoId = n.nerdocalissianoId WHERE n.telegramUserId = ?", (user.id,))
    res = cur.fetchone()
    if res[0] == None:
        curr = 0
    else:
        curr = res[0]
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Il tuo saldo è di {curr} nerdocalire')

def ottieni(update, context):
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
def spendi(update, context):
    user = update.message.from_user
    if(len(context.args) < 2):
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Dovresti scrivermi /spendi seguito dal numero di nerdocalire e dalla ragione per cui vuoi spenderle.')
        return
    else:
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
def storia(update, context):
    user = update.message.from_user
    s = "Queste sono le tue ultime 10 transazioni:"
    cur = conn.cursor()
    cur.execute("SELECT t.nerdocalire, t.reason, t.tdate FROM transactions t INNER JOIN nerdocalissiani n on t.nerdocalissianoId = n.nerdocalissianoId WHERE telegramUserId = ? ORDER BY transactionId DESC LIMIT 10", (user.id,))
    all = cur.fetchall()
    for (nerdocalire, reason, date) in all:
        s += f'\nIl giorno {date} hai {"speso" if nerdocalire < 0 else "ottenuto"} {abs(nerdocalire)} nerdocalire perché {reason}'
    context.bot.send_message(chat_id=update.effective_chat.id, text=s)
def karma(update, context):
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
def chisono(update, context):
    user = update.message.from_user
    cur = conn.cursor()
    cur.execute("SELECT name FROM nerdocalissiani WHERE telegramUserId = ?", (user.id,))
    val = cur.fetchone()
    if val[0] == None:
        nome = "uno sconosciuto"
    else:
        nome = val[0]
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Sei {nome}')
def skarma(update, context):
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
def ping(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'/pong')
    

    

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO)
updater = Updater(token = token, use_context = True)
dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
join_handler = CommandHandler('join', join)
saldo_handler = CommandHandler('saldo', saldo)
ottieni_handler = CommandHandler('ottieni', ottieni)
spendi_handler = CommandHandler('spendi', spendi)
storia_handler = CommandHandler('storia', storia)
karma_handler = CommandHandler('karma', karma)
chisono_handler = CommandHandler('chisono', chisono)
skarma_handler = CommandHandler('skarma', skarma)
ping_handler = CommandHandler('ping', ping)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(join_handler)
dispatcher.add_handler(saldo_handler)
dispatcher.add_handler(spendi_handler)
dispatcher.add_handler(ottieni_handler)
dispatcher.add_handler(storia_handler)
dispatcher.add_handler(karma_handler)
dispatcher.add_handler(chisono_handler)
dispatcher.add_handler(skarma_handler)
dispatcher.add_handler(ping_handler)

updater.start_polling()
