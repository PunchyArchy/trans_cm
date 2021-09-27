from tkinter import ttk
from tkinter import *
import os
import datetime
from gravity_interface.configs import config as s
from gravity_interface.styles import color_solutions as cs
from gravity_interface.styles import fonts

dirpath = os.path.dirname(os.path.realpath(__file__))


class MainTreeview:
	def __init__(self, master, operator, font='"Roboto" 12'):
		self.master = master
		self.operator = operator
		self.carnumsClose = []
		self.companies = {}
		self.font = font
		self.reverse = False
		self.style = ttk.Style()
		self.style.map("Treeview",
		          foreground=self.fixed_map("foreground"),
		          background=self.fixed_map("background"))
		self.treeviewfg = '#E2E2E2'
		self.metaData = {}

	def sortTime(self, tv, col):
		l = [(tv.set(k, col), k) for k in tv.get_children('')]
		newList = []
		for el in l:
			if el[0] == 'None':
				newList.append(('23:59:59', el[1]))
			else:
				newList.append((el[0],el[1]))
		newList.sort(key=lambda x: datetime.datetime.strptime(x[1], '%H:%M:%S') , reverse=self.reverse)
		for index, (val, k) in enumerate(newList):
			tv.move(k, '', index)
		self.changeReverse()

	def sortDate(self, tv, col):
		l = [(tv.set(k, col), k) for k in tv.get_children('')]
		newList = []
		for el in l:
			if el[0] == 'None':
				newList.append(('23:59 01.01', el[1]))
			else:
				newList.append((el[0],el[1]))
		try:
			newList.sort(key=lambda x: datetime.datetime.strptime(x[0], '%H:%M %d.%m'),
			reverse=self.reverse)
		except:
			newList.sort(key=lambda x: datetime.datetime.strptime(x[0], '%H:%M %d.%m'),
			reverse=self.reverse)
		for index, (val, k) in enumerate(newList):
			tv.move(k, '', index)
		self.changeReverse()

	def sortWeight(self, tv, col):
		print('sorting weight', col)
		l = [(tv.set(k, col), k) for k in tv.get_children('')]
		newList = []
		for el in l:
			if el[0] == 'None':
				newList.append((0, el[1]))
			else:
				newList.append((el[0],el[1]))
		print('newList\n', newList)
		newList.sort(key=lambda t: int(t[0]), reverse=self.reverse)
		for index, (val, k) in enumerate(newList):
			tv.move(k, '', index)
		self.changeReverse()

	def getMovedDate(self, date):
		#date = date.split(' ')
		#date = date[1] + ' ' + date[0]
		try:
			date = date.strftime('%H:%M %d.%m')
		except AttributeError: date = 'None'
		return date

	def changeReverse(self):
		if self.reverse == False:
			self.reverse = True
		else: self.reverse = False

	def sortId(self, tv, col, reverse=False):
		l = [(tv.item(k)["text"], k) for k in tv.get_children()] #Display column #0 cannot be set
		if reverse == False:
			l.sort(key=lambda t: t[0], reverse=self.reverse)
			self.changeReverse()
		else:l.sort(key=lambda t: t[0], reverse=True)
		for index, (val, k) in enumerate(l):
			tv.move(k, '', index)
			
	def sortUsual(self, tv, col):
		l = [(tv.set(k, col), k) for k in tv.get_children('')]
		l.sort(reverse=self.reverse)
		for index, (val, k) in enumerate(l):
			tv.move(k, '', index)
		self.changeReverse()

	def OnClick(self, event):
		col = self.tree.identify_column(event.x)
		print('col', col)
		if self.reverse:
			print('rev', self.reverse)
			self.img = PhotoImage(file=dirpath + os.sep + 'imgs' + os.sep + 'tric.png')
		else:
			print('not rev', self.reverse)
			self.img = PhotoImage(file=dirpath + os.sep + 'imgs' + os.sep + 'tricR.png')
		self.tree.heading(col,anchor='w',image=self.img)
		#self.changeReverse()

	def get_carid(self, carlist, carnum):
		for car in carlist:
			if car[0] == carnum:
				carid = car[1]
				return carid

	def get_idtype(self, carlist, carnum):
		for car in carlist:
			if car[0] == carnum:
				typeid = car[-1]
				return typeid

	def getTodayHistory2(self, tablename, ident='today'):
		request = 'records.id, records.car_number, records.brutto, records.tara,'
		request += 'records.cargo,records.time_in, records.time_out,'
		request += 'records.inside, records.alerts,'
		request += 'clients.short_name, trash_types.name, trash_cats.cat_name,'
		request += 'records.notes, users.username, records.checked'
		if ident == 'today':
			today = datetime.datetime.today()
			ident = "time_in::date = '{}'".format(today)
		joins = "inner join users on (records.operator = users.id) "
		joins += "inner join clients on (records.carrier = clients.id) "
		joins += "inner join trash_cats on (records.trash_cat = trash_cats.id) "
		joins += "inner join trash_types on (records.trash_type = trash_types.id) "
		comm = "SELECT {} FROM {} {} WHERE {}"
		comm = comm.format(request, tablename, joins, ident)
		record = self.operator.send_ar_sql_comm(comm)
		return record

	def getTodayHistory(self, today, tablename):
		comm = "select * from {} where time_in::date = '{}' or time_out::date = '{}'"
		comm = comm.format(tablename, today, today)
		record = self.operator.send_ar_sql_comm(comm)
		return record

	def replaceIdByName(self, rec, pos, dict):
		newList = []
		for el in rec:
			newList.append(el)
		value = self.getKeyByValue(dict, rec[pos])
		newList[pos] = value
		return newList

	def getKeyByValue(self, dict, searchValue):
		for key, value in dict.items():
			if value == searchValue:
				return key

	def getRangeHistory(self, start_date, end_date, typeMode='id', catMode='id'):
		ident = "time_in > '{}' AND time_in <= '{}'".format(start_date, end_date)
		records = self.getTodayHistory2(s.book, ident)
		return records

	def frmtYear(self, date):
		de = date.split('.')[0][2:]
		date = date.replace('2020',de)
		return date

	def fixed_map(self, option):
	    return [elm for elm in self.style.map("Treeview", query_opt=option)
	            if elm[:2] != ("!disabled", "!selected")]

	def get_tree(self):
		return self.tree

	def get_timenow(self):
		'''Возвращает отформатированную, читабельную дату'''
		today = datetime.datetime.today()
		frmt = today.strftime('%Y.%m.%d %H:%M:%S')
		return frmt

	def countStatistic(self, history, carlist):
		for rec in history:
			for car in carlist:
				if rec[0] == car[0]:
					cur = self.companies[car[2]]
					wght = rec[3]
					if type(wght) == type(None):
						wght = 0
					cur += wght
					self.companies[car[2]] = abs(cur)
		return self.companies

	def countCompanies(self, carlist):
		for rec in carlist:
			company = rec[2]
			if company not in self.companies:
				self.companies[company] = 0
		return self.companies

	def clearTree(self):
		self.tree.delete(*self.tree.get_children())

class NotificationTreeview(MainTreeview):
	def __init__(self, operator, master):
		self.errors_desctription = {True: 'Подключение успешно',
									False: 'Подключение утеряно'}
		super().__init__(operator, master)


	def createTree(self):
		self.tree=ttk.Treeview(self.master,style="Custom.Treeview")
		self.tree["columns"]=("one")
		self.tree.column("#0", width=400, minwidth=30, stretch='NO')
		self.tree.column("one", width=1150, minwidth=30, stretch='NO')

		self.tree.heading("#0", text="Пункт", anchor='w')
		self.tree.heading("one", text="Статус", anchor='w')
		self.tree.bind("<Button-1>", self.OnClick)

	def fillTree(self, information):
		self.clearTree()
		for point, info in information.items():
			value = self.errors_desctription[info['status']]
			self.tree.insert("", 0, text=point, values=(value,))


class CurrentTreeview(MainTreeview):
	def init(self, operator, master):
		MainTreeview(self, operator, master)

	def createTree(self):
		self.tree=ttk.Treeview(self.master,style="Custom.Treeview")
		self.tree["columns"]=("one","two", "two1", "two2", "three","four","five")
		self.tree.column("#0", width=137, minwidth=30, stretch='NO')
		self.tree.column("one", width=138, minwidth=30, stretch='NO')
		self.tree.column("two", width=112, minwidth=30, stretch='NO')
		self.tree.column("two1", width=112, minwidth=30, stretch='NO')
		self.tree.column("two2", width=102, minwidth=30, stretch='NO')
		self.tree.column("three", width=138, minwidth=30, stretch='NO')
		self.tree.column("four", width=138, minwidth=30, stretch='NO')
		self.tree.column("five", width=158, minwidth=30, stretch='NO')

		self.tree.heading("#0", text="ID записи",anchor='w',
			command=lambda :self.sortId(self.tree, "#0"))
		self.tree.heading("one", text="Въезд",anchor='w',
			command=lambda :self.sortDate(self.tree, "one"))
		self.tree.heading("two", text="Брутто",anchor='w',
			command=lambda :self.sortWeight(self.tree, "two"))
		self.tree.heading("two1", text="Тара",anchor='w',
			command=lambda :self.sortWeight(self.tree, "two"))
		self.tree.heading("two2", text="Нетто",anchor='w',
			command=lambda :self.sortWeight(self.tree, "two"))
		self.tree.heading("three", text="Категория",anchor='w',
			command=lambda :self.sortUsual(self.tree, "three"))
		self.tree.heading("four", text="Гос. номер",anchor='w',
			command=lambda :self.sortUsual(self.tree, "four"))
		self.tree.heading("five", text="Комментарии",anchor='w',
			command=lambda :self.sortUsual(self.tree, "five"))
		self.tree.bind("<Button-1>", self.OnClick)

	def fillTree(self):
		self.clearTree()
		timenow = datetime.datetime.now()
		#timenow = timenow.strftime('%d.%m.%Y %H:%M')
		timenow = timenow - datetime.timedelta(minutes=5)
		request = 'records.id, records.car_number, records.brutto, records.tara,'
		request += 'records.cargo, trash_cats.cat_name, records.time_in,'
		request += 'records.notes'
		tablenames = 'trash_cats, {}'.format(s.book)
		ident = "(inside='True' or time_out > '{}')".format(timenow)
		ident += "and trash_cats.id = records.trash_cat"
		comm = "select {} from {} where {}"
		comm = comm.format(request, tablenames, ident)
		#print('comm-', comm)
		record = self.operator.send_ar_sql_comm(comm)
		#print('record for inserting -', record)
		for rec in record:
			self.tree.insert("",1,text=rec[0],values=(self.getFrmtDate(rec[6]),
			rec[2], rec[3],rec[4], rec[5], rec[1], rec[7]))

	def getFrmtDate(self, date):
		#olddate = datetime.strptime(date, '%Y.%m.%d %H:%M:%S')
		newdate = date.strftime('%H:%M %d.%m')
		return newdate

class BansTreeview(MainTreeview):
	def init(self, operator, master):
		MainTreeview(self, operator, master)

	def createTree(self):
		self.tree=ttk.Treeview(self.master,style="Custom.Treeview")
		self.tree["columns"]=("one","two")
		self.tree.column("#0", width=300, minwidth=30, stretch='NO')
		self.tree.column("one", width=450, minwidth=30, stretch='NO')
		self.tree.column("two", width=300, minwidth=30)
		self.tree.bind("<Button-1>", self.OnClick)

		self.tree.heading("#0",text="Клиент",anchor='w',
			command=lambda :self.sortClients(self.tree, "#0"))
		self.tree.heading("one", text="Причина",anchor='w',
			command=lambda :self.sortUsual(self.tree, "one"))
		self.tree.heading("two", text="Дата",anchor='w',
			command=lambda :self.sortDate(self.tree, "two"))

	def fillTree(self, debtorsList):
		self.clearTree()
		for debtor in debtorsList:
			self.tree.insert("",1,text=debtor['name'],values=(debtor['reason'],debtor['time']))
			#self.getFrmtDate(debtor['time'])))

	def getCarnums(self):
		return self.carnumsClose

	def sortClients(self, tv, col):
		l = [(tv.item(k)["text"], k) for k in tv.get_children()] #Display column #0 cannot be set
		l.sort(reverse=self.reverse)
		for index, (val, k) in enumerate(l):
			tv.move(k, '', index)
		self.changeReverse()


class HistroryTreeview(MainTreeview):
	def init(self, operator, master):
		MainTreeview(self, operator, master)

	def createTree(self):
		self.tree=ttk.Treeview(self.master, style="Custom.Treeview",)
		self.tree["columns"]=("1","2","3","4","5", "6","7","8","9","10","11")
		self.tree.column("#0", width=104, minwidth=50, anchor='w')
		#self.tree.column("preone", width=50, minwidth=30, stretch='NO')
		self.tree.column("1", width=140, minwidth=30, stretch='NO')
		self.tree.column("2", width=185, minwidth=30, anchor='w')
		self.tree.column("3", width=110, minwidth=30, stretch='NO')
		self.tree.column("4", width=110, minwidth=30, stretch='NO')
		self.tree.column("5", width=108, minwidth=30, stretch='NO')
		self.tree.column("6", width=140, minwidth=30, stretch='NO')
		self.tree.column("7", width=140, minwidth=30)
		self.tree.column("8", width=140, minwidth=30, stretch='NO')
		self.tree.column("9", width=140, minwidth=30, stretch='NO')
		self.tree.column("10", width=90, minwidth=30, stretch='NO')
		self.tree.column("11", width=190, minwidth=30, stretch='NO')
		self.tree.bind("<Button-1>", self.OnClick)
		self.tree.heading("#0", text="ID",anchor='w',
			command=lambda :self.sortId(self.tree, "#0"))
		#self.tree.heading("preone", text="ID машины",anchor='w')
		self.tree.heading("1", text="Гос. номер",anchor='w',
			command=lambda :self.sortUsual(self.tree, "1"))
		self.tree.heading("2", text="Перевозчик",anchor='w',
			command=lambda :self.sortUsual(self.tree, "2"))
		self.tree.heading("3", text="Брутто",anchor='w',
			command=lambda :self.sortWeight(self.tree, "3"))
		self.tree.heading("4", text="Тара",anchor='w',
			command=lambda :self.sortWeight(self.tree, "4"))
		self.tree.heading("5", text="Нетто",anchor='w',
			command=lambda :self.sortWeight(self.tree, "5"))
		self.tree.heading("6", text="Категория",anchor='w',
			command=lambda :self.sortUsual(self.tree, "6"))
		self.tree.heading("7", text="Вид груза",anchor='w',
			command=lambda :self.sortUsual(self.tree, "7"))
		self.tree.heading("8", text="Дата въезда",anchor='w',
			command=lambda: self.sortDate(self.tree,"8"))
		self.tree.heading("9", text="Дата выезда",anchor='w',
			command=lambda: self.sortDate(self.tree,"9"))
		#self.tree.heading("seven", text="На территории",anchor='w')
		self.tree.heading("10", text='Примечания', anchor='w',
			command=lambda :self.sortUsual(self.tree, "10"))
		self.tree.heading("11", text="Комментарии",anchor='w',
			command=lambda :self.sortUsual(self.tree, "11"))

	def fillTree(self, history, trashcat='кат. груза', trashtype='вид груза',
	contragent='перевозчики', carnum='гос. номер'):
		marks = ''
		self.clearTree()
		print('history is', history)
		if trashcat != 'кат. груза':
			marks += '1'
		else: marks += '0'
		if trashtype != 'вид груза':
			marks += '1'
		else: marks += '0'
		if contragent != 'перевозчики' and contragent != '':
			marks += '1'
		else: marks += '0'
		if carnum != 'гос. номер' and carnum != '':
			marks += '1'
		else: marks += '0'
		print('marks is', marks)
		if marks.count('1') <= 1:
			for rec in history:
				#print('rec from history insterting', rec)
				if marks == '0000':
					self.insertRec(rec)
				if marks[0] == '1' and trashcat == rec[11]:
						self.insertRec(rec)
				if marks[1] == '1' and trashtype == rec[10]:
						self.insertRec(rec)
				if marks[2] == '1' and contragent == rec[9]:
						self.insertRec(rec)
				if marks[3] == '1' and carnum == rec[1]:
						self.insertRec(rec)
		else:
			for rec in history:
				show = True
				for liter in marks:
					if marks[0] == '1' and trashcat != rec[11]:
						show = False
					if marks[1] == '1' and trashtype != rec[10]:
						show = False
					if marks[2] == '1' and contragent != rec[9]:
						show = False
					if marks[3] == '1' and carnum != rec[1]:
						show = False
				if show == True:
					print('here a')
					self.insertRec(rec)

	def insertRec(self, rec):
		if rec[8] != None and rec[8] > '' and rec[14] == None:
			self.tree.insert("",1,text=rec[0], tags=('red',),values=(rec[1],
				rec[9], rec[2], rec[3],rec[4], rec[11],rec[10],
				self.getMovedDate(rec[5]), self.getMovedDate(rec[6]),
				rec[8], rec[12]))
		elif rec[8] != None and rec[8] > '' and rec[14] == True:
			self.tree.insert("",1,text=rec[0], tags=('green',),values=(rec[1],
				rec[9], rec[2], rec[3],rec[4], rec[11],rec[10],
				self.getMovedDate(rec[5]), self.getMovedDate(rec[6]),
				rec[8], rec[12]))
		else:
			self.tree.insert("",1,text=rec[0],values=(rec[1],
				rec[9], rec[2], rec[3],rec[4], rec[11],rec[10],
				self.getMovedDate(rec[5]), self.getMovedDate(rec[6]),
				rec[8], rec[12]), tags='usual')
		self.tree.tag_configure('red', background='#BE6161',
			foreground=self.treeviewfg, font=fonts.statistic_tree_font)
		self.tree.tag_configure('usual', background=cs.treeview_bg_color,
			font=fonts.statistic_tree_font, foreground=self.treeviewfg)
		self.tree.tag_configure('green', background='#009C7C',
			font=fonts.statistic_tree_font, foreground=self.treeviewfg)
