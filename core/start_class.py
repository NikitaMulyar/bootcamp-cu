import aiohttp

from core.yandex_api_functions import get_text_retelling, get_img, get_text_category

from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, ContextTypes


class BotClass:
    async def menu(self):
        classes = [[InlineKeyboardButton('🗳️ Краткое содержание текста', callback_data='pp1')],
                   [InlineKeyboardButton('🖼️ Генерация изображения по тексту', callback_data='pp2')],
                   [InlineKeyboardButton('🗃️ Определение жанра текста', callback_data='pp3')],
                   [InlineKeyboardButton('🗂 AI ассистент', callback_data='pp4')]]
        return InlineKeyboardMarkup(classes)

    async def stop(self):
        classes = [[InlineKeyboardButton('️📥 Начать обучение', callback_data='study')]]
        return InlineKeyboardMarkup(classes)

    async def stop_dialog(self):
        classes = [[InlineKeyboardButton('️⛔️ Завершить диалог', callback_data='end_dialog')]]
        return InlineKeyboardMarkup(classes)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('🔮 Привет-привет!\nДавно искал бесплатного ИИ-помощника? Ты обратился по адресу!',
                                        reply_markup=await self.menu())
        return 1

    async def get_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        context.user_data['used'] = query.data
        text = '▶️ *Краткое содержание текста*\n\nПрисылай текст\, и я перескажу его тебе\!'

        if query.data == 'pp2':
            text = ('▶️ *Генерация изображения по тексту*\n\nВключи свою фантазию на максимум\: '
                    'опиши\, какую картинку ты хочешь\!')
        elif query.data == 'pp3':
            text = '▶️ *Определение жанра текста*\n\nПрисылай текст\, и я скажу\, к каким категориям он относится\!'
        elif query.data == 'pp4':
            text = '▶️ *AI ассистент*\n\nПрисылай файлы или ссылки на веб\-страницы\, и я смогу навигировать по ним тебя\!'

        if query.message.photo:
            await context.bot.send_message(query.message.chat.id, text, parse_mode='MarkdownV2')
        else:
            await query.edit_message_text(text, parse_mode='MarkdownV2')
        if query.data == 'pp4':
            context.user_data['list'] = []
            return 3
        return 2

    async def process_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('⏳ Идет обработка ответа...')
        text = update.message.text
        attempts = 3
        if context.user_data['used'] == 'pp1':
            while attempts > 0:
                try:
                    res = await get_text_retelling(text)
                    await update.message.reply_text('✅ Готово!\n\n' + res, reply_markup=await self.menu())
                    context.user_data.clear()
                    return 1
                except Exception as e:
                    print(e)
                    attempts -= 1
        elif context.user_data['used'] == 'pp2':
            while attempts > 0:
                try:
                    res = await get_img(text)
                    await update.message.reply_photo(res, caption='✅ Готово!', reply_markup=await self.menu())
                    context.user_data.clear()
                    return 1
                except Exception as e:
                    print(e)
                    attempts -= 1
        elif context.user_data['used'] == 'pp3':
            while attempts > 0:
                try:
                    res = await get_text_category(text)
                    await update.message.reply_text('✅ Готово!\n\n' + res, reply_markup=await self.menu())
                    context.user_data.clear()
                    return 1
                except Exception as e:
                    print(e)
                    attempts -= 1
        await update.message.reply_text('⚠️ К сожалению, не удалось обработать запрос',
                                        reply_markup=await self.menu())
        context.user_data.clear()
        return 1

    async def get_urls(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            session = aiohttp.ClientSession()
            async with session.get(update.message.text) as response:
                res = await response.text()
                context.user_data['list'].append(res)
                await update.message.reply_text('✅ Материал успешно загружен', reply_markup=await self.stop())
        except Exception as e:
            await update.message.reply_text('⚠️ К сожалению, не удалось обработать запрос. Загрузка продолжается',
                                            reply_markup=await self.stop())
        return 3

    async def get_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(update.message)
        return 3

    async def process_study(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('⏳ Идет обучение...')
        return 3

    async def end(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('⚠️ Выход', reply_markup=await self.menu())
        context.user_data.clear()
        return ConversationHandler.END
