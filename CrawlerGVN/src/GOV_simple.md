# 研究国务院每周报告对行业股票的影响
## 研究思路
因为国务院每周都会定期公布报告，这其中会提到部分行业的相关政策，经过肉眼观察，一般对所提及行业的股票的走势有正向影响，因此希望能够通过对报告的分析，研究股票的走势

---

## 基本流程 及 代码结构
1 爬取数据  

- 根据主列表网页获取每个报告页面的url  
~~~ 
get_list(url): 获取相应的url的列表 返回值url的标题，网址，日期 return list(url)

preHref(L)： 对给定的列表里面的内容，整理成dataframe pd.DataFrame({"date":date, "text":text,"href":href}) return(listText) 

getAllList()： 整合上述两个函数获取上述preHref(L)得到的dataframe return(listText)

generateContent(listText)  {"text": cur_text, "KeySent": cur_key, "title": cur_title} return None

get_data()：处理上述生成的数据， 删除重合部分 return listText

get_Nouns(): 拿到"KeySent"中的所有名词
~~~

2 匹配行业  

- 根据上个过程中得到的名词，结合二级行业名称进行行业匹配
~~~
get_Ind(): 拿到所有的KeySent的名词中，和行业名词重合的 return DataWords, Ind
~~~ 

3 对应相应行业的股票  

- 根据股票行业信息，拿到上述行业交集中所涉及到的所有股票
~~~
get_stock()：拿到每个报告对应行业对应的股票列表 return DataInd
~~~

4 计算每个行业在事件公布10天内的平均收益率  
~~~
cal_returnRate()：计算每只涉及到的股票的收益率
cal_return()：计算每个行业的平均收益率 return data
~~~
5 计算所有涉及到的股票在事件公布10天内的收益率

---

## 结果分析

1 基本上会在一周之内形成比较明显的上升趋势， 之后会波动

---

## 学到了什么
1 字符串日期转换 datetime.datetime.strptime(s, format) #"%Y-%m-%d"  pd.datetime可以将一列字符串转化为日期
2 去掉日期中的时分秒 strftime  
3 股票之间的收益率是可以直接相加的  
4 eval() 读取字典的时候很好用

--- 

## 尚未解决的问题
1 因为直接用pd.datetime转化会带有时分秒，但是存为csv文件之后再读取就没有了，以前的解决方式是在转化时间之后加astype("str")
2 时间的加减 datetime.timedelta
