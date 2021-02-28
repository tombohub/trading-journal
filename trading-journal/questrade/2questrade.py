from questrade_api import Questrade
import os
import json
import datetime
import time

class QuestradeApiHandler:

    q = object()
    refresh_token = None #if this class gets initialized with a refresh token
    validated = False
    symbols_ids_filename = ".questrade_syms.json" # We'll save all symbol ids that we ever fetched in this file. This will save us time (and api calls). Found under ~/.questrade_syms.json
    symbols_ids = {} #symbol ids will be saved in this dict for quick access (should be identical to the file above...and both will always be auto updated)
    default_token_filename = ".questrade.json" # the library we're importing stores refresh token info here

    def __init__(self, refresh_token=None):
        self.refresh_token = refresh_token

        # First, if a refresh token was past, try to use it
        if refresh_token:
            try:
                self.q = Questrade(refresh_token=refresh_token)
                time = self.q.time

                if 'time' in time:
                    self.validated = True
            except Exception as e:
                print('Exception occurred', e)
            finally:
                if self.validated:
                    print("Questrade API validated")
                    self._read_symbols_ids()
                else:
                    print("Failed to initialize API using token: ", refresh_token)
            
        # otherwise, we'll try to init the API using any potentially stored refresh tokens (by the library)
        else:
            try:
                self.q = Questrade()
                time = self.q.time

                if 'time' in time:
                    self.validated = True
            except: #if it failed, then try to manually read the refresh token saved in the local json file. "~/.questrade.json"
                _refresh_token = None

                default_file = os.path.join(os.path.expanduser('~'), self.default_token_filename)

                if os.path.exists(default_file):
                    with open(default_file) as f:
                        token_json = json.load(f)

                        if 'refresh_token' in token_json:
                            _refresh_token = token_json['refresh_token']

                if _refresh_token:
                    self.q = Questrade(refresh_token=_refresh_token)
                    time = self.q.time

                    if 'time' in time:
                        self.validated = True
            finally:
                if self.validated:
                    print("Questrade API validated")
                    self._read_symbols_ids() # attempt to read all symbol ids that we have fetched in the past
                else:
                    print("Not validated!")

    def _add_symbol_id(self, symbol, id):
        if symbol not in self.symbols_ids:
            self.symbols_ids[symbol] = {}
            self.symbols_ids[symbol]['sym_id'] = id
            self.symbols_ids[symbol]['date_retrieved_EST'] = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
            self.symbols_ids[symbol]['date_retrieved_timestamp'] = round(time.time())

            # now save to our file
            self._update_symbols_file()

    def _update_symbols_file(self):
        symbols_ids_file = os.path.join(os.path.expanduser('~'), self.symbols_ids_filename)
        
        with open(symbols_ids_file, 'w') as json_file:
            json.dump(self.symbols_ids, json_file)

    def _get_sym_id_for_symbol(self, symbol=None):
        sym_id = None

        if self.is_validated() and symbol:
            symbol = symbol.upper()

            if symbol in self.symbols_ids:
                return self.symbols_ids[symbol]['sym_id']

            else:
                results = self.q.symbols_search(prefix=symbol)
                
                for result in results['symbols']:
                    if result['symbol'].upper() == symbol:
                        sym_id = result['symbolId']
                        self._add_symbol_id(symbol=symbol, id=sym_id)
                        break

        return sym_id

    def is_validated(self):
        return self.validated

    def _read_symbols_ids(self):
        if self.is_validated():
            symbols_ids_file = os.path.join(os.path.expanduser('~'), self.symbols_ids_filename)

            if os.path.exists(symbols_ids_file):
                with open(symbols_ids_file) as f:
                    self.symbols_ids = json.load(f)

    def get_intraday_candles(self, symbol=None, timeframe="OneMinute"):
        '''
        Returns Last 2000 candles
        Options are: OneMinute, TwoMinutes, ThreeMinutes, FourMinutes, FiveMinutes, TenMinutes, FifteenMinutes, TwentyMinutes, HalfHour, OneHour, TwoHours, ThreeHours, FourHours
        OneDay, OneWeek, OneMonth, OneYear
        '''
        if self.is_validated() and symbol and timeframe:
            sym_id = self._get_sym_id_for_symbol(symbol=symbol)

            if sym_id > 0:
                return self.q.markets_candles(sym_id, interval=timeframe)
        
        return None

    def get_previous_close(self, symbol):
        """
        Gets the previous closing price of a symbol (1 api call. 2 calls if symbol was never ever retrieved before)
        """
        prev_close = None

        if self.is_validated() and symbol:
            try:
                sym_id = self._get_sym_id_for_symbol(symbol=symbol)

                if sym_id:
                    res = self.q.symbol(sym_id)

                    if 'symbols' in res:
                        prev_close = res['symbols'][0]['prevDayClosePrice']

            except Exception as e:
                print(f"Couldn't get previous close for symbol {symbol}", e)
                prev_close = None

        return prev_close

    def get_last_price(self, symbol, regular_hours_only=False):
        """
        Gets the last traded price for symbol
        If regular_hours_only is set to True, then only get last trading price using regular market hours
        """
        last_price = None
        price_key = "lastTradePriceTrHrs" if regular_hours_only else "lastTradePrice"

        if self.is_validated() and symbol:
            try:
                sym_id = self._get_sym_id_for_symbol(symbol=symbol)

                if sym_id:
                    res = self.q.markets_quote(sym_id)

                    if 'quotes' in res:
                        last_price = res['quotes'][0][price_key]

            except Exception as e:
                print(f"Couldn't get last price for symbol {symbol}", e)
                last_price = None

        return last_price


ko = QuestradeApiHandler()

mo = ko.get_last_price(symbol='QS', regular_hours_only=True)
print(mo)