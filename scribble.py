from Queue import Queue, Empty
from threading import Thread, Timer


###################################################################
###################################################################
###################################################################
###################################################################
#============ define event types ============#
EVENT_TIMER = 'eTimer'
EVENT_LOG = 'eLog'
EVENT_MARKETDATA = 'eMarketData'
EVENT_MARKETDATA_CONTRACT = 'eMarketDataContract'

EVENT_INVESTOR = 'eInvestor'
EVENT_TDLOGIN = 'eTdLogin'
EVENT_ORDER = 'eOrder'
EVENT_ORDER_ORDERREF = 'eOrderOrderRef'
EVENT_TRADE = 'eTrade'
EVENT_TRADE_CONTRACT = 'eTradeContract'

EVENT_POSITION = 'ePosition'
EVENT_ACCOUNT = 'eAccount'
EVENT_INSTRUMENT = 'eInstrument'

EVENT_TIMER_FAST = 'eTimerFast'
EVENT_TIMER_SLOW = 'eTimerSlow'
EVENT_TIMER = 'eTimer'
EVENT_NONE = None

EVENT_HELLO = 'eHello' # test event
#============================================#
###################################################################
###################################################################
###################################################################
###################################################################


class EventEngine(object):

    def __init__(self):
        """
        An eventqueue to stack in events LIFO, activeFlag is a flag
        thread is the event threading, targeting on distribute function
        which get event out of queue and distribute them to the listening 
        functions/objects. Timer is a timer object, push timer events constantly
        """
        self.eventQueue = Queue()
        self.activeFlag = False
        self.thread = Thread(target = self.distribute, name = 'EventThread')
        self.timer = QTimer()
        self.timer.timeout.connect(self.onTimer)
        self.listenerMapping = dict()

    def register(self, eType, func):
        try:
            listeningFuncs = self.listenerMapping[eType]
        except KeyError:
            listeningFuncs = []
            self.listenerMapping[eType] = listeningFuncs
        if func not in listeningFuncs:
            listeningFuncs.append(func)

    def onTimer(self):
        event = Event(eType=EVENT_TIMER)
        event.data = {'time':time.time()}
        self.eventQueue.put(event)

    def distribute(self):
        while self.activeFlag:
            try:
                event = self.eventQueue.get()
                if event.type in self.listenerMapping:
                    [f(event) for f in self.listenerMapping[event.type]]
            except Empty:
                pass

    def startEngine(self):
        self.activeFlag = True
        self.thread.start()
        self.timer.start(200)

    def suspendEngine(self):
        self.activeFlag = False
        self.timer.stop()
        self.thread.join()

    def viewStatus(self):
        print '#----------eventQueue----------#'
        for ev in list(self.eventQueue.queue):
            print ev.data, '#_has_eType#', ev.type
        print '#--------listenerMapping--------#'
        print self.listenerMapping

    def put(self, event):
        self.eventQueue.put(event)

#============================================#
class Event:
    def __init__(self, eType=EVENT_NONE):
        self.type = eType
        self.data = dict()
#============================================#

###################################################################
###################################################################
###################################################################
###################################################################


