from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, ContextTypes

import email_validator
from core.database.models.db_helper import db_helper
from core.database.models.user import User
from sqlalchemy import select


class RegClass:
    state_email = 1
    state_fio = 2
    state_experience = 3
    state_speciality = 4
    state_place = 5

    async def menu(self):
        classes = [
            [InlineKeyboardButton("🗳️ Получить совет", callback_data="advice")],
            [
                InlineKeyboardButton(
                    "🗂 Получить вопросы для тренировки",
                    callback_data="questions",
                )
            ],
            [
                InlineKeyboardButton(
                    "🗃️ Анализировать речь", callback_data="speech"
                )
            ],
            [InlineKeyboardButton("🎧 Аудио эссе", callback_data="essay")],
        ]
        return InlineKeyboardMarkup(classes)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = await db_helper.get_session()
        stmt = select(User).where(User.id == update.message.from_user.id)
        user_exists = (await session.execute(stmt)).scalar_one_or_none()

        if user_exists:
            await update.message.reply_text(
                f"✅ {user_exists.fio}, ты уже есть в системе!",
                reply_markup=await self.menu(),
            )
            await session.close()
            return ConversationHandler.END
        context.user_data["register"] = {}
        await update.message.reply_text(
            "🔮 Привет-привет!\n"
            "Я - твой ассистент в непростом пути к преподаванию.\n"
            "Ты можешь просить советы и тренировать питчинг, присылая мне голосовые,"
            "а я дам тебе основанные на ней советы, как сделать речь лучше!\n\n"
            "Но сначала нужно пройти регистрацию. Пожалуйста, введи свой адрес эл. почты"
        )
        await session.close()
        return self.state_email

    async def get_email(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        email = update.message.text
        try:
            email_validator.validate_email(email, check_deliverability=True)

            session = await db_helper.get_session()
            stmt = select(User).where(User.email == email)
            user_exists = (await session.execute(stmt)).scalar_one_or_none()

            if user_exists:
                await update.message.reply_text(
                    "⚠️ Данный адрес уже занят - попробуй еще разок!"
                )
                await session.close()
                return self.state_email

            context.user_data["register"]["email"] = email
            await update.message.reply_text(
                "✅ Записал! Теперь напиши свои ФИО"
            )
            await session.close()
            return self.state_fio
        except email_validator.EmailNotValidError:
            await update.message.reply_text(
                "⚠️ Некорректный адрес - попробуй еще разок!"
            )
            return self.state_email

    async def get_fio(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        fio = update.message.text
        context.user_data["register"]["fio"] = fio
        await update.message.reply_text(
            "✅ Записал! Теперь напиши свой опыт работы"
        )
        return self.state_experience

    async def get_experience(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        experience = update.message.text
        context.user_data["register"]["experience"] = experience
        await update.message.reply_text(
            "✅ Записал! Теперь напиши свою специальность"
        )
        return self.state_speciality

    async def get_speciality(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        speciality = update.message.text
        context.user_data["register"]["speciality"] = speciality
        await update.message.reply_text(
            "✅ Записал! Теперь напиши, где и кем ты планируешь работать"
        )
        return self.state_place

    async def get_place(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        place = update.message.text
        context.user_data["register"]["place"] = place

        session = await db_helper.get_session()
        user = User(
            **context.user_data["register"], id=update.message.from_user.id
        )
        session.add(user)
        await session.commit()
        await session.close()

        context.user_data.clear()
        await update.message.reply_text(
            "✅ Зарегистрировал!", reply_markup=await self.menu()
        )
        return ConversationHandler.END

    async def end(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⚠️ Регистрация прервана")
        context.user_data.clear()
        return ConversationHandler.END
