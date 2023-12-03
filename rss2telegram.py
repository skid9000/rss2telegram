#!/usr/bin/env python3
#-*- coding: utf-8 -*-
import feedparser
import logging
import sqlite3
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from pathlib import Path

config = Path("./config.py")
try:
    config.resolve(strict=True)
except FileNotFoundError:
    print("Please copy config.py.sample to config.py and fill the properties.")
    exit()


import config

rss_dict = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# SQLITE
def sqlite_connect():
    global conn
    conn = sqlite3.connect('rss.db', check_same_thread=False)


def sqlite_load_all():
    sqlite_connect()
    c = conn.cursor()
    c.execute('SELECT * FROM rss')
    rows = c.fetchall()
    conn.close()
    return rows


def sqlite_write(name, link, last):
    sqlite_connect()
    c = conn.cursor()
    q = [(name), (link), (last)]
    c.execute('''INSERT INTO rss('name','link','last') VALUES(?,?,?)''', q)
    conn.commit()
    conn.close()


# RSS
def rss_load():
    # if the dict is not empty, empty it.
    if bool(rss_dict):
        rss_dict.clear()

    for row in sqlite_load_all():
        rss_dict[row[0]] = (row[1], row[2])


async def cmd_rss_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if bool(rss_dict) is False:
        await update.message.reply_text("The database is empty")
    else:
        for title, url_list in rss_dict.items():
            await update.message.reply_text(
                "Title: " + title +
                "\nRSS url: " + url_list[0] +
                "\nLast checked article: " + url_list[1])


async def cmd_rss_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # try if there are 2 arguments passed
    try:
        context.args[1]
    except IndexError:
        await update.message.reply_text("ERROR: The format needs to be: /add <title> <link>")
        raise
    # try if the url is a valid RSS feed
    try:
        rss_d = feedparser.parse(context.args[1])
        rss_d.entries[0]['title']
    except IndexError:
        await update.message.reply_text(
            "ERROR: The link does not seem to be a RSS feed or is not supported")
        raise
    sqlite_write(context.args[0], context.args[1], str(rss_d.entries[0]['link']))
    rss_load()
    await update.message.reply_text("Added \nTITLE: %s\nRSS: %s" % (context.args[0], context.args[1]))
    print("Added \nTITLE: %s\nRSS: %s" % (context.args[0], context.args[1]))


async def cmd_rss_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    name = str(context.args[0])
    try:
        c.execute('DELETE FROM rss WHERE name = ?', [name])
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print('Error %s:' % e)
    rss_load()
    await update.message.reply_text("Removed: " + name)
    print("Removed: " + name)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "RSS to Telegram bot" +
        "\n\nAfter successfully adding a RSS link, the bot starts fetching the feed every "
         + str(config.delay) + " seconds. (This can be set in config.py) ⏰⏰⏰" +
        "\n\nTitles are used to easily manage RSS feeds and need to contain only one word 📝📝📝" +
        "\n\nCommands:" +
        "\n/help Posts this help message." +
        "\n/add <title> <link> To add a RSS feed in database." +
        "\n/remove <title> Remove a RSS feed from database."
        "\n/list Lists all the titles and the RSS feeds links from the DB.")


async def rss_monitor(context: ContextTypes.DEFAULT_TYPE):
    for name, url_list in rss_dict.items():
        rss_d = feedparser.parse(url_list[0])
        if (url_list[1] != rss_d.entries[0]['link']):
            print("New RSS update for " + name + ", updating database...")
            conn = sqlite3.connect('rss.db')
            q = [(str(rss_d.entries[0]['link'])), (name)]
            c = conn.cursor()
            c.execute('''UPDATE rss SET 'last' = ? WHERE name=? ''', q)
            conn.commit()
            conn.close()
            rss_load()
            print("Sending RSS update to Telegram...")
            await context.bot.send_message(config.chatid, rss_d.entries[0]['link'])
            print("Success.")


def init_sqlite():
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE rss (name text, link text, last text)''')


def main() -> None:
    dp = Application.builder().token(config.Token).build()

    dp.add_handler(CommandHandler("add", cmd_rss_add))
    dp.add_handler(CommandHandler("help", cmd_help))
    dp.add_handler(CommandHandler("start", cmd_help))
    dp.add_handler(CommandHandler("list", cmd_rss_list))
    dp.add_handler(CommandHandler("remove", cmd_rss_remove))

    #dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


    db = Path("./rss.db")
    try:
        db.resolve(strict=True)
    except FileNotFoundError:
        print("Database not found, trying to create a new one.")
        try:
            init_sqlite()
        except Exception as e:
            print("Error when creating database : ", e.message, e.args)
            pass
        else:
            print("Success.")

    rss_load()
    print("Running RSS Monitor.")

    dp.job_queue.run_repeating(rss_monitor, config.delay)
    dp.run_polling(allowed_updates=Update.ALL_TYPES)
    conn.close()


if __name__ == '__main__':
    main()
