import numpy as np
import time
import pandas as pd
import xlsxwriter
import os

#this page helping us to re-use functions and variables without writing them more then once

product_type = ["stock", "etf"]

prefix = ["", "K", "M", "B", "T", "k", "m", "b", "t"]

borsas_index = []

stock_sectors = ["Basic Materials", "CONSUMER_CYCLICAL", "Financial Services", "Realestate", "Consumer Defensive",
                "Healthcare", "Utilities", "Communication Services", "Energy", "Industrials", "Technology"]
bond_sectors = ["US Government", "AAA", "AA", "A", "BBB", "BB", "B", "Below B", "others"]
all_sectors = stock_sectors + bond_sectors

headlines = np.asarray([
    "averageValume",
    "currency",
    "debt_to_assent",
    "industry",
    "last_full_year_div",
    "leveraged",
    "marketCap",
    "previousClose",
    "product_type",
    "profitability",
    "sector",
    "trailingPe",
    "yield_1y",
    "yield_5y"
])

currency = ["USD", ]


default_values = {
    "averageValume": -1,
    "currency": "-1",
    "debt_to_assent": -1,
    "industry": "-1",
    "last_full_year_div": -1,
    "leveraged": False,
    "marketCap": -1,
    "name": "name",
    "previousClose": -1,
    "price_history": [],
    "product_type": "-1",
    "profitability": -1,
    "sector": "-1",
    "trailingPe": -1,
    "yearly_dividend": [],
    "yield_1y": -1,
    "yield_5y": -1
}

fields = [
    "symbol",
    "averageValume",
    "currency",
    "debt_to_assent",
    "industry",
    "last_full_year_div",
    "leveraged",
    "marketCap",
    "name",
    "previousClose",
    "price_history",
    "product_type",
    "profitability",
    "sector",
    "trailingPe",
    "yearly_dividend",
    "yield_1y",
    "yield_5y"
]

def leng(x):
    return len(str(x))


def sql_to_show(data):
    return [data[0],
            data[1],
            data[2],
            data[3],
            ("Stock" if data[4] == 0 else "ETF"),
            get_sectors_name(data[5]),
            data[6],
            ("Leveraged" if data[7] else "Not Leveraged"),
            two_point_percentage(data[8]),
            two_point_percentage(data[9]),
            two_point_percentage(data[10]),
            add_prefix(data[11])]

# @staticmethod # consider adding to other methods
def convert_string_to_number(number):
    """"for dealing with representing like  -15,010.3M
            relevent for extarcting data from HTML"""
    try:
        minus = False
        if number[0] == "-":
            minus = True
            number = number[1:]
        
        # if the number have one of those prefix we will turn it to the full number
        try:
            multiply = prefix.index(number[-1])
            if multiply != -1:
                multiply = 10**((multiply%4+1)*3) 
                number = number[:-1]
        except: multiply = 1

        divided_number = number.split(",")
        res = 0
        for i in divided_number:
            res = res * 1000 + float(i)

        if minus: res = -1 * res
    
        return res*multiply
    except ValueError:
        return -1

def add_prefix(number):
    try:
        number = float(number)
    except:
        return "-"
    multiply = 0
    for i in range(4):
        if(number >= 1000):
            number = number/1000
            multiply += 1
        else: break

    if number >= 100:
        number = (number//10)*10
    elif number >= 10:
        number = int(round(number))
    else:
        number = round(number*10)//10

    return str(number) + prefix[multiply]
   
def get_relevant_dates(time_length=5, start_time=None, end_time=None):
    """
        :param time_length: int
        :param start_time: tuple or list in the form (d,m,yyyy)
        :param end_time: tuple or list in the form (d,m,yyyy)
         the function complite the missing params and
        :return start time & end time in form of 'd-m-yyyy' 
     """
    
    if end_time is None:
        end_time = time.localtime()[:3][::-1]
    if start_time is None:
        start_time = end_time.copy()
        start_time[2] = start_time[2]-time_length

    start_time = "-".join([str(t) for t in start_time])
    end_time = "-".join([str(t) for t in end_time])
    return start_time, end_time



def get_sectors_name(sector_index):
    try:
        return all_sectors[sector_index]
    except Exception:
        return "index error"

def get_sector_index(sector_name):
    try:
        return all_sectors.index(sector_name)
    except Exception:
        return -1 



def get_benchmark_yield():
    "return QQQ 5 years detailed yield"
    return [1.1003496595751494, 1.0666549243004677, 1.302516102588014, 0.937726452964105, 1.4288811421353493]

def get_benchmark_4y_yield():
    return np.prod(get_benchmark_yield()[1:])

def get_benchmark_dividend():
    "return QQQ 5 years devidends"
    return [0.01067287, 0.01127553, 0.00968813, 0.00822085, 0.00894117, 0.00420541]

def two_point_percentage(number, percentage=False):
    try:
        if not isinstance(number, str):
            number = str(number)
        if not number.isnumeric or number == "-1" or number == "-":
            return "-"

        i = number.find(".")
        if i + 2 < len(number)-2: number = number[:i+2]
        if percentage: number = number + "%"
        return number

    except Exception as e:
        #print("calc.twoPoint.num: "+str(number)+"\n"+str(e))
        return "-"


def find_closest(arr, target, start, end, above):
    """
    @above: true if you want to get the target or the closest above it,
            false if you want to get the target or the closest below it
    """
    if end == start:
        if above:
            if end == len(arr) or arr[start] >= target: return start
            return start + 1
        else:
            if start == 0 or arr[start] <= target: return start
            return start - 1

    mid = (end - start) // 2 + start
    if arr[mid] == target:
        return mid
    if arr[mid] < target:
        return find_closest(arr, target, mid + 1, end, above)
    return find_closest(arr, target, start, mid - 1, above)

def split_word(word):
    # stocks name are usaly long so we split it to 2 lines
    for index in range(max(0, len(word) // 2 - 2), len(word) - 1):
        if word[index] == " ":
            return (word[:index] + "\n" + word[index + 1:])


def filter_data(data):
    for s in data:
        for i in range(len(s))[1:]:
            if default_values[fields[i]] == s[i]:
                s[i] = "-"
            else:
                if i in [1, 7]:
                    s[i] = add_prefix(s[i])
                elif i in [3]:
                    s[i] = two_point_percentage(s[i], True)
                elif i in [5, 9, 14, 16, 17]:
                    s[i] = two_point_percentage(s[i])
    mask_filter = [0, 1, 2, 3, 4, 5, 6, 7, 9, 11, 12, 13, 14, 16, 17]
    return np.vstack((np.hstack((["symbol"], headlines)), data[:, mask_filter]))

def pretty_print(data):
    if len(data) == 0:
        print("there are no stocks left after the filter\nyou should reset your filter and try again")
        return
    data = filter_data(data)
    length = np.zeros((len(data), len(data[0])), dtype=int)
    for i, row in enumerate(data):
        for j in range(len(row)):
            length[i, j] = len(str(row[j]))

    max = np.max(length, axis=0)
    res = ""
    for i, row in enumerate(data):
        for j in range(len(row)):
            res += str(row[j]) + " "*(max[j] - length[i, j] + 4)
        res += "\n"
    print(res)
    pass


def data_to_xlsx(data):
    if len(data) == 0:
        print("there are no stocks left after the filter\nyou should reset your filter and try again")
        return
    file_name = input("enter a name, for the excel file: ")
    workbook = xlsxwriter.Workbook(os.getcwd() + "/data_files/"+file_name+".xlsx")
    worksheet = workbook.add_worksheet()
    data = filter_data(data)
    for row in range(len(data)):
        for col in range(len(data[0])):
            worksheet.write(row, col, data[row][col])
    workbook.close()
    print("the data is ready in file " + file_name + " in folder data_files")



if __name__ == '__main__':
    pass

    #data = np.asarray(pd.read_csv('data_files/data.csv', sep=';', header=None))
    #pretty_print(data[:500])
