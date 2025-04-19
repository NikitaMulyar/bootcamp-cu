import asyncio
import gc
import os

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)

from core.database.models import db_helper, Base
from core.reg_class import RegClass
from core.start_class import BotClass

gc.enable()
load_dotenv()

os.environ["TZ"] = "Europe/Moscow"


async def make_tables():
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def main():
    asyncio.gather(make_tables())
    application = (
        Application.builder()
        .token(os.getenv("TELEGRAM_BOT_TOKEN"))
        .connection_pool_size(2048)
        .read_timeout(10)
        .write_timeout(10)
        .connect_timeout(10)
        .pool_timeout(10)
        .concurrent_updates(True)
        .get_updates_connect_timeout(10)
        .get_updates_connection_pool_size(10)
        .get_updates_pool_timeout(10)
        .get_updates_read_timeout(10)
        .get_updates_write_timeout(10)
        .build()
    )
    register_class = RegClass()
    reg_handler = ConversationHandler(
        entry_points=[CommandHandler("start", register_class.start)],
        states={
            register_class.state_email: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, register_class.get_email
                )
            ],
            register_class.state_fio: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, register_class.get_fio
                )
            ],
            register_class.state_experience: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    register_class.get_experience,
                )
            ],
            register_class.state_speciality: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    register_class.get_speciality,
                )
            ],
            register_class.state_place: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, register_class.get_place
                )
            ],
        },
        fallbacks=[CommandHandler("end", register_class.end)],
    )

    botcl = BotClass()
    get_advice = CallbackQueryHandler(botcl.get_advice, pattern=r"advice")
    advice_audio_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(botcl.choose_audio, pattern=r"speech"),
            CallbackQueryHandler(botcl.get_questions, pattern=r"questions"),
            CallbackQueryHandler(botcl.get_essay, pattern=r"essay"),
        ],
        states={
            botcl.state_audio: [
                MessageHandler(filters.VOICE, botcl.get_audio)
            ],
            botcl.state_audio_essay: [
                MessageHandler(filters.VOICE, botcl.save_essay)
            ],
        },
        fallbacks=[CommandHandler("end", botcl.end)],
    )

    application.add_handlers(
        handlers={1: [reg_handler], 2: [get_advice], 3: [advice_audio_handler]}
    )

    application.run_polling()


if __name__ == "__main__":
    main()
