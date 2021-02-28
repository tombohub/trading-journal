######
# Interact with Questrade to get trades and other data

import csv
import sys
import json
import datetime
from rich import print
from questrade_api import Questrade

q = Questrade()


def save_executions(date: str):
    """Save executions to executions.json file
    This is so we can delete unwanted orders until we have proper script to select
    only day trading orders

    Args:
        date (str): date of orders executions
    """
    
    # need to add because questrade accepts ISO format
    start_time = date + 'T00:00:00-05:00'
    end_time = date + 'T23:59:59-05:00'
    response = q.account_executions(id=51779544, startTime=start_time, endTime=end_time)
    orders = response['executions']
    # collect only Executed orders
    # orders: list = [order for order in response['orders'] if order['state'] == 'Executed']
    orders.sort(key=lambda exec: exec['id'])
    
    with open('executions.json','w') as file:
        json.dump(orders, file)


def save_orders(date: str):
    """Save orders to orders.json file
    This is so we can delete unwanted orders until we have proper script to select
    only day trading orders

    Args:
        date (str): date of orders execution
    """
    
    # need to add because questrade accepts ISO format
    start_time = date + 'T00:00:00-05:00'
    end_time = date + 'T23:59:59-05:00'
    response = q.account_orders(id=51779544, startTime=start_time, endTime=end_time, stateFilter='All')
    orders = response['orders']
    # collect only Executed orders
    # orders: list = [order for order in response['orders'] if order['state'] == 'Executed']
    orders.sort(key=lambda x: x['id'])
    
    with open('orders.json','w') as file:
        json.dump(orders, file)


def generate_trades(orders):
    pass


def export_csv(orders: list):
    with open('orders.csv', 'w') as csvfile:
        fieldnames = [
            'Date', 
            'Symbol', 
            'Quantity', 
            'Enter Time', 
            'Enter Price', 
            'Exit Time', 
            'Exit Price', 
            'Buy Value', 
            'Sell Value',
            'Commission' ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # loop in pairs to have both buy and sell side
        for buy, sell in zip(orders[::2], orders[1::2]):

            # to make sure buy order is Buy and vice versa
            # in case not all orders are day trade and don't have pairing order
            if buy['side'] != 'Buy' or sell['side'] != 'Sell':
                print('o no, buy  is not buy or sell is not sell!')
                return

            symbol = buy['symbol']
            quantity = buy['filledQuantity']
            enter_time = datetime.datetime.fromisoformat(buy['creationTime'])
            enter_price = buy['avgExecPrice']
            exit_time = datetime.datetime.fromisoformat(sell['creationTime'])
            exit_price = sell['avgExecPrice']
            buy_value = quantity * float(enter_price)
            sell_value = quantity * float(exit_price)
            #comission of EFT is 0 to buy, but Questrade makes is null in response
            commission = float(buy['comissionCharged'] or 0) + sell['comissionCharged']

            writer.writerow({
                'Date': enter_time.date(),
                'Symbol': symbol, 
                'Quantity': quantity,
                'Enter Time': enter_time.time(),
                'Enter Price': enter_price,
                'Exit Time': exit_time.time(),
                'Exit Price': exit_price,
                'Buy Value': buy_value,
                'Sell Value': sell_value,
                'Commission': commission                
            })



def main():
    action = sys.argv[1]
    
    if action == 'save':
        date: str = input('What date you want to get orders yyyy-mm-dd: ')
        save_orders(date)
        save_executions(date)
    elif action == 'export':
        with open('orders.json','r') as file:
            orders = json.load(file)
            export_csv(orders)
    else:
        print('choose "save" or "export"')
        return 

if __name__ == '__main__':
    main()
    


