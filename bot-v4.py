import time
from datetime import date, datetime
import re
from telethon.tl.types import MessageEntityTextUrl
from telethon import TelegramClient, sync, events
import configparser
import asyncio
import os
os.environ['PYTHONASYNCIODEBUG'] = '1'


config = configparser.ConfigParser()
config.read("./conf.ini")

# Вставляем api_id, api_hash и ссылку на канал
API_ID = config['Telegram']['API_ID']
API_HASH = config['Telegram']['API_HASH']
CHANNEL = config['Telegram']['CHANNEL']

# Создаем клиент
client = TelegramClient('session_name', API_ID, API_HASH)
# Создаем родительский класс со списком групп по тегу


class TableOfContents():
    def __init__(self):
        self.links = {}
        self.tables = {}


# Задаем ссылки
tableOfContents = TableOfContents()
tableOfContents.links["#содержание"] = int(1916)
tableOfContents.links["#файлы"] = int(1917)
tableOfContents.links["#текст"] = int(1919)
tableOfContents.links["#взаимодействие"] = int(1920)
tableOfContents.links["#оптимизация"] = int(1921)
tableOfContents.links["#скрипты"] = int(1922)
tableOfContents.links["#хихоз"] = int(1923)
tableOfContents.links["#macos"] = int(1924)
tableOfContents.links["#android"] = int(1925)
tableOfContents.links["#desktop"] = int(1926)
tableOfContents.links["#mobile"] = int(1927)


# Создаем класс группы


class GroupOfTag():
    def __init__(self, eventBody, tableOfContents=tableOfContents):
        self.id = eventBody.id
        self.links = {}
        self.messageInner = ""

        self.innerHeaders = eventBody.message.splitlines()
        self.titleTag = self.innerHeaders[0].lower()
        del self.innerHeaders[0]

        self.templist = []
        self.innerIDs = []
        for i, inner_text in eventBody.get_entities_text(MessageEntityTextUrl):
            url = i.url
            self.innerIDs.append(url.split("/")[-1])
        for i in range(len(self.innerHeaders)):
            self.links[int(self.innerIDs[i])] = [
                self.innerHeaders[i], self.titleTag, self.id]
        self.innerIDs = []

    def delete_broken_links(self):
        for link in set(helper.linksToDelete):
            if link in self.links:
                del self.links[link]

    def bake_message_inner(self):
        self.templist = []
        for id in self.links:
            line = "[" + str(self.links[id][0]) + "](" + \
                CHANNEL + str(id) + ")"
            self.templist.append(line)

        self.messageInner = "\n".join(self.templist)


# Создаем класс сообщения-события


class EventMessage():
    def __init__(self, eventBody):
        self.id = eventBody.id
        self.header = eventBody.message.splitlines()[0]
        if len(eventBody.message.splitlines()) > 1:
            self.tags = eventBody.message.splitlines()[1].split("(")[0]
            self.tags = list(re.findall("#\S+", self.tags))
        else:
            self.tags = []


# Создаем хелпера, чтоб записывать индексы


class Helper():
    def __init__(self):
        self.linksToDelete = []
        self.groupsToUpdate = []

        self.FullMessagesIndex = dict()
        self.currentID = ""
        self.currentHeader = ""
        self.currentBacklinks = []

        self.fullHeadersIndex = []
        self.fullIDsIndex = []
        self.fullBacklinksIndex = []

        self.itsNewMessage = False

        self.updatedTags = []
        for id in self.FullMessagesIndex:
            self.fullIDsIndex.append(int(id))
            self.fullHeadersIndex.append(self.FullMessagesIndex[id][0])
            self.fullBacklinksIndex.append(self.FullMessagesIndex[id][1])

    def append_index_row(self, id: int, header: str, tags: list, backlinks: int):
        if int(id) in self.FullMessagesIndex.keys():
            self.FullMessagesIndex.update({
                id: [
                    header, self.FullMessagesIndex[int(id)][1] + tags,
                    self.FullMessagesIndex[int(id)][2] + backlinks
                ]})
        else:
            self.FullMessagesIndex[int(id)] = [
                header, list(tags), list(backlinks)]
            self.fullIDsIndex.append(int(id))
            self.fullHeadersIndex.append(header)
            self.fullBacklinksIndex.append(tags)

    async def check_dead_links(self, tableOfContents=tableOfContents):
        for id in helper.FullMessagesIndex:
            helper.currentID = id
            helper.currentBacklinks = helper.FullMessagesIndex[id][2]
            try:
                targetMessage = EventMessage(await client.get_messages(CHANNEL, ids=int(helper.currentID)))
            except:
                helper.linksToDelete.append(helper.currentID)
                helper.groupsToUpdate.append(helper.currentBacklinks)


helper = Helper()
client.start()

# Cоздаем словарь с группами по тегу. Индексируем сообщения

for tag in tableOfContents.links:
    id = tableOfContents.links[tag]
    tableOfContents.tables[id] = GroupOfTag(
        client.get_messages(CHANNEL, ids=int(id)))
    targetGroup = tableOfContents.tables[id]

    for innerLink in targetGroup.links:
        helper.append_index_row(int(
            innerLink), targetGroup.links[innerLink][0], [targetGroup.titleTag], [targetGroup.id])


# Удаляем сообщение из всех групп после его удаления из канала


@ client.on(events.MessageDeleted(chats=(CHANNEL)))
async def handler(event):
    if event.deleted_ids in helper.FullMessagesIndex.keys():
        await helper.check_dead_links()
        if helper.groupsToUpdate:
            helper.groupsToUpdate.append(1916)
            for groupID in set(helper.groupsToUpdate):
                targetGroup = tableOfContents.tables[int(groupID)]
                targetGroup.delete_broken_links()
                targetGroup.bake_message_inner()
                await client.edit_message(CHANNEL, targetGroup.id, "**" + targetGroup.titleTag.upper() + "**\n" + targetGroup.messageInner)


# Реагируем на новое или измененное сообщение

@ client.on(events.MessageEdited(chats=(CHANNEL), pattern="🐸"))
async def handler(event):

    # Проверяем мертвые ссылки
    # await helper.check_dead_links()
    # Создаем инстанс сообщения-события
    eventMessage = EventMessage(await client.get_messages(CHANNEL, ids=event.message.id))
    # Проверяем, что изменения были не в оглавлении
    if int(eventMessage.id) not in tableOfContents.links.values():
        # Добавляем к каждому сообщению тег «содержание»
        eventMessage.tags.append("#содержание")
        # Проверяем, новое ли это письмо. Если да — добавляем в оглавление
        if int(eventMessage.id) not in list(
                helper.FullMessagesIndex.keys()):
            helper.itsNewMessage = True
            # Получаем групп каждого тега в сообщении, добавляем в нее запись, индексируем
            for tag in eventMessage.tags:
                if tag in tableOfContents.links:
                    id = tableOfContents.links[tag]
                    targetGroup = tableOfContents.tables[int(id)]

                    helper.append_index_row(
                        int(eventMessage.id),
                        eventMessage.header,
                        eventMessage.tags,
                        [targetGroup.id])

                    targetGroup.links[int(eventMessage.id)] = [
                        helper.FullMessagesIndex[int(eventMessage.id)][0],
                        helper.FullMessagesIndex[int(eventMessage.id)][1],
                        helper.FullMessagesIndex[int(eventMessage.id)][2]]

                    helper.groupsToUpdate.append(int(targetGroup.id))

        # Если это измененное письмо, то находим родителей и нужную запись в них, обновляем заголовок
        else:
            helper.itsNewMessage = False

            if int(eventMessage.id) in list(helper.FullMessagesIndex.keys()):

                if eventMessage.header != helper.FullMessagesIndex[int(eventMessage.id)][0]:
                    helper.groupsToUpdate + \
                        helper.FullMessagesIndex[int(eventMessage.id)][2]

                    for groupID in helper.FullMessagesIndex[int(eventMessage.id)][2]:
                        tableOfContents.tables[int(groupID)].links[int(
                            eventMessage.id)][0] = eventMessage.header

                if set(eventMessage.tags).symmetric_difference(set(helper.FullMessagesIndex[int(eventMessage.id)][1])) != set():

                    helper.updatedTags = set(eventMessage.tags).symmetric_difference(
                        set(set(helper.FullMessagesIndex[int(eventMessage.id)][1])))

                    for groupTitle in helper.updatedTags:
                        targetGroup = tableOfContents.tables[tableOfContents.links[
                            groupTitle]]
                        helper.groupsToUpdate.append(int(targetGroup.id))

                        if int(eventMessage.id) in targetGroup.links:
                            helper.linksToDelete.append(int(eventMessage.id))
                        else:
                            helper.FullMessagesIndex.update({int(eventMessage.id): [
                                                            eventMessage.header,
                                                            eventMessage.tags,
                                                            targetGroup.id]})
                            targetGroup.links.update({
                                int(eventMessage.id): [
                                    helper.FullMessagesIndex[int(
                                        eventMessage.id)][0],
                                    helper.FullMessagesIndex[int(
                                        eventMessage.id)][1],
                                    helper.FullMessagesIndex[int(eventMessage.id)][2]]})

        # Обновляем группы в Телеграме
        if helper.groupsToUpdate:
            helper.groupsToUpdate.append(1916)
            for groupID in set(helper.groupsToUpdate):
                targetGroup = tableOfContents.tables[int(groupID)]
                targetGroup.delete_broken_links()
                targetGroup.bake_message_inner()
                await client.edit_message(CHANNEL, targetGroup.id, "**" + targetGroup.titleTag.upper() + "**\n" + str(targetGroup.messageInner))

########################################################################

# Здесь нужно написать обновление групп при запуске при несоответствии
# for table in tableOfContents.tables:
#   for innerLink in table.links:
#       try
            # загрузка сообщения
            # фикс заголовка
            # фикс тегов
        # except
            # в список на удаление

    # перерисовка
########################################################################

client.run_until_disconnected()
