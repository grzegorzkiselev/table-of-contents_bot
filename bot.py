import configparser
from telethon import TelegramClient, sync, events
from telethon.tl.types import MessageEntityTextUrl
import re

config = configparser.ConfigParser()
config.read("./config.ini")

# Вставляем api_id и api_hash
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

client = TelegramClient('session_name', api_id, api_hash)
# client = TelegramClient(None, api_id, api_hash)

client.start()

client.parse_mode = 'markdown'
channel = "https://t.me/grzegorzkiselevwill"


class TableOfContents:
    def __init__(self):
        self.tags = {}
        self.ids = []

    def add_tag(self, tag, id):
        self.tags[tag] = id
        self.ids.append(id)


tableOfContents = TableOfContents()
tableOfContents.add_tag("#содержание", 1916)
tableOfContents.add_tag("#текст", 1917)
tableOfContents.add_tag("#файлы", 1917)
tableOfContents.add_tag("#взаимодействие", 1917)
tableOfContents.add_tag("#оптимизация", 1920)
tableOfContents.add_tag("#скрипты", 1921)
tableOfContents.add_tag("#хихоз", 1922)
tableOfContents.add_tag("#macos", 1923)
tableOfContents.add_tag("#android", 1924)
tableOfContents.add_tag("#android11", 1925)
tableOfContents.add_tag("#desktop", 1926)
tableOfContents.add_tag("#mobile", 1927)


class GroupOfTag:
    def __init__(self, body):
        self.id = body.id
        self.headers = body.message.splitlines()
        self.title = self.headers[0]
        del self.headers[0]
        self.urls = []
        self.ids = []
        self.links = {}
        self.list = ""
        self.linksToRemove = []
        self.needsUpdate = False
        self.templist = []
        for i, inner_text in body.get_entities_text(MessageEntityTextUrl):
            url = i.url
            self.urls.append(url)
            self.ids.append(re.search("\d+", url).group(0))
            # self.links[self.headers[i]] = re.search("\d+", url).group(0)
        for i in range(len(self.headers)):
            self.links[self.ids[i]] = self.headers[i]

    async def update_list(self):
        for id in self.links:
            line = "[" + str(self.links[id]) + \
                "](https://t.me/grzegorzkiselevwill/" + str(id) + ")"
            self.templist.append(line)

        self.list = "\n".join(self.templist)

        await client.edit_message(channel, self.id, str("**" + self.title + "**") + "\n" + self.list)

    def add_header_to_links(self, header, id):
        self.links[id] = header

    def delete_headers_from_remove_list(self):
        for link in self.linksToRemove:
            if link in self.linksToRemove:
                del self.links[str(link)]


class HeaderMessage:
    def __init__(self, body):
        self.url = "https://t.me/grzegorzkiselevwill/" + str(body.id)
        self.id = body.id
        self.header = body.message.splitlines()[0]
        try:
            self.tags = re.search(
                "#[\s\S]*", body.message).group(0).split(" ")
        except:
            self.tags = []


@ client.on(events.MessageEdited(chats=(channel)))
async def handler(event):
    print("acab")
    for id in tableOfContents.ids:
        groupOfTag = GroupOfTag(await client.get_messages(channel, ids=id))
        for id in groupOfTag.links:
            try:
                referencedMessage = HeaderMessage(await client.get_messages(channel, ids=int(id)))
                pattern = "🐸"
                if not(re.search(pattern, referencedMessage.header)):
                    groupOfTag.needsUpdate = True
                    groupOfTag.linksToRemove.append(referencedMessage.id)

                if(groupOfTag.links[id] != referencedMessage.header):
                    groupOfTag.needsUpdate = True
                    groupOfTag.links[id] = referencedMessage.header

                if(groupOfTag.title.lower() != "#содержание"):
                    if(groupOfTag.title.lower() not in referencedMessage.tags):
                        groupOfTag.needsUpdate = True
                        groupOfTag.linksToRemove.append(referencedMessage.id)

                for tag in referencedMessage.tags:
                    targetMessageId = tableOfContents.tags[tag]
                    targetGroup = GroupOfTag(await client.get_messages(channel, ids=int(targetMessageId)))

                    if(str(referencedMessage.id) not in targetGroup.links):
                        targetGroup.add_header_to_links(
                            referencedMessage.header, referencedMessage.id)

                        # await client.edit_message(channel, targetGroup.id, str(targetGroup.title) + "\n" + str(targetGroup.list))
                        await targetGroup.update_list()

            except:
                groupOfTag.needsUpdate = True
                groupOfTag.linksToRemove.append(str(id))

        if groupOfTag.needsUpdate:
            groupOfTag.delete_headers_from_remove_list()
            await groupOfTag.update_list()


@ client.on(events.NewMessage(chats=(channel)))
async def normal_handler(event):

    newMessage = await client.get_messages(channel, ids=event.message.id)
    headerMessage = HeaderMessage(newMessage)

    pattern = "🐸"
    if(re.search(pattern, headerMessage.header)):
        headerMessage.tags.append("#содержание")

        for tag in headerMessage.tags:
            id = tableOfContents.tags[tag]
            groupOfTag = GroupOfTag(await client.get_messages(channel, ids=id))
            groupOfTag.add_header_to_links(
                headerMessage.header, headerMessage.url)
            await groupOfTag.update_list()

client.run_until_disconnected()
