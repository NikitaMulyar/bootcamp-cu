import argparse
import asyncio
import datetime
import gc
import logging
import os
import time

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler,
                          ConversationHandler, TypeHandler)

from core.start_class import BotClass

gc.enable()
load_dotenv()

logging.basicConfig(
    filename='logs.log', filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING,
    encoding='utf-8'
)

logger = logging.getLogger(__name__)
os.environ['TZ'] = "Europe/Moscow"


def main():
    application = (Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).connection_pool_size(2048).read_timeout(10)
                   .write_timeout(10).connect_timeout(10).pool_timeout(10).concurrent_updates(True)
                   .get_updates_connect_timeout(10).get_updates_connection_pool_size(10)
                   .get_updates_pool_timeout(10).get_updates_read_timeout(10)
                   .get_updates_write_timeout(10).build())

    config_ex = BotClass()
    ex_handler = ConversationHandler(
        entry_points=[CommandHandler('start', config_ex.start)],
        states={
            1: [CallbackQueryHandler(config_ex.get_request, pattern=r'(pp1|pp2|pp3|pp4)')],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, config_ex.process_query)],
        },
        fallbacks=[CommandHandler('end', config_ex.end)]
    )

    application.add_handlers(handlers={1: [ex_handler]})

    application.run_polling()


if __name__ == '__main__':
    main()
