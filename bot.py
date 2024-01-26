import sqlite3
import time
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, \
						Text, OpenLink, Location, EMPTY_KEYBOARD
from config import *

with sqlite3.connect("database.db") as db:
	cursor = db.cursor()
	cursor.executescript(creationQuery)

BLACKLISTED_MSG = "⛔️ Ты находишься в блек-листе дружок."
NORIGHTS_MSG = "⛔️ Прав у тебя нет, дружок."
bot = Bot(token=groupToken)

async def sendLogMessage(msg):
	if isLogEnabled is True:
		await bot.api.messages.send(peer_id=1, message=msg, random_id=0) # change for your id
#32312
@bot.on.private_message(payload={"cmd": "menu"})
@bot.on.private_message(text=["Start", "Начать", "start", "начать", "меню", "menu"])
async def menu_handler(message: Message):
	vk = int(message.from_id)
	user = await bot.api.users.get(message.from_id)
	try:
		db = sqlite3.connect("database.db")
		cursor = db.cursor()
		isUserRegistered = cursor.execute("SELECT vk FROM users WHERE vk = ?", [vk]).fetchone()
		if isUserRegistered is None:
			cursor.execute("INSERT INTO users(vk,name) VALUES(?,?)", [vk, user[0].first_name])
			db.commit()
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) was registered")
		isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
		isHelper = cursor.execute("SELECT isHelper FROM users WHERE vk = ?", [vk]).fetchone()
	except sqlite3.Error as e:
		print("Error ", e)
	finally:
		cursor.close()
		db.close()
	if (isAdmin[0] != 1 or isHelper[0] != 1 or None):
		keyboard = Keyboard(one_time=True).add(Text("Оставить заявку на получение аккаунта", {"cmd": "giveacc"}), color=KeyboardButtonColor.PRIMARY).row().add(Text("Посмотреть копирайты", {"cmd": "copyrights"}), color=KeyboardButtonColor.PRIMARY)
		return await message.answer("⌛ Открываю меню.", keyboard=keyboard)
	if (isHelper[0] == 1 and isAdmin[0] != 1):
		keyboard = Keyboard(one_time=True).add(Text("Оставить заявку на получение аккаунта", {"cmd": "giveacc"}), color=KeyboardButtonColor.PRIMARY).row().add(Text("Посмотреть копирайты", {"cmd": "copyrights"}), color=KeyboardButtonColor.PRIMARY).row().add(Text("Что умеет хелпер?", {"cmd": "hhelp"}), color=KeyboardButtonColor.POSITIVE)
		return await message.answer("⌛ Открываю меню.", keyboard=keyboard)
	if (isAdmin[0] == 1):
		keyboard = Keyboard(one_time=True).add(Text("Оставить заявку на получение аккаунта", {"cmd": "giveacc"}), color=KeyboardButtonColor.PRIMARY).row().add(Text("Посмотреть копирайты", {"cmd": "copyrights"}), color=KeyboardButtonColor.PRIMARY).row().add(Text("Что умеет хелпер?", {"cmd": "hhelp"}), color=KeyboardButtonColor.POSITIVE).add(Text("Что умеет админ?", {"cmd": "ahelp"}), color=KeyboardButtonColor.NEGATIVE)
		return await message.answer("⌛ Открываю меню.", keyboard=keyboard)

@bot.on.private_message(payload={"cmd": "giveacc"})
async def giveacc_handler(message: Message):
	user = await bot.api.users.get(message.from_id)
	vk = int(message.from_id)
	try:
		db = sqlite3.connect("database.db")
		cursor = db.cursor()
		isBlacklisted = cursor.execute("SELECT vk FROM blacklist WHERE vk = ?", [vk]).fetchone()
		isHaveEnoughBalance = cursor.execute("SELECT balance FROM users WHERE vk = ?", [vk]).fetchone()
		if isBlacklisted is None:
			if(isHaveEnoughBalance[0] > 0):
				keyboard = Keyboard(one_time=True).add(Text("Вернуться в главное меню", {"cmd": "menu"}), color=KeyboardButtonColor.NEGATIVE)
				await message.answer("✅ Запрос на получение аккаунта отправлен.", keyboard=keyboard)
				await bot.api.messages.send(peer_id=341233861, message=f"❗️ @id{message.from_id}({user[0].first_name} {user[0].last_name}) просит выдать ему аккаунт.\n\n⚠️ !give {message.from_id} [acc] [hours] [punish] для выдачи;\n⚠️ !refuse {message.from_id} [reason] для отказа.", random_id=0)
			else:
				keyboard = Keyboard(one_time=True).add(Text("Как заработать сторики?", {"cmd": "howToEarn"}), color=KeyboardButtonColor.PRIMARY).row().add(Text("Вернуться в главное меню", {"cmd": "menu"}), color=KeyboardButtonColor.NEGATIVE)
				return await message.answer(f"⛔️ Недостаточно сториков на балансе.\n\n💹 Курс обмена: 1 сторик = 1 аккаунт\n💳 На счёте: {isHaveEnoughBalance[0]} сториков", keyboard=keyboard)
		else:
			return await message.answer(BLACKLISTED_MSG)
	except sqlite3.Error as e:
		print("Error ", e)
	finally:
		cursor.close()
		db.close()

	"""
	user = await bot.api.users.get(message.from_id)
	if message.from_id in list(map(int, blacklist)):
		return await message.answer(BLACKLISTED_MSG)
	keyboard = Keyboard(one_time=True).add(Text("Вернуться в главное меню", {"cmd": "menu"}), color=KeyboardButtonColor.NEGATIVE)
	await message.answer("✅ Запрос на получение аккаунта отправлен.", keyboard=keyboard)
	await bot.api.messages.send(peer_id=341233861, message=f"❗️ @id{message.from_id}({user[0].first_name} {user[0].last_name}) просит выдать ему аккаунт.\n\n⚠️ !give {message.from_id} [acc] [hours] [punish] для выдачи;\n⚠️ !refuse {message.from_id} [reason] для отказа.", random_id=0)
	"""

@bot.on.private_message(text=["!give <id> <acc> <hours> <punish>", "!give"]) # отдать акк
async def give_handler(message: Message, id=None, acc=None, hours=None, punish=None):
	vk = int(message.from_id)
	tmpid = int(id)
	user = await bot.api.users.get(message.from_id)
	try:
		db = sqlite3.connect("database.db")
		cursor = db.cursor()
		isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
		if (isAdmin[0] != 1 or None):
			await message.answer(NORIGHTS_MSG)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) trying use: command !give ({id}, {acc}, {hours}, {punish})")
			return
		else:
			if id and acc and hours and punish is not None:
				await bot.api.messages.send(peer_id=tmpid, message=f"🎉 Поздравляем, ваша заявка на выдачу аккаунта одобрена!\n\n{acc} (формат nick:pass) имеет {hours} отыгранных часов, {punish}.", random_id=0)
				cursor.execute("UPDATE users SET balance = balance - 1 WHERE vk = ?", [tmpid])
				db.commit()
				await bot.api.messages.send(peer_id=tmpid, sticker_id=15623, random_id=0)
				await bot.api.messages.send(peer_id=message.from_id, sticker_id=63726, random_id=0)
				await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) used: command !give ({id}, {acc}, {hours}, {punish})")
			else:
				await bot.api.messages.send(peer_id=message.from_id, sticker_id=18464, random_id=0)
	except sqlite3.Error as e:
		print("Error ", e)
	finally:
		cursor.close()
		db.close()

@bot.on.private_message(text=["!refuse <id> <reason>", "!refuse"]) # не отдать акк
async def refuse_handler(message: Message, id=None, reason=None):
	vk = int(message.from_id)
	user = await bot.api.users.get(message.from_id)
	try:
		db = sqlite3.connect("database.db")
		cursor = db.cursor()
		isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
		if (isAdmin[0] != 1 or None):
			await message.answer(NORIGHTS_MSG)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) trying use: command !refuse ({id}, {reason})")
			return
		else:
			if id and reason is not None:
				await bot.api.messages.send(peer_id=id, message=f"❌ Вашу заявку на выдачу аккаунта отклонили.\n⚠️ Причина: {reason}", random_id=0)
				await bot.api.messages.send(peer_id=id, sticker_id=63061, random_id=0)
				await bot.api.messages.send(peer_id=message.from_id, sticker_id=63726, random_id=0)
				await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) used: command !refuse ({id}, {reason})")
			else:
				await bot.api.messages.send(peer_id=message.from_id, sticker_id=18464, random_id=0)
	except sqlite3.Error as e:
		print("Error ", e)
	finally:
		cursor.close()
		db.close()

@bot.on.private_message(payload={"cmd": "copyrights"})
async def copyrights_handler(message: Message):
	keyboard = Keyboard(one_time=True).add(Text("Вернуться в главное меню", {"cmd": "menu"}), color=KeyboardButtonColor.NEGATIVE)
	await message.answer("👨‍💻 Разработчик: @id341233861(Dust0n)\n🤖 При поддержке: @dust0n(Wonert Bots)", keyboard=keyboard)
	await bot.api.messages.send(peer_id=message.from_id, sticker_id=63752, random_id=0)

@bot.on.private_message(payload={"cmd": "howToEarn"})
async def howToEarn_handler(message: Message):
	keyboard = Keyboard(one_time=True).add(Text("Вернуться в главное меню", {"cmd": "menu"}), color=KeyboardButtonColor.NEGATIVE)
	await message.answer("📜 Список способов по заработку сториков:\n\n1️⃣. Опубликовать в нашей группе правдивую и хорошо написанную историю (с пруфами) - 1 сторик;\n2️⃣. Помочь идеей для бота (присылать @id341233861(ему), 1 идея = 1 сторик);\n3️⃣. Пожертвовать свой аккаунт с более чем тремя отыгранными часами (1 аккаунт = 1 сторик).", keyboard=keyboard)
	await bot.api.messages.send(peer_id=message.from_id, sticker_id=67070, random_id=0)

@bot.on.chat_message(text="!sendsticker <sid>")
async def fun_handler(message: Message, sid):
	vk = int(message.from_id)
	user = await bot.api.users.get(message.from_id)
	try:
		db = sqlite3.connect("database.db")
		cursor = db.cursor()
		isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
		if (isAdmin[0] != 1):
			await message.answer(NORIGHTS_MSG)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) trying use: command !sendsticker ({sid})")
			return
		else:
			await bot.api.messages.send(peer_id=2000000004, sticker_id=sid, random_id=0)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) used: command !sendsticker ({sid})")
	except sqlite3.Error as e:
		print("Error ", e)
	finally:
		cursor.close()
		db.close()

@bot.on.private_message(text="!permslist")
async def permslist_handler(message: Message):
	vk = int(message.from_id)
	user = await bot.api.users.get(message.from_id)
	try:
		db = sqlite3.connect("database.db")
		cursor = db.cursor()
		isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
		if (isAdmin[0] != 1 or None):
			await message.answer(NORIGHTS_MSG)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) trying use: command !permslist")
			return
		else:
			await message.answer("📜 Список прав:\n\n1️⃣ - взаимодействие с блек-листом;\n2️⃣ - полные привилегии управления ботом.\n\n‼️ Не рекомендуется выдавать полные привелегии управления ботом посторонним лицам!")
			await bot.api.messages.send(peer_id=message.from_id, sticker_id=8138, random_id=0)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) used: command !permslist")
	except sqlite3.Error as e:
		print("Error ", e)
	finally:
		cursor.close()
		db.close()

@bot.on.private_message(payload={"cmd": "ahelp"})
@bot.on.private_message(text="!ahelp")
async def ahelp_handler(message: Message):
	vk = int(message.from_id)
	user = await bot.api.users.get(message.from_id)
	try:
		db = sqlite3.connect("database.db")
		cursor = db.cursor()
		isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
		if (isAdmin[0] != 1 or None):
			await message.answer(NORIGHTS_MSG)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) trying use: command !ahelp")
			return
		else:
			keyboard = Keyboard(one_time=True).add(Text("Вернуться в главное меню", {"cmd": "menu"}), color=KeyboardButtonColor.NEGATIVE)
			await message.answer("📜 Список команд администратора:\n\n1️⃣. !ahelp - прочитать этот список;\n2️⃣. !permslist - посмотреть список прав;\n3️⃣. !giveperms [vk id (цифровой)] [permid] [new data (0/1)] - выдать права юзеру;\n4️⃣. !give [vk id (цифровой)] [acc] [hours] [punish] - одобрить заявку юзера;\n5️⃣. !refuse [vk id (цифровой)] [reason] - отклонить заявку юзера;\n6️⃣. !setbal [vk id (цифровой)] [count] - установить баланс юзеру;\n7️⃣. !bladd [vk id (цифровой)] - добавить юзера в блек-лист;\n8️⃣. !bldel [vk id (цифровой)] - убрать юзера из блек-листа;\n9️⃣. в разработке;\n🔟. в разработке.", keyboard=keyboard)
			await bot.api.messages.send(peer_id=message.from_id, sticker_id=8138, random_id=0)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) used: command !ahelp")
	except sqlite3.Error as e:
		print("Error ", e)
	finally:
		cursor.close()
		db.close()

@bot.on.private_message(payload={"cmd": "hhelp"})
@bot.on.private_message(text="!hhelp")
async def hhelp_handler(message: Message):
	vk = int(message.from_id)
	user = await bot.api.users.get(message.from_id)
	try:
		db = sqlite3.connect("database.db")
		cursor = db.cursor()
		isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
		isHelper = cursor.execute("SELECT isHelper FROM users WHERE vk = ?", [vk]).fetchone()
		if (isAdmin[0] != 1 or isHelper[0] != 1 or None):
			await message.answer(NORIGHTS_MSG)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) trying use: command !hhelp")
			return
		else:
			keyboard = Keyboard(one_time=True).add(Text("Вернуться в главное меню", {"cmd": "menu"}), color=KeyboardButtonColor.NEGATIVE)
			await message.answer("📜 Список команд помощника:\n\n1️⃣. !hhelp - прочитать этот список;\n2️⃣. !bladd [vk id (цифровой)] - добавить юзера в блек-лист;\n3️⃣. !bldel [vk id (цифровой)] - убрать юзера из блек-листа;\n4️⃣. в разработке;\n5️⃣. в разработке;\n6️⃣. в разработке;\n7️⃣. в разработке;\n8️⃣. в разработке;\n9️⃣. в разработке;\n🔟. в разработке.", keyboard=keyboard)
			await bot.api.messages.send(peer_id=message.from_id, sticker_id=8138, random_id=0)
			await sendLogMessage(f"[log]: user @id{message.from_id}({user[0].first_name} {user[0].last_name}) used: command !hhelp")
	except sqlite3.Error as e:
		print("Error ", e)
	finally:
		cursor.close()
		db.close()

@bot.on.private_message(text=["!bladd <vkid>", "!bladd"])
async def bladd_handler(message: Message, vkid=None):
	vk = int(message.from_id)
	if vkid is not None:
		tmpVK = int(vkid)
		user = await bot.api.users.get(tmpVK)
		try:
			db = sqlite3.connect("database.db")
			cursor = db.cursor()
			isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
			isHelper = cursor.execute("SELECT isHelper FROM users WHERE vk = ?", [vk]).fetchone()
			isAlreadyExists = cursor.execute("SELECT vk FROM blacklist WHERE vk = ?", [tmpVK]).fetchone()
			if (isAdmin[0] != 1 or isHelper[0] != 1 or None):
				await message.answer(NORIGHTS_MSG)
				return
			else:
				try:
					if isAlreadyExists[0] is not None:
						await message.answer(f"⛔️ Пользователь @id{tmpVK}({user[0].first_name} {user[0].last_name}) уже добавлен в блек-лист.")
					else:
						db = sqlite3.connect("database.db")
						cursor = db.cursor()
						cursor.execute("INSERT INTO blacklist(vk) VALUES(?)", [tmpVK])
						db.commit()
						await message.answer("✅ ok.")
				except sqlite3.Error as e:
					print("Error ", e)
		except sqlite3.Error as e:
			print("Error ", e)
		finally:
			cursor.close()
			db.close()
	else:
		await message.answer("⚠️ Используй !bladd [vk id (цифровой)].")

@bot.on.private_message(text=["!setbal <vkid> <bal>", "!setbal"])
async def bladd_handler(message: Message, vkid=None, bal=None):
	vk = int(message.from_id)
	if vkid is not None and bal is not None:
		tmpVK = int(vkid)
		tmpBal = int(bal)
		try:
			db = sqlite3.connect("database.db")
			cursor = db.cursor()
			isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
			isExists = cursor.execute("SELECT vk FROM users WHERE vk = ?", [tmpVK]).fetchone()
			if (isAdmin[0] != 1 or None):
				await message.answer(NORIGHTS_MSG)
				return
			else:
				try:
					if isExists is None:
						await message.answer("⛔️ Ты кажись ошибся дружочек, не существует пользователя в бд под таким цифровым айди вк.")
					else:
						db = sqlite3.connect("database.db")
						cursor = db.cursor()
						cursor.execute("UPDATE users SET balance = ? WHERE vk = ?", [tmpBal, tmpVK])
						db.commit()
						await message.answer("✅ ok.")
				except sqlite3.Error as e:
					print("Error ", e)
		except sqlite3.Error as e:
			print("Error ", e)
		finally:
			cursor.close()
			db.close()
	else:
		await message.answer("⚠️ Используй !setbal [vk id (цифровой)] [balance].")

@bot.on.private_message(text=["!bldel <vkid>", "!bldel"])
async def bldel_handler(message: Message, vkid=None):
	vk = int(message.from_id)
	if vkid is not None:
		tmpVK = int(vkid)
		user = await bot.api.users.get(tmpVK)
		try:
			db = sqlite3.connect("database.db")
			cursor = db.cursor()
			isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
			isHelper = cursor.execute("SELECT isHelper FROM users WHERE vk = ?", [vk]).fetchone()
			isExists = cursor.execute("SELECT vk FROM blacklist WHERE vk = ?", [tmpVK]).fetchone()
			if (isAdmin[0] != 1 or isHelper[0] != 1 or None):
				await message.answer(NORIGHTS_MSG)
				return
			else:
				try:
					if isExists is None:
						await message.answer(f"⛔️ Пользователь @id{tmpVK}({user[0].first_name} {user[0].last_name}) не добавлен в блек-лист.")
					else:
						db = sqlite3.connect("database.db")
						cursor = db.cursor()
						cursor.execute("DELETE FROM blacklist WHERE vk = ?", [tmpVK])
						db.commit()
						await message.answer("✅ ok.")
				except sqlite3.Error as e:
					print("Error ", e)
		except sqlite3.Error as e:
			print("Error ", e)
		finally:
			cursor.close()
			db.close()
	else:
		await message.answer("⚠️ Используй !bldel [vk id (цифровой)].")

@bot.on.private_message(text=["!giveperms <id> <perm> <nData>", "!giveperms"])
async def giveperms_handler(message: Message, id=None, perm=None, nData=None):
	vk = int(message.from_id)
	if id or perm or nData is not None:
		tmpVk = int(id)
		tmpData = int(nData)
		try:
			db = sqlite3.connect("database.db")
			cursor = db.cursor()
			isAdmin = cursor.execute("SELECT isAdmin FROM users WHERE vk = ?", [vk]).fetchone()
			print(isAdmin)
			if (isAdmin[0] != 1 or isAdmin[0] == None):
				print(isAdmin)
				await message.answer(NORIGHTS_MSG)
				return
			else:
				if (int(perm) != 1 and int(perm) != 2):
					await message.answer("⛔️ Ты кажись ошибся дружочек, не существует права под таким идентификатором.")
					return
				if (int(perm) == 1):
					try:
						db = sqlite3.connect("database.db")
						cursor = db.cursor()
						isUserRegistered = cursor.execute("SELECT vk FROM users WHERE vk = ?", [tmpVk]).fetchone()
						if isUserRegistered is None:
							await message.answer("⛔️ Ты кажись ошибся дружочек, не существует пользователя в бд под таким цифровым айди вк.")
							return
						else:
							if (tmpData != 0 and tmpData != 1):
								await message.answer("⛔️ Ты кажись ошибся дружочек, новое значение поля неверное.")
								return
							else:
								cursor.execute("UPDATE users SET isHelper = ? WHERE vk = ?", [tmpData, tmpVk])
								db.commit()
								if tmpData == 1:
									await bot.api.messages.send(peer_id=tmpVk, message=f"⚠️ У твоего профиля замечено изменение значения isHelper на {tmpData}.\n\n⚠️ Для запроса списка доступных команд используй !hhelp.", random_id=0)
								else:
									await bot.api.messages.send(peer_id=tmpVk, message=f"⚠️ У твоего профиля замечено изменение значения isHelper на {tmpData}.", random_id=0)
								await message.answer("✅ ok.")
					except sqlite3.Error as e:
						print("Error ", e)
				if(int(perm) == 2):
					try:
						db = sqlite3.connect("database.db")
						cursor = db.cursor()
						isUserRegistered = cursor.execute("SELECT vk FROM users WHERE vk = ?", [tmpVk]).fetchone()
						if isUserRegistered is None:
							await message.answer("⛔️ Ты кажись ошибся дружочек, не существует пользователя в бд под таким цифровым айди вк.")
							return
						else:
							if (tmpData != 0 and tmpData != 1):
								await message.answer("⛔️ Ты кажись ошибся дружочек, новое значение поля неверное.")
								return
							else:
								cursor.execute("UPDATE users SET isAdmin = ? WHERE vk = ?", [tmpData, tmpVk])
								db.commit()
								if tmpData == 1:
									await bot.api.messages.send(peer_id=tmpVk, message=f"⚠️ У твоего профиля замечено изменение значения isAdmin на {tmpData}.\n\n⚠️ Для запроса списка доступных команд используй !ahelp.", random_id=0)
								else:
									await bot.api.messages.send(peer_id=tmpVk, message=f"⚠️ У твоего профиля замечено изменение значения isAdmin на {tmpData}", random_id=0)
								await message.answer("✅ ok.")
					except sqlite3.Error as e:
						print("Error ", e)
		except sqlite3.Error as e:
			print("Error ", e)
		finally:
			cursor.close()
			db.close()
	else:
		await message.answer("⚠️ Используй !giveperms [vk id (цифровой)] [permid] [new data (0/1)].\n\n⚠️ 0 - отобрать, 1 - выдать.")

bot.run_forever()
