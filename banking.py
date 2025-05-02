import random
import time
import sqlite3
from luhnformula import luhnformula as lf

def createPin():
    """
    Creates a random, 4 digit PIN.
    :return: str
    """
    pin = ''
    for digit in range(4):
        pin += str(random.randrange(0, 10, 1))  # Random digits 0-9
    return pin

def createCC():
    """
    Creates a random, 15 digit number leading off with 400000 then adds a Luhn check digit.
    :return: str
    """
    cc = '400000'  # We need 9 more random digits

    for digit in range(9):
        cc += str(random.randrange(0, 10, 1))  # This is the base, 15-digit account #
        # cc = '400000844943340' # 15 digits that should end with a checksum of 57, thus 3 gets it to 60.
        # Why 60? The Luhn Algorithm calculates checksums that are divisible by 10.

    cc = lf.addcheckdigit(cc)  # Calculate and append the checksum digit.
    return cc

def mainMenu():
    print('1. Create an account\n'
          '2. Log into account\n'
          '0. exit')
    choice = input()
    return choice

def accountMenu():
    '''
    The menu for checking the account balance and doing other account actions.
    :return pick: str
    '''
    print('1. Balance\n'
          '2. Add income\n'
          '3. Do transfer\n'
          '4. Close account\n'
          '5. Log out\n'
          '0. exit')
    pick = input()
    return pick

def recordCard(con, cur, CC, PIN):
    """
    Saves a new card's info to the db.
    :param con:
    :param cur:
    :param CC:
    :param PIN:
    :return:
    """
    query = f'INSERT INTO card (number, pin, balance)'\
            f'VALUES (\'{CC}\', \'{PIN}\', 0)'
    cur.execute(query)
    con.commit()

def insertNew(file, table, num, pin, bal=0):
    """
    Creates a new account.
    :param file: path
    :param table: string
    :param num: string
    :param pin: string
    :param bal: int, default = 0
    :return: None
    """
    query = f'INSERT INTO {table} (number, pin, balance) VALUES ({num}, {pin}, {bal});'
    with sqlite3.connect(file) as con:
        cur = con.cursor()
        cur.execute(query)

def createTable(file, table):
    """
    Creates the SQlite db file if necessary
    :return: con object
    """
    query = (f'CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY, '
             'number TEXT, pin TEXT, balance INTEGER DEFAULT 0);')
    with sqlite3.connect(file) as con:
        cur = con.cursor()
        cur.execute(query)
    '''
    This command is skipped if the table already exists in card.s3db. con and cur still exist.
    '''
    return con

def makeDeposit(file, table, num, pin, amount):
    """
    Adds to an account, reports success.
    :param file: path
    :param table: string
    :param num: string
    :param pin: string
    :param amount: int
    :return: None
    """
    balance = getBalance(file, table, num, pin)
    balance += amount
    query = f'UPDATE {table} SET balance = {balance} WHERE number = {num} and pin = \'{pin}\';'
    with sqlite3.connect(file) as con:
        cur = con.cursor()
        cur.execute(query)
    print('Income was added!')

def login_db(file, table, num, pin):
    """
    logs into an account, reports success or failure.
    :param file: path
    :param table: string
    :param num: string
    :param pin: string
    :return: boolean
    """
    query = f'SELECT pin FROM {table} WHERE number = {num}'
    with sqlite3.connect(file) as con:
        cur = con.cursor()
        cur.execute(query)
        try:
            success = (cur.fetchone()[0] == pin)
        except TypeError:  # A nonexistent account number will return None.
            success = False
        print('You have successfully logged in!' if success else 'Wrong card number or PIN!')
        return success

def getBalance(file, table, num, pin):
    """
    returns a tuple with one element, the balance
    :param file: The db file
    :param table: The table in the file
    :param num: The account number
    :param pin: The user's PIN
    :return: int
    """
    query = f'SELECT balance FROM {table} WHERE number = {num} AND pin = \'{pin}\';'
    with sqlite3.connect(file) as con:
        cur = con.cursor()
        cur.execute(query)
        return cur.fetchone()[0]

def closeAccount(file, table, num, pin):
    """
    Deletes the account with the supplied account number and PIN.
    Reports its success.
    :param file: path
    :param table: string
    :param num: string
    :param pin: string
    :return: None
    """
    query = f'DELETE FROM {table} WHERE NUMBER = {num} AND pin = \'{pin}\';'
    with sqlite3.connect(file) as con:
        cur = con.cursor()
        cur.execute(query)
    print('The account has been closed')

def doTransfer(file, table, source, pin, target, amount):
    """
    Transfers money between two accounts. Checks for sufficient funds first.
    Reports success or failure.
    :param file: path
    :param table: string
    :param source: string
    :param pin: string
    :param target: string
    :param amount: int
    :return: None
    """
    source_bal = getBalance(file, table, source, pin)
    if amount > source_bal:
        print('Not enough money!')
        return None  # Drop out if insufficient funds.
    else:
        query1 = f'UPDATE {table} SET balance = balance + {amount} WHERE number = {target};'
        query2 = f'UPDATE {table} SET balance = balance - {amount} WHERE number = {source};'
        with sqlite3.connect(file) as con:
            cur = con.cursor()
            cur.execute(query1)
            cur.execute(query2)
        print('Success!')

def checkForAccount(file, table, account):
    """
    Checks for a valid account number.
    :param file: path
    :param table: string
    :param account: string
    :return: boolean
    """
    query = f'SELECT id FROM {table} WHERE number = {account};'
    with sqlite3.connect(file) as con:
        cur = con.cursor()
        cur.execute(query)
        return (cur.fetchone() != None)
        # This is a tuple if the account exists,
        # None if it doesn't.

if __name__ == '__main__':

    db_file = './card.s3db'
    db_table = 'card'
    createTable(db_file, db_table)  # Creates the db and table if necessary

    random.seed(time.time())  # Make it closer to truly random.

    accounts = []
    pins = []
    '''
    These are lists of dictionaries.
    '''

    choice = mainMenu()

    while choice != '0':
        if choice == '1':
            account = createCC()
            pin = createPin()
            accounts.append({account: 0})  # Append the account number with the balance set to 0.
            pins.append({account: pin})  # Append the account number with the PIN.
            # recordCard(con, cur, account, pin)
            insertNew(db_file, 'card', account, pin)
            print(f"Your card has been created\n"
                  f"Your card number:\n"
                  f"{account}\n"
                  f"Your card PIN:\n"
                  f"{pin}")

        elif choice == '2':
            card = input('Enter your card number: ')
            PIN = input('Enter your PIN: ')
            login = login_db(db_file, 'card', card, PIN)
            pick = None  # It's gotta start somewhere!
            if login:  # A valid card number and PIN have been entered.
                while pick != '5':  # Not logout.
                    pick = accountMenu()
                    if pick == '1':  # Locate the account balance.
                        bal = getBalance(db_file, db_table, card, PIN)
                        print(f'Balance: {bal}')
                        pick = None  # Reset the flag.
                    elif pick == '0':  # Exit the program immediately.
                        print('Bye!')
                        exit()
                    elif pick == '2':
                        # Add income.
                        income = int(input('Enter income: '))
                        makeDeposit(db_file, 'card', card, PIN, income)
                        pick = None  # Reset the flag.
                    elif pick == '3':
                        target = input('Enter card number: ')
                        if lf.isvalid(target):
                            if checkForAccount(db_file, db_table, target):
                                amount = int(input('Enter much money you want to transfer: '))
                                doTransfer(db_file, db_table, card, PIN, target, amount)
                            else:
                                print('Such a card does not exist.')
                        else:
                            print('Probably you made a mistake in the card number. Please try again!')
                        pick = None  # Reset the flag.
                    elif pick == '4':
                        closeAccount(db_file, db_table, card, PIN)
                        pick = '5'  # Return to the main menu.
                    else:
                        pass  # Must have been 5, log out.

        choice = mainMenu()

    print('Bye!')