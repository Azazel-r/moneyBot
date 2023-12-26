# Autor: René Richter
# Datum: 25.10.2023
# Zweck: Twitch bot $WAGGG MON€YYY system lol

from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator, UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
import json
import time
from random import randint, random

class NotRegistered(Exception):
    pass
class AlreadyRegistered(Exception):
    pass
class NegativeBalance(Exception):
    pass
class NegativeItemStock(Exception):
    pass
class NegativeItemInv(Exception):
    pass
class EmptyInv(Exception):
    pass
class ItemNotFound(Exception):
    pass
class FullInv(Exception):
    pass

class MoneyDaten:

    def __init__(self):
        self.SPEICHER = 'speicherNeu.json'
        self.SHOPSPEICHER = 'shop.json'
        self.VARSPEICHER = 'varSpeicher.json'
        self.daten = None
        self.vars = None
        self.shop = None

    def laden(self):
        with open(self.SPEICHER, "r") as datei:
            self.daten = json.load(datei)
            datei.close()
        with open(self.SHOPSPEICHER, "r") as datei:
            self.shop = json.load(datei)
            datei.close()
        with open(self.VARSPEICHER, "r") as datei:
            self.vars = json.load(datei)
            datei.close()

    def speichern(self):
        with open(self.SPEICHER, "w") as datei:
            json.dump(self.daten, datei, indent=4)
            datei.close()
        with open(self.SHOPSPEICHER, "w") as datei:
            json.dump(self.shop, datei, indent=4)
            datei.close()
        with open(self.VARSPEICHER, "w") as datei:
            json.dump(self.vars, datei, indent=4)
            datei.close()

    def log(self, user, action):
        # -- dieser abschnitt is nur um die uhrzeit fancier zu machen, zB 15:6:2 -> 15:06:02 --
        t = time.localtime()
        text = ''
        for i in range(2,-1,-1):
            zahl = str(t[i])
            text += zahl if len(zahl) >= 2 else '0' + zahl
            text += '.'
        text = text[:-1] + ' '
        for i in range(3,6):
            zahl = str(t[i])
            text += zahl if len(zahl) >= 2 else '0' + zahl
            text += ':'
        # -- ende --
        text = text[:-1] + f' | {user} {action}'
        with open('logs.txt', 'a') as datei:
            datei.write(f'\n{text}')
            datei.close()
        with open('index.html', 'a') as datei:
            datei.write(f"\n<pre>{text}</pre>")
            datei.close()

    def shopSortierenNachPreis(self):
        # sehr weirde funktion ich gebs zu aber die funktioniert und das is die hauptsache
        sortShop = {}
        listShop = list(self.shop)
        indexList = [1 for i in range(len(self.shop))]
        while len(sortShop) != len(self.shop):
            klIndex = indexList.index(1)
            for i in range(len(self.shop)):
                if indexList[i]:
                    preis = self.shop[listShop[i]][0]
                    if preis < self.shop[listShop[klIndex]][0]:
                        klIndex = i
            name = listShop[klIndex]
            sortShop[name] = [self.shop[name][0], self.shop[name][1]]
            indexList[klIndex] = 0
        self.shop = sortShop

    # -------------- SETTER -------------------

    def register(self, user):
        if user not in self.daten:
            self.daten[f'{user}'] = [0, [["Founder-Badge", 1]], [0,0,0], 0]
            print(f'User {user} registriert')
            return
        raise AlreadyRegistered

    def adjustBalance(self, user, amount):
        try:
            self.daten[user][0] += amount
            if self.daten[user][0] < 0:
                self.daten[user][0] -= amount
                raise NegativeBalance
        except KeyError:
            raise NotRegistered
        
    def adjustKasse(self, user, amount):
        try:
            self.daten[user][3] += amount
            if self.daten[user][3] < 0:
                self.daten[user][3] -= amount
                raise NegativeBalance
        except KeyError:
            raise NotRegistered
    
    def give(self, user, item, amount):
        try:
            for e in self.daten[user][1]:
                if e[0] == item:
                    if (e[1] + amount) >= 0:
                        if e[1] + amount <= self.vars['max'][item]:
                            e[1] += amount
                            return
                        else:
                            raise FullInv
                    else:
                        raise NegativeItemInv # wenn man zuwenig items von einer sorte hat und noch mehr abzieht
            if amount > 0:
                if amount <= self.vars['max'][item]:   
                    self.daten[user][1].append([item, amount])
                else:
                    raise FullInv
            else:
                raise ItemNotFound # wenn item weggenommen wird, aber es nicht im inv ist
        except KeyError:
            raise NotRegistered
        
    def adjustItemStock(self, item, amount):
        try:
            self.shop[item][1] += amount
            if self.shop[item][1] < 0:
                self.shop[item][1] -= amount
                raise NegativeItemStock
        except KeyError:
            raise ItemNotFound
        
    def setCoolDown(self, user, cd, amount): # cd = 0 -> work cooldown
        try:
            self.daten[user][2][cd] = amount
        except:
            raise NotRegistered
        
    def adjustJackpot(self, amount):
        self.vars['Jackpot'] += amount

    def addNewItem(self, name, price, amount, maximum=1):
        if name not in self.shop:
            if amount >= 0:
                self.shop[name] = [price, amount]
                self.vars['max'][name] = maximum
            else:
                raise NegativeItemStock
        else:
            raise ItemNotFound
        
    def removeItem(self, name):
        if name in self.shop:
            self.shop.pop(name)
            self.vars['max'].pop(name)
        else:
            raise ItemNotFound

    # -------------- GETTER -------------------
    
    def balance(self, user):
        try:
            bal = self.daten[user][0]
            return bal
        except:
            raise NotRegistered
        
    def kasse(self, user):
        try:
            return self.daten[user][3]
        except:
            raise NotRegistered
    
    def inv(self, user):
        try:
            inventory = self.daten[user][1]
            if len(inventory) > 0:
                return inventory
            raise EmptyInv
        except KeyError:
            raise NotRegistered
        
    def getCooldown(self, user, cd):
        try:
            return self.daten[user][2][cd]
        except:
            raise NotRegistered

    def anzShopItems(self):
        return len(self.shop)
    
    def getShopItem(self, id):
        return list(self.shop)[id-1]
    
    def getShopPrice(self, item):
        return self.shop[item][0]
    
    def getShopAmount(self, item):
        return self.shop[item][1]
    
    def getJackpot(self):
        return self.vars['Jackpot']
    
    def getMaxAmount(self, item):
        return self.vars['max'][item]   

    def workFunc(self, x):
        return -0.0002*x**2 + 0.69*x + 20/3

    def convertTime(self, x):
        erg = [0,0,0]
        erg[2] = x % 60
        x //= 60
        erg[1] = x % 60
        x //= 60
        erg[0] = x
        return erg



class Bot:

    async def init(self):
        
        APP_ID = 'id'
        APP_SECRET = 'secret'
        USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]
        self.TARGET_CHANNEL = ['oberfeldbesen', 'azazel_r']
        self.daten = MoneyDaten()

        self.twitch = await Twitch(APP_ID, APP_SECRET)
        self.helper = UserAuthenticationStorageHelper(self.twitch, USER_SCOPE)
        await self.helper.bind()
        
        # OLD CODE:
        #self.auth = UserAuthenticator(self.twitch, USER_SCOPE)
        #self.token, self.refresh_token = await self.auth.authenticate()
        #await self.twitch.set_user_authentication(self.token, USER_SCOPE, self.refresh_token)

        self.chat = await Chat(self.twitch)
        self.chat.register_event(ChatEvent.READY, self.on_ready)
        
        # commands
        self.chat.register_command('register', self.register)
        self.chat.register_command('sus', self.sus)
        self.chat.register_command('inv', self.inv)
        self.chat.register_command('shop', self.shop)
        self.chat.register_command('buy', self.buy)
        self.chat.register_command('add', self.add)
        self.chat.register_command('work', self.work)
        self.chat.register_command('use', self.use)
        self.chat.register_command('restock', self.restock)
        self.chat.register_command('slots', self.slots)
        self.chat.register_command('jackpot', self.jackpot)
        self.chat.register_command('additem', self.addItem)
        self.chat.register_command('removeitem', self.removeItem)
        self.chat.register_command('roulette', self.roulette)
        self.chat.register_command('log', self.log)
        self.chat.register_command('kasse', self.kasse)

        # starte den bot
        self.chat.start()
    
    # Baby, now I'm ready, moving on

    async def on_ready(self, rdy: EventData):
        self.daten.laden()
        print("Oh, but maybe, I was ready, all along...")
        await rdy.chat.join_room(self.TARGET_CHANNEL)

    # Commands n stuff

    async def register(self, cmd: ChatCommand):
        username = cmd.user.name
        try:
            self.daten.register(username)
            self.daten.speichern()
            await cmd.reply("Erfolgreich registriert!")
            self.daten.log(username, 'registered.')
        except AlreadyRegistered:
            await cmd.reply("Entweder bist du schon registriert oder etwas ist schiefgelaufen :|")

    async def sus(self, cmd: ChatCommand):
        username = cmd.user.name
        try:
            await cmd.reply(f'Du spürst {self.daten.balance(username)} Münzen auf deinem Konto.')
            self.daten.log(username, f'casts SUS, senses {self.daten.balance(username)} coins.')
        except NotRegistered:
            await cmd.reply('Entweder bist du nicht registriert oder etwas ist schiefgelaufen :|')

    async def inv(self, cmd: ChatCommand):
        username = cmd.user.name
        try:
            schrank = self.daten.inv(username)
            reply = 'Du öffnest deinen Schrank und schaust dir deine Besitztümer an: '
            for e in schrank:
                reply += f'{e[1]}x {e[0]}, '
            await cmd.reply(reply[:-2])
        except EmptyInv:
            await cmd.reply("Du hast keine Besitztümer PoroSad")
        except NotRegistered:
            await cmd.reply('Entweder bist du nicht registriert oder etwas ist schiefgelaufen :|')

    async def shop(self, cmd: ChatCommand):
        if cmd.parameter == '':
            reply = ''
            for i in range(1, self.daten.anzShopItems()+1):
                reply += f'({i}) {self.daten.getShopItem(i)} | '
            await cmd.reply(reply[:-2])
            #await cmd.reply(f"Gib !shop 1 bis !shop {self.daten.anzShopItems()} ein, um das ganze Angebot zu sehen!")
        elif int(cmd.parameter) in range(1, self.daten.anzShopItems()+1):
            item = self.daten.getShopItem(int(cmd.parameter)) 
            await cmd.reply(f"Gegenstand: {item} | Preis: {self.daten.getShopPrice(item)} Münze(n) | Auf Lager: {self.daten.getShopAmount(item)} Stück.")
        else:
            await cmd.reply("Ungültier Command-Parameter PoroSad")

    async def buy(self, cmd: ChatCommand):
        username = cmd.user.name
        param = cmd.parameter.split()
        if len(param) == 0:
            await cmd.reply(f"Gib !buy <Itemnummer> <Anzahl> ein, um etwas zu kaufen!")
        elif len(param) == 2:
            try:
                id = int(param[0])
                amount = int(param[1])
                item = self.daten.getShopItem(id)
                price = self.daten.getShopPrice(item)

                if amount <= 0:
                    await cmd.reply("Du kannst nicht 0 oder weniger Items kaufen du kek")
                    return
                
                
                self.daten.adjustItemStock(item, -amount)
                self.daten.adjustBalance(username, -price * amount)
                self.daten.give(username, item, amount)
                self.daten.speichern()
                await cmd.reply(f"Kauf erfolgreich: {amount}x {item} für {price * amount} Münze(n).")
                self.daten.log(username, f'bought {amount}x {item} for {price * amount} coins.')

            except NegativeItemStock:
                await cmd.reply("Sieht so aus als wären nicht genug Exemplare im Shop PoroSad")
            except NegativeBalance:
                self.daten.adjustItemStock(item, amount)
                await cmd.reply("Du hast nicht genug Münzen, um dir das zu kaufen PoroSad.")
            except FullInv:
                self.daten.adjustItemStock(item, amount)
                self.daten.adjustBalance(username, price * amount)
                await cmd.reply(f'Du kannst nicht so viel kaufen, da es du maximale Anzahl von {self.daten.getMaxAmount(item)} im Inventar überschreiten würdest PoroSad')
            except NotRegistered:
                await cmd.reply('Entweder bist du nicht registriert oder etwas ist schiefgelaufen :|')
            except:
                await cmd.reply("Ungültier Command-Parameter, oder etwas ist schief gelaufen PoroSad")
        else:
            await cmd.reply("Ungültier Command-Parameter PoroSad")

    async def add(self, cmd: ChatCommand):
        username = cmd.user.name
        param = cmd.parameter.split()
        try:
            if username == 'azazel_r':
                self.daten.adjustBalance(param[0], int(param[1]))
                self.daten.speichern()
                self.daten.log(username, f'cheated and gave {param[0]} {int(param[1])} coins.')
            else:
                await cmd.reply("Keine Rechte, ätsch.")
        except NegativeBalance:
            await cmd.reply("Vermögen würde ins negative gehen, nicht possible.")
        except:
            await cmd.reply("Irgendwas ist schiefgelaufen PoroSad")

    async def work(self, cmd: ChatCommand):
        username = cmd.user.name
        zeit = int(time.time())
        try:
            cd = self.daten.getCooldown(username, 0)
            if cmd.parameter == '':
                if zeit >= cd:
                    await cmd.reply("Du bist bereit zu arbeiten. Gib !work <zeit> (in Minuten) an, um zu arbeiten.")
                else:
                    t = self.daten.convertTime(cd - zeit)
                    await cmd.reply(f'Du kannst das nächste mal in {t[0]}h {t[1]}min {t[2]}s arbeiten!')
            elif 20 <= int(cmd.parameter) <= 1000:
                COOLDOWN = int(cmd.parameter)
                if zeit >= cd: # 0 für work cooldown
                    n = int(self.daten.workFunc(int(cmd.parameter)))
                    self.daten.adjustBalance(username, n)
                    self.daten.setCoolDown(username, 0, zeit+COOLDOWN*60)
                    self.daten.speichern()
                    await cmd.reply(f"Du arbeitest für die nächsten {COOLDOWN} Minuten und hast dir {n} Münze(n) verdient!")
                    self.daten.log(username, f'worked for {COOLDOWN} minutes and got {n} coins.')
                else:
                    t = self.daten.convertTime(cd - zeit)
                    await cmd.reply(f'Du kannst das nächste mal in {t[0]}h {t[1]}min {t[2]}s arbeiten!')
            else:
                await cmd.reply("Die angegebene Zeit muss zwischen 20 und 1000 Minuten liegen!")
        except NotRegistered:
            await cmd.reply('Entweder bist du nicht registriert oder etwas ist schiefgelaufen :|')
        except:
            await cmd.reply("Ungültier Command-Parameter, oder etwas ist schief gelaufen PoroSad")

    async def use(self, cmd: ChatCommand):
        username = cmd.user.name
        try:
            item = cmd.parameter
            self.daten.give(username, item, -1)
            if item == 'Fake-Muenze':
                wurf = randint(0,1)
                if wurf:
                    await cmd.reply("Die Münze ist fake und useless, deshalb schmeißt du sie weg. Dabei landet sie auf Kopf.")
                else:
                    await cmd.reply("Die Münze ist fake und useless, deshalb schmeißt du sie weg. Dabei landet sie auf Zahl.")
            self.daten.speichern()
            self.daten.log(username, f'used item {item}.')
        except ItemNotFound:
            await cmd.reply("Du hast kein valides Item übergeben :|")
        except NegativeItemInv:
            await cmd.reply('Du hast nicht genug Items von dieser Sorte :|')
        except NotRegistered:
            await cmd.reply('Entweder bist du nicht registriert oder etwas ist schiefgelaufen :|')

    async def restock(self, cmd: ChatCommand):
        username = cmd.user.name
        try:
            item = cmd.parameter.split(':')[0]
            amount = int(cmd.parameter.split(':')[1])
            if username == 'azazel_r': 
                self.daten.adjustItemStock(item, amount)
                self.daten.speichern()
                self.daten.log(username, f'restocked item {item} by {amount}.')
            else:
                await cmd.reply("Keine Rechte, ätsch.")
        except ItemNotFound:
            await cmd.reply("Du hast kein valides Item übergeben :|")
        except NegativeItemStock:
            await cmd.reply("Geht nicht, es würde zu wenig Items davon im Shop geben :|")
        except:
            await cmd.reply("Etwas ist schiefgelaufen :|")

    async def slots(self, cmd: ChatCommand):
        username = cmd.user.name
        emojis = ['💀', '💤', '😶‍🌫️', '🥴', '😇', '🤯', '🥒']
        payout = [0, 0.2, 1, 2, 3, 4, 7]
        chances = [35, 22, 15, 10, 8, 6, 4]
        zeit = int(time.time())
        cd = 30

        if cmd.parameter == '':
            await cmd.reply("Nutze !slots <Einsatz>, um zu spielen! Einsatz muss mehr als 5 Münzen sein.")
            return

        try:
            if zeit - self.daten.getCooldown(username, 1) > cd:
                bet = int(cmd.parameter.split()[0])
                if bet < 5:
                    await cmd.reply("Du kannst nicht weniger als 5 Münzen setzen :|")
                    return
                reply = f'🎰 Du spinnst die Glücksmaschine für {bet} Münzen und bekommst... '
                self.daten.adjustBalance(username, -bet)
                self.daten.adjustKasse(username, int(bet/6))
                self.daten.setCoolDown(username, 1, zeit)
                spin = randint(1,100)
                jackspin = random()
                acc = 0
                self.daten.adjustJackpot(int(bet/5))
                for i in range(len(chances)):
                    if spin <= acc + chances[i]:
                        p = int(payout[i]*bet)
                        self.daten.adjustBalance(username, p)
                        reply += f'{emojis[i]} {p} Münze(n)!'
                        self.daten.log(username, f'played slots for {bet} coins and got {p} coins out of it.')
                        if jackspin <= (0.5+min(bet,1000)/2000)/100:
                            pot = self.daten.getJackpot()
                            reply += f' Außerdem, WOW! DU BIST LUCKY UND HITTEST DEN JACKPOT MIT {pot} MÜNZE(N)!! 🎉🎉'
                            self.daten.adjustBalance(username, pot)
                            self.daten.adjustJackpot(-pot)
                            self.daten.log(username, f'has won the slots-jackpot with {pot} coins!')

                        self.daten.speichern()
                        await cmd.reply(reply)
                        return
                    else:
                        acc += chances[i]
            else:
                await cmd.reply(f"Du musst noch warten, Freundchen!! ({cd - (zeit - self.daten.getCooldown(username, 1))}s)")

        except NotRegistered:
            await cmd.reply('Entweder bist du nicht registriert oder etwas ist schiefgelaufen :|')
        except NegativeBalance:
            await cmd.reply("Du bist broke. Du kannst kein Glücksspiel mehr spielen, solang du nicht 5 Münzen hast :|")
        except Exception as e:
            print(e)
            print(type(e))
            await cmd.reply("Ungültier Command-Parameter, oder etwas ist schief gelaufen PoroSad")

    async def jackpot(self, cmd: ChatCommand):
        await cmd.reply(f'Im Slots-Jackpot sind gerade {self.daten.getJackpot()} Münze(n). Viel Glück!')

    async def addItem(self, cmd: ChatCommand):
        username = cmd.user.name
        try:
            item = cmd.parameter.split(":")[0]
            price = int(cmd.parameter.split(":")[1])
            amount = int(cmd.parameter.split(":")[2])
            if username == 'azazel_r':
                self.daten.addNewItem(item, price, amount)
                self.daten.shopSortierenNachPreis()
                self.daten.speichern()
                await cmd.reply('👍')
                self.daten.log(username, f'added new item {item} {amount} times for {price} coins to the item shop.')
            else:
                await cmd.reply("Keine Rechte, ätsch.")

        except ItemNotFound:
            await cmd.reply('Dieses Item existiert schon im Shop!')
        except NegativeItemStock:
            await cmd.reply('Du kannst keine kleinere Anzahl als 0 festlegen!')
        except:
            await cmd.reply("Ungültier Command-Parameter, oder etwas ist schief gelaufen PoroSad")

    async def removeItem(self, cmd: ChatCommand):
        username = cmd.user.name
        try:
            if username == 'azazel_r':
                self.daten.removeItem(cmd.parameter)
                self.daten.speichern()
                await cmd.reply('👍')
                self.daten.log(username, f'removed item {cmd.parameter} from the shop.')
            else:
                await cmd.reply("Keine Rechte, ätsch.")
        except ItemNotFound:
            await cmd.reply('Dieses Item existiert nicht PoroSad')

    async def roulette(self, cmd: ChatCommand):
        if cmd.parameter == '':
            await cmd.reply('Nutze !roulette <Einsatz> <Wette>, um Roulette zu spielen. Dabei ist Wette entweder "Black", "Red" oder eine Zahl von 0 bis 36 :)')
            return
        username = cmd.user.name
        br = [1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1]
        br += br
        brStr = ['BLACK', 'RED']
        brEmojis = ['⬛',  '🟥', '🟩']
        roll = randint(0,36)
        farbe = brStr[br[roll-1]] if roll > 0 else 'GREEN'
        zeit = int(time.time())
        cd = 30

        try:
            if zeit - self.daten.getCooldown(username, 2) > cd:
                param = cmd.parameter.split()
                einsatz = int(param[0])
                wette = param[1]
                logstr = f'played roulette and bet {einsatz} coins on {wette.upper()}. roulette gave {roll} {farbe}. '
                reply = f'Das Roulette gibt aus... {roll} {farbe} {brEmojis[2] if farbe == "GREEN" else brEmojis[brStr.index(farbe)]}! '

                if einsatz <= 0:
                    await cmd.reply("Du kannst nicht 0 oder weniger Münzen setzen!")
                    return
                
                self.daten.adjustBalance(username, -einsatz)
                self.daten.adjustKasse(username, int(einsatz/6))
                if wette.upper() in brStr:
                    if wette.upper() == farbe:
                        reply += f'Du gewinnst mit deiner Wette auf die Farbe {farbe} und sackst {einsatz*2} Münzen ein :)'
                        self.daten.adjustBalance(username, einsatz*2)
                        logstr += f'they won {einsatz*2} coins.'
                    else:
                        reply += f'Du verlierst mit deiner Wette auf die Farbe {wette.upper()} und verlierst deinen Einsatz von {einsatz} Münze(n) :('
                        logstr += f'they lost and got nothing.'

                elif wette in [f'{i}' for i in range(37)]:
                    if roll == int(wette):
                        reply += f'Du gewinnst mit deiner Wette auf die Zahl {roll} und sackst {einsatz*36} Münzen ein EZ Clap'
                        self.daten.adjustBalance(username, einsatz*36)
                        logstr += f'they won {einsatz*36} coins.'
                    else:
                        reply += f'Du verlierst mit deiner Wette auf die Zahl {wette} und verlierst deinen Einsatz von {einsatz} Münze(n) :('
                        logstr += f'they lost and got nothing.'

                else:
                    self.daten.adjustBalance(username, einsatz)
                    await cmd.reply('Ungültige Wette. Usage: black, red oder eine Zahl von 0 bis 36!')
                    return
                
                self.daten.speichern()
                self.daten.setCoolDown(username, 2, zeit)
                await cmd.reply(reply)
                self.daten.log(username, logstr)
            
            else:
                await cmd.reply(f"Du musst noch warten, Freundchen!! ({cd - (zeit - self.daten.getCooldown(username, 2))}s)")


        except NotRegistered:
            await cmd.reply('Entweder bist du nicht registriert oder etwas ist schiefgelaufen :|')
        except NegativeBalance:
            await cmd.reply('Du kannst nicht mehr Münzen setzen als du besitzt!')
        except:
            await cmd.reply("Ungültier Command-Parameter, oder etwas ist schief gelaufen PoroSad")

    async def log(self, cmd: ChatCommand):
        await cmd.reply("Der log ist hier zu finden: https://azazel.dev/logs")

    async def kasse(self, cmd: ChatCommand):
        username = cmd.user.name
        try:
            if cmd.parameter.lower() == 'payout':
                if self.daten.balance(username) < 5:
                    bal = self.daten.kasse(username)
                    self.daten.adjustBalance(username, bal)
                    self.daten.adjustKasse(username, -bal)
                    await cmd.reply(f'{bal} Münze(n) ausgezahlt!')
                    self.daten.log(username, f'gets {bal} coins from insurance.')
                    return
                else:
                    await cmd.reply('Du kannst erst die Kasse auszahlen lassen, wenn du weniger als 5 Münzen hast!')
                    return
            await cmd.reply(f'Du hast {self.daten.kasse(username)} Münze(n) in deiner Versicherungskasse. Du kannst sie dir mit "!kasse payout" auszahlen lassen, wenn du pleite bist.')
        except NotRegistered:
            await cmd.reply('Entweder bist du nicht registriert oder etwas ist schiefgelaufen :|')

# ------------------------
asyncio.run(Bot().init())
