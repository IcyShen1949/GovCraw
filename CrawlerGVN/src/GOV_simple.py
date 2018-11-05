# coding=utf-8
from urllib import request
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
import json
import nltk
import jieba
import jieba.posseg as psg
from tqdm import tqdm
import datetime
import matplotlib.pyplot as plt
import numpy as np
# import tushare as ts
Num_page = 10
Delta_day = 20
data_path = "E:/python/ljs/CrawlerGVN/data/"
def preHref(L):
    href = []
    text = []
    date = []
    for item in L:
        text.append(re.sub(r'\xa0', "", item.text) )
        href.append(item.a["href"])
        date.append(item.span.text)
    return pd.DataFrame({"date":date, "text":text,"href":href})


def get_list(url):
    try:#网络反应迟钝
        RootPage = request.urlopen(url)
    except:
        # time.sleep(10)
        RootPage = request.urlopen(url)

    # data_path = "E:/python/ljs/CrawlerGVN/data/"
    # RootPage = open(data_path + "国务院常务会议(1)_国务院.html")
    soup = BeautifulSoup(RootPage, from_encoding="utf8")
    ul = soup.body.ul
    return ul.find_all("h4")

def getAllList():
    if os.path.exists(data_path + "listText.csv"):
        listText = pd.read_csv(data_path + "listText.csv", encoding = "gbk")
    else:
        parent_url = "http://sousuo.gov.cn/column/30562/"
        L = []
        for page_num in tqdm(range(Num_page)):
            url = parent_url + str(page_num) + ".htm"
            temp = get_list(url)
            L.extend(temp)

        listText = preHref(L)
        # listText["text"][58] = re.sub(r'\xa0', "", listText["text"][58])
        # listText["text"][172] = re.sub(r'\xa0', "", listText["text"][172])
        print(len(listText))
        listText.to_csv(data_path + "listText.csv", index= False, encoding="gbk")
    return listText

def generateContent(listText):
    title = []
    for i in tqdm(range(len(listText))):
        url = listText["href"][i]
        Page = request.urlopen(url)
        soup = BeautifulSoup(Page, from_encoding="utf8")
        mida = soup.find_all("div", attrs = {"class":"left_area zthy"})
        mida2 = soup.find_all("div", attrs={"class": "left_area"})
        if ((len(mida) < 1) and (len(mida2) > 0)):
            midUrl = mida2[0].a["href"]
            if midUrl.startswith(".."):
                midUrl = "http://www.gov.cn/guowuyuan" + midUrl.lstrip("..")
            temp = BeautifulSoup(request.urlopen(midUrl), from_encoding="utf8")
        elif len(mida) == 1 :
            midUrl = mida[0].a["href"]
            temp = BeautifulSoup(request.urlopen(midUrl), from_encoding="utf8")
        else:
            temp = soup
        title.append(temp.title.text)
        temp_para = temp.find_all("p")
        temp_text = []
        for ii in range(len(temp_para)):
            if temp_para[ii].text != "\n":
                cur_key = re.sub(r'[\xa0\u2022]', "", temp_para[ii].text)
                cur_title = cur_key.split("\n")[0]
                cur_key = "\n".join(cur_key.split("\n")[1:])
                Num = ii
                break
        for j in range((Num + 1) , len(temp_para)):
            cur_para = temp_para[j].text
            if len(cur_para) > 0:
                temp_text.append(cur_para)
        cur_text = re.sub(r'[\xa0\u2022]', "", "\n".join(temp_text[1:]))
        with open(data_path + str(i) + ".json", "w") as f:
            json.dump({"text": cur_text, "KeySent": cur_key, "title": cur_title} , f, ensure_ascii=False)

def get_data():
    listText = getAllList()
    if not os.path.exists(data_path + str(0) + ".json"):
        generateContent(listText)
    KeySent = []
    FullText = []
    Title = []
    for i in range(len(listText)):
        cur_file = data_path + str(i) + ".json"
        with open(cur_file, "r") as f:
            cur_data = json.load(f)
        os.remove(cur_file)
        KeySent.append(cur_data["KeySent"])
        FullText.append(cur_data["text"])
        Title.append(cur_data["title"])
    listText["FullText"] = FullText
    listText["KeySent"] = KeySent
    listText["Title"] = Title
    listText.to_csv(data_path + "GOVData_final.csv", index=False, encoding="gbk")
    print(len(listText))
    return listText


def word_tokenize(tokens):
    return [token.replace("''", '"').replace("``", '"') for token in nltk.word_tokenize(tokens)]
def get_Nouns():
    data = pd.read_csv(data_path + "GOVData2.csv", encoding="gbk")
    Noun = []
    AllWords = []
    for i in tqdm(range(len(data["KeySent"]))):
        # print(i)
        item = data["KeySent"][i]
        if str(item )== "nan":
            cur_Noun = ""
        else:
            cur_text = "\n".join( item.split("\r\n")[1:])
            words = [(x.word, x.flag) for x in psg.cut(cur_text)]
            cur_Noun = []
            for w, tag in words:
                if tag == "n":
                    cur_Noun.append(w)
                # print(w, tag)
        Noun.append(" ".join(cur_Noun))
        AllWords.extend(cur_Noun)
    data["Noun"] = Noun
    data.to_csv(data_path + "DataWords.csv", index=False, encoding="gbk")
    with open(data_path + "Nouns.txt", "w") as f:
        f.write(" ".join(AllWords))
    return data, AllWords

def get_Ind():
    DataWords = pd.read_csv(data_path + "DataWords.csv", encoding="gbk")
    indus_file = data_path + "行业分类和公募持仓数据样例.csv"
    with open(indus_file, "r", encoding="utf-8") as f:
        ind_data = pd.read_csv(f)
    AllInd = set(ind_data["二级行业名称"])
    with open(data_path + "二级行业.txt", "w") as f:
        f.write(" ".join(AllInd))
    with open(data_path + "Nouns.txt", "r") as f:
        Nouns = f.readlines()[0].split(" ")
    SplitInd = list(jieba.cut(" ".join(AllInd)))
    SplitInd.remove("行业")
    SplitInd.remove("工程")
    Intersect = []
    N = 0
    for i in tqdm(range(len(DataWords["Noun"]))):
        item = DataWords["Noun"][i]
        if ((str(item) != "nan") and (len(item) > 0)  ):
            cur_inter = set(item.split(" ") ) & set(SplitInd)
            Intersect.append(cur_inter)
            if len(cur_inter) > 0:
                N += 1
        else:
            Intersect.append(set())
    Ind = []
    for index in range(len(Intersect)):
        cur_ind = []
        if len(Intersect[index]) > 0:
            for out_item in Intersect[index]:
                for item in AllInd:
                    if out_item in item:
                        cur_ind.append(item)
        Ind.append(" ".join(cur_ind))
    DataWords["Industry"] = Ind
    DataWords.to_csv(data_path + "DataInd.csv", index=False, encoding="gbk")
    with open(data_path + "AllInd.txt", "w") as f:
        f.write(" ".join(Ind))
    return DataWords, Ind

def get_stock():
    indus_file = data_path + "行业分类和公募持仓数据样例.csv"
    with open(indus_file, "r", encoding="utf-8") as f:
        ind_data = pd.read_csv(f)
    ind2code = dict(zip(list(ind_data["二级行业名称"]), list(ind_data["二级行业代码"])))
    with open(data_path + "industry_to_stock.txt", "r") as f:
        ind2stock = eval(f.readlines()[0])
    DataInd, Ind = get_Ind()
    SelInd = list(set(" ".join(Ind).split(" ")))
    SelInd.remove("")
    Stock = []
    for iI in range(len(DataInd)):
        if DataInd["Industry"][iI] != "":
            item = DataInd["Industry"][iI]
            Litem = item.split(" ")

            cur_stock = []
            for Ineitem in Litem:
                cur_stock.extend(ind2stock[ind2code[Ineitem]])
            Stock.append(" ".join(cur_stock))
        else:
            Stock.append("")
    DataInd["Stock"] = Stock
    DataInd.to_csv(data_path + "DataStock.csv", index=False, encoding="gbk")
    SelStock = list(set(" ".join(Stock).split(" ")))
    SelStock.remove("")
    with open(data_path + "SelStock.txt", "w") as f:
        f.write(" ".join(SelStock))
    return DataInd

def cal_returnRate():
    with open(data_path + "SelStock.txt", "r") as f:
        SelStock = f.readlines()
        SelStock = SelStock[0].split(" ")

    for code in tqdm(SelStock):
        stock = pd.read_csv(data_path + "Stock/" + code + ".csv")
        temp1 = list(stock["close"].diff().values)
        temp2 = [float("nan")] * len(temp1)
        temp2[1:] = list(stock["close"])[:-1]
        stock["returnRate"] = np.array(temp1) / np.array(temp2)
        # stock["returnRate"] = stock["close"].diff()
        stock.to_csv(data_path + "Stock/" + code + ".csv", index=False)

def cal_return():
    data = pd.read_csv(data_path + "DataStock.csv", encoding="gbk")
    data["date"] = pd.to_datetime(data["date"])
    Standard = pd.read_csv(data_path + "Stock/" + "600015" + ".csv")
    AvgReturn = []
    AllRe = {}
    for index in tqdm(range(len(data))):
        item = data["Stock"][index]

        if isinstance(item , str):
            Sts = item.split(" ")
            Stemp = pd.DataFrame([0] * len(Standard),columns={"returnRate"}, index=Standard["date"])
            Re = {}
            for code in Sts:
                cur_s = pd.read_csv(data_path + "Stock/" + code + ".csv").set_index("date")
                temp = cur_s["returnRate"] + Stemp["returnRate"]
                Re[code] = temp
            Selcode = pd.DataFrame(Re, columns=Re.keys(), index = Standard["date"])
            AllRe.update(Re)
            Avg = Selcode.mean(axis = 1)
            Avg = pd.DataFrame(Avg.values, columns={"returnRate"}, index = Avg.index)
            AvgReturn.append(index)
            Avg.to_csv(data_path + "Avg/" + str(index) + ".csv")
        else:
            AvgReturn.append(-1)
    Allcode = pd.DataFrame(AllRe, columns=AllRe.keys(), index=Standard["date"])
    Allcode.to_csv(data_path + "AllReturn.csv", index=False, encoding="gbk")
    data["AvgReturn"] = AvgReturn
    data.to_csv(data_path + "DataReturn.csv", index=False, encoding="gbk")
    return data

def main():
    cal_returnRate()
    _ = cal_return()
    Standard = pd.read_csv(data_path + "Stock/" + "600015" + ".csv")
    data = pd.read_csv(data_path + "DataReturn.csv", encoding="gbk")
    x = list(range(1, 11))
    y = np.zeros((10, 1))
    Num = 0
    for index in tqdm(range(len(data))):
        item = data["Stock"][index]
        if isinstance(item, str):
            cur_date = data["date"][index]  # .strftime("%Y-%m-%d")
            ReAvg = pd.read_csv(data_path + "Avg/" + str(index) + ".csv").set_index("date")
            if cur_date not in Standard["date"].values:
                for day in range(5):
                    cur_date = (datetime.datetime.strptime( data["date"][index], "%Y-%m-%d") + datetime.timedelta(days=day)).strftime("%Y-%m-%d")
                    if cur_date in Standard["date"].values:
                        break

            end_date = ( datetime.datetime.strptime( cur_date, "%Y-%m-%d")+ datetime.timedelta(days=Delta_day + 1)).strftime("%Y-%m-%d")
            plt.figure()
            plt.plot(list(range(1, 11)), ReAvg[cur_date:end_date].values[:10])#ReAvg[cur_date:end_date].index.values
            plt.savefig(data_path + "figure/" + cur_date + ".png")
            y += ReAvg[cur_date:end_date].values[:10] * len(item.split(" "))
            Num += len(item.split(" "))
            # plt.show()

    Avgy = y / float(Num)
    plt.figure()
    plt.plot(x, Avgy)
    plt.savefig(data_path + "figure/Avg.png")


if __name__ == "__main__":
    main()





    # data_file = "E:/python/py3_remote/demo/data/行业分类和公募持仓数据样例.csv"
    # data = pd.read_csv(data_file , encoding="gbk", sep = ",")
    # print(len(data))
# temp = list(set(" ".join(data).split(" ")))
# for code in tqdm(temp):
#     t = ts.get_k_data(code, start="2013-01-01")
#     t.to_csv("./Stock/" + code + ".csv", index=False)
# temp = ts.get_k_data("300431", start="2013-01-01)
