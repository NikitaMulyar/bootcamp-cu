import aiohttp

from core.database.models import db_helper, User
from core.yandex_api_functions import get_ans_by_assist, get_stt, get_text
from sqlalchemy import select

from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, ContextTypes


class BotClass:
    state_audio = 1

    async def menu(self):
        classes = [[InlineKeyboardButton('🗳️ Получить совет', callback_data='advice')],
                   [InlineKeyboardButton('🗂 Получить вопросы для тренировки', callback_data='questions')],
                   [InlineKeyboardButton('🗃️ Анализировать речь', callback_data='speech')]]
        return InlineKeyboardMarkup(classes)

    async def get_advice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text('⏳ Идет обработка...')

        session = await db_helper.get_session()
        stmt = (select(User).where(User.id == query.from_user.id))
        user = (await session.execute(stmt)).scalar_one_or_none()

        try:
            res = await get_ans_by_assist(user.experience, user.speciality, user.place)
            for i in range(0, len(res), 2000):
                await context.bot.send_message(query.message.chat.id, res[i:i + 2000])
            await context.bot.send_message('✅ Готово!', reply_markup=await self.menu())
        except Exception as e:
            print(e)
            await query.edit_message_text(f'⚠️ К сожалению, не удалось обработать запрос',
                                          reply_markup=await self.menu())
        await session.close()

    async def choose_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text('Присылай аудиосообщение, чтобы я мог прослушать его и дать рекомендации '
                                      'по ее улучшении')
        return self.state_audio

    async def get_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = await db_helper.get_session()
        stmt = (select(User).where(User.id == update.message.from_user.id))
        user = (await session.execute(stmt)).scalar_one_or_none()

        await update.message.reply_text('⏳ Идет обработка...')
        file = await update.message.voice.get_file()
        file_path = f'core/audio_files/{update.message.from_user.id}.ogg'
        await file.download_to_drive(file_path)
        try:
            res = await get_stt(file_path)
            await update.message.reply_text(res)
            advice = await get_text(res, f'опыт: {user.experience}, специальность: {user.experience},'
                                         f'место работы: {user.place}', update)
            for i in range(0, len(advice), 2000):
                await update.message.reply_text(advice[i:i + 2000])
            await update.message.reply_text('✅ Готово!', reply_markup=await self.menu())
        except Exception as e:
            print(e)
            await update.message.reply_text(f'⚠️ К сожалению, не удалось обработать запрос: {e}',
                                            reply_markup=await self.menu())

        await session.close()
        return ConversationHandler.END

    async def end(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('⚠️ Диалог прерван')
        context.user_data.clear()
        return ConversationHandler.END
