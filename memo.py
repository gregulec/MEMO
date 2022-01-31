import tornado.ioloop
import tornado.web
import tornado.websocket
import asyncio
import struct
from random import randint

games = {}
waitingGames = None
players = {}
num = 0

class Game:

    def __init__(self,gid,player1):
        self.id = gid
        i = 0
        count0 = 0
        count1 = 0
        count2 = 0 
        self.cards = []
        while True:
            ranodom = randint(0,2)
            if (ranodom == 0) & (count0 < 2):
                count0 = count0 + 1
                self.cards.append("circle")
                i = i + 1
            if (ranodom == 1) & (count1 < 2):
                count1 = count1 + 1
                self.cards.append("square") 
                i = i + 1
            if (ranodom == 2) & (count2 < 2):
                count2 = count2 + 1
                self.cards.append("rect")
                i = i + 1
            if i < 6:
                continue
            break
        print(self.cards)
        # self.cards = ["circle","square","rect","circle","square","rect"]
        self.oneVisible = False
        self.nrVisibleCard = None
        self.pairs = 3
        self.player1 = player1
        self.player2 = None
        self.pointsP1 = 0
        self.pointsP2 = 0
        self.end = False

    def setOponent(self,oponent):
        self.player2 = oponent

    def getID(self):
        return self.id

    def removeOponen(self):
        self.player2 = None

    def getPlayer1(self):
        return self.player1

    def getPlayer2(self):
        return self.player2

    def getOponent(self,pid):
        if pid != self.player1:
            return self.player1
        else:
            return self.player2
    
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
 
class Player(tornado.websocket.WebSocketHandler):

    def open(self):
        global num
        global waitingGames
        self.id = num
        players[self.id] = self
        self.sendId(self.id)
        num = num + 1
        if waitingGames == None:
            #create new game
            self.idGame = num
            num = num + 1
            newGame = Game(self.idGame,self.id)
            waitingGames = newGame
            print("nowa gra utworzona") 
        else:
            #join to game
            waitingGames.setOponent(self.id)
            self.idGame = waitingGames.getID()
            games[self.idGame] = waitingGames
            waitingGames = None
            print("dolaczonono do gry") 

    def on_close(self):
        if int(self.idGame) in games:
            if games[int(self.idGame)].end == False:
                #not end game
                del players[int(self.id)]
                print("close player")
            else:
                #end game
                del games[int(self.idGame)]
                del players[int(self.id)]
                print("close player and end game")

    def on_message(self, message):
        unpack = struct.unpack('bb',message)
        print(unpack[0],unpack[1])
        if unpack[0] == 0:
            print("odebrano id")
            self.receiveID(unpack[1])
        else:
            print("odebrano nr karty")
            self.onClickCard(unpack[1])
    
    def receiveID(self,pid):
        global waitingGames
        del players[int(self.id)]
        #remove open results
        if waitingGames == None:
            #after join to game
            game = games[self.idGame]
            game.removeOponen()
            del games[self.idGame]
            waitingGames = game
            print("cofam zmiany po dolaczeniu do gry")
        else:
            #after create new game
            waitingGames = None
            print("cofam zmiany po nowej grze")
        self.id = pid
        players[self.id] = self
        #restore game
        for i in games:
            if (int(games[i].getPlayer1()) == self.id) | (int(games[i].getPlayer2()) == self.id):
                self.idGame = games[i].getID()
                print("odtwarzam zapisana gre")                    

    def onClickCard(self,nrCard):   
        oponentID = games[int(self.idGame)].getOponent(self.id)
        oponent = players[oponentID]
        self.showCard(nrCard)
        oponent.showCard(nrCard)
        if games[int(self.idGame)].oneVisible == False:
            #one card
            games[int(self.idGame)].oneVisible = True
            games[int(self.idGame)].nrVisibleCard = nrCard
            print("jedna karta")
        else:
            #two cards
            if games[int(self.idGame)].cards[games[int(self.idGame)].nrVisibleCard] == games[int(self.idGame)].cards[nrCard]:
                #pair
                self.hit(games[int(self.idGame)].nrVisibleCard,nrCard)
                oponent.hit(games[int(self.idGame)].nrVisibleCard,nrCard)
                self.notMove()
                oponent.move()
                if self.id == games[int(self.idGame)].player1:
                    games[int(self.idGame)].pointsP1 = games[int(self.idGame)].pointsP1 + 1
                    print("punkt1")
                else:
                    games[int(self.idGame)].pointsP2 = games[int(self.idGame)].pointsP2 + 1
                    print("punkt2")
                games[int(self.idGame)].pairs = games[int(self.idGame)].pairs - 1
                if (games[int(self.idGame)].pairs == 0):
                    print("sprawdzam wynik")
                    self.notMove()
                    oponent.notMove()
                    #player1 win
                    if games[int(self.idGame)].pointsP1 > games[int(self.idGame)].pointsP2:
                        if self.id == games[int(self.idGame)].player1:
                            oponent.win()
                            self.lose()
                        else:
                            oponent.lose()
                            self.win()
                    #player2 win
                    else:
                        if self.id == games[int(self.idGame)].player1:
                            self.win()
                            oponent.lose()
                        else:
                            oponent.win()
                            self.lose()
                    games[int(self.idGame)].end = True
                print("para")
            else:
                #mishit
                self.miss(games[int(self.idGame)].nrVisibleCard,nrCard)
                oponent.miss(games[int(self.idGame)].nrVisibleCard,nrCard)
                self.notMove()
                oponent.move()
                print("pudlo")
            games[int(self.idGame)].oneVisible = False
            print("dwie karty")

    def showCard(self,nrCard):
        if (games[int(self.idGame)].cards[nrCard]=="circle"):
            message = struct.pack('bbb',4,0,nrCard)
        if (games[int(self.idGame)].cards[nrCard]=="square"):
            message = struct.pack('bbb',4,1,nrCard)
        if (games[int(self.idGame)].cards[nrCard]=="rect"):
            message = struct.pack('bbb',4,2,nrCard)
        print(struct.unpack('bbb',message))
        self.write_message(message,True)

    def win(self):
        message = struct.pack('bbb',2,1,0)
        print(struct.unpack('bbb',message))
        self.write_message(message,True)

    def lose(self):
        message = struct.pack('bbb',2,0,0)
        print(struct.unpack('bbb',message))
        self.write_message(message,True)     

    def move(self):
        message = struct.pack('bbb',3,1,0)
        print(struct.unpack('bbb',message))
        self.write_message(message,True) 

    def notMove(self):
        message = struct.pack('bbb',3,0,0)
        print(struct.unpack('bbb',message))
        self.write_message(message,True) 

    def hit(self,nrCard1,nrCard2):
        message = struct.pack('bbb',1,nrCard1,nrCard2)
        print(struct.unpack('bbb',message))
        self.write_message(message,True)
        
    def miss(self,nrCard1,nrCard2):
        message = struct.pack('bbb',0,nrCard1,nrCard2)
        print(struct.unpack('bbb',message))
        self.write_message(message,True)

    def sendId(self,pid):
        message = struct.pack('bbb',5,pid,0)
        print(struct.unpack('bbb',message))
        self.write_message(message,True)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", Player)
    ])
 
if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    tornado.web.Application(debug= True,autoreload=True)
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()