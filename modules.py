from gravity_interface.terminal import Terminal
from tkinter import *
from time import sleep
from gravity_interface.widgets.treeview import *
from gravity_interface.widgets.dropDownCalendar import MyDateEntry
from gravity_interface.widgets.drop_down_combobox import AutocompleteCombobox
from gravity_interface.configs import config as s
from datetime import datetime
from gravity_interface.styles import color_solutions as cs
from gravity_interface.styles import fonts


class SysNot(Terminal):
    """ Окно уведомлений"""

    def __init__(self, root, settings, operator, can):
        Terminal.__init__(self, root, settings, operator, can)
        self.name = 'SysNot'
        self.buttons = settings.toolBarBtns
        self.tar = NotificationTreeview(self.root, operator)
        self.tar.createTree()
        self.tree = self.tar.get_tree()
        self.tree.config(height=35)
        self.btn_name = self.settings.notifBtn

    def drawing(self):
        Terminal.drawing(self)
        self.drawWin('maincanv', 'sysNot')
        self.drawTree()
        self.buttons_creation(tagname='winBtn')

    def destroyBlockImg(self, mode='total'):
        Terminal.destroyBlockImg(self, mode)
        self.drawTree()

    def drawTree(self):
        info = self.get_ar_health_monitor()
        self.tar.fillTree(info)
        self.can.create_window(self.w / 1.9, self.h / 1.95, window=self.tree,
                               tag='tree')


class Statistic(Terminal):
    """ Окно статистики """

    def __init__(self, root, settings, operator, can):
        Terminal.__init__(self, root, settings, operator, can)
        self.btns_height = self.h / 4.9
        self.name = 'Statistic'
        self.buttons = settings.statBtns
        #self.font = '"Montserrat SemiBold" 14'
        self.chosenType = ''
        self.chosenContragent = ''
        self.choosenCat = ''
        self.typePopup = ...
        self.carnums = []
        self.filterColNA = '#2F8989'
        self.filterColA = '#44C8C8'
        self.tar = HistroryTreeview(self.root, operator)
        self.tar.createTree()
        self.tree = self.tar.get_tree()
        self.get_carnums()
        self.tree.bind("<Double-1>", self.OnDoubleClick)
        self.posOptionMenus()
        self.calendarsDrawn = False
        self.btn_name = self.settings.statisticBtn

    def OnDoubleClick(self, event):
        '''Реакция на дабл-клик по заезду'''
        item = self.tree.selection()[0]
        self.chosenStr = self.tree.item(item, "values")
        self.record_id = self.tree.item(item, "text")
        if self.chosenStr[3] == 'None':
            self.draw_change_records(self.chosenStr)
        else:
            self.draw_add_comm()

    def draw_change_records(self, string):
        self.parsed_string = self.parse_string(string)
        self.orupState = True
        btnsname = 'record_change_btns'
        self.initBlockImg('record_change_win', btnsname=btnsname, hide_widgets=self.statisticInteractiveWidgets)
        self.posEntrys(self.parsed_string["car_number"], self.parsed_string["trash_type"],
                       self.parsed_string["trash_cat"],
                       self.parsed_string["carrier"], self.parsed_string["notes"], spec_protocols=False,
                       call_method="manual")
        self.root.bind('<Return>', lambda event: self.change_record())
        self.root.bind('<Escape>', lambda event: self.destroyORUP(mode="decline"))
        self.root.bind("<Button-1>", lambda event: self.clear_optionmenu(event))
        self.unbindArrows()

    def parse_string(self, string):
        # Парсит выбранную строку из окна статистики и возвращает словарь с элементами
        parsed = {}
        parsed["car_number"] = string[0]
        parsed["carrier"] = string[1]
        parsed["trash_cat"] = string[5]
        parsed["trash_type"] = string[6]
        parsed["notes"] = string[10]
        return parsed

    def change_record(self):
        info = self.getEntysInfo()
        carrier = self.operator.get_db_info_comm('clients', 'id', "short_name='{}'".format(info['carrier']),
                                                 failure_message='Укажите перевозчика')
        trash_type = self.operator.get_db_info_comm('trash_types', 'id', "name='{}'".format(info['trash_type']),
                                                    failure_message='Укажите вид груза')
        trash_cat = self.operator.get_db_info_comm('trash_cats', 'id', "cat_name='{}'".format(info['trash_cat']),
                                                   failure_message='Укажите категорию груза')
        self.try_upd_record(carrier, trash_type, trash_cat, info['comm'])

    def try_upd_record(self, carrier, trash_type, trash_cat, comm, mode='record_changing'):
        forbide_reason = self.checkDebtor()
        if self.check_absence_error(self.trashTypeOm, self.operator.all_trash_types):
            self.initErrorWin(text='Не опознан вид груза', name=mode)
        elif self.check_absence_error(self.trashCatOm, list(self.operator.trashCatsDict.keys())):
            self.initErrorWin(text='Не опознана категория груза', name=mode)
        elif self.checkOrupContragent():
            self.initNoContragentError(mode)
        elif forbide_reason and self.errorShown == False:
            self.initDebtError(mode, forbide_reason)
        else:
            if not 'Было исправлено.' in comm:
                if len(comm) == 0:
                    comm = 'Было исправлено'
                else:
                    comm = comm + ' Было исправлено.'
            self.send_upd_record_comm(carrier, trash_type, trash_cat, comm)
            self.destroyORUP(mode="total")
            self.drawStatTree()

    def send_upd_record_comm(self, carrier, trash_type, trash_cat, notes):
        msg = {}
        msg['change_record'] = {'carrier': carrier, 'trash_type': trash_type, 'trash_cat': trash_cat,
                                'notes': notes, 'record_id': self.record_id}
        self.send_ar_sys_comm(msg)

    def draw_add_comm(self):
        btnsname = 'addCommBtns'
        self.add_comm_text = self.getText(h=5, w=42, bg=cs.orup_bg_color)
        self.initBlockImg(name='addComm', btnsname=btnsname, seconds=('second'),
                          hide_widgets=self.statisticInteractiveWidgets)
        self.can.create_window(self.w / 2, self.h / 2.05, window=self.add_comm_text, tag='blockimg')
        self.root.bind('<Return>', lambda event: self.add_comm())
        self.root.bind('<Escape>', lambda event: self.destroyBlockImg(mode="total"))

    def add_comm(self):
        msg = {}
        comm = self.add_comm_text.get("1.0", 'end-1c')
        msg['add_comm'] = {'notes': comm, 'record_id': self.record_id}
        self.send_ar_sys_comm(msg)
        self.destroyBlockImg()
        self.drawStatTree()

    def _getCarnums(self, history):
        for rec in history:
            if rec[1] not in self.carnums:
                self.carnums.append(rec[1])

    def posOptionMenus(self):
        self.placeTypeOm()
        self.placeCatOm(bg=self.filterColNA)
        self.placeContragentCombo()
        self.placePoligonOm()
        self.placeCarnumCombo()
        self.ifShowNotes()
        self.statisticInteractiveWidgets = [self.poligonOm, self.trashTypeOm, self.trashCatOm, self.contragentCombo,
                                            self.carnumCombo, self.commentOm]
        self.hide_widgets(self.statisticInteractiveWidgets)

    def abortFiltres(self):
        # self.can.delete('filter')
        # self.posOptionMenus()
        self.trashTypeStat.set('вид груза')
        self.trashCatStat.set('кат. груза')
        self.contragentCombo.set('перевозчики')
        self.poligonVar.set('полигон')
        self.carnumCombo.set('гос. номер')
        self.commentVar.set('примечания')
        self.startCal.set_date(datetime.today())
        self.endCal.set_date(datetime.today())

    def ifShowNotes(self):
        listname = ['примечания', 'Да', 'Нет']
        self.commentVar = StringVar()
        self.commentOm = AutocompleteCombobox(self.root,
                                              textvariable=self.commentVar)
        self.commentOm['style'] = 'statwin.TCombobox'
        self.commentOm.set('примечания')
        self.commentOm.config(width=12, height=30, font=fonts.statistic_filtres)
        self.commentOm.set_completion_list(listname)
        self.can.create_window(self.w / 1.278, self.btns_height, window=self.commentOm,
                               tags=('filter', 'typeCombobox'))

    def placePoligonOm(self):
        listname = ['полигон'] + self.poligonsList
        self.poligonVar = StringVar()
        self.poligonOm = AutocompleteCombobox(self.root,
                                              textvariable=self.poligonVar)
        self.poligonOm['style'] = 'statwin.TCombobox'
        self.poligonOm.set('полигон')
        self.poligonOm.config(width=8, height=30, font=fonts.statistic_filtres)
        self.poligonOm.set_completion_list(listname)
        self.can.create_window(self.w / 2.475, self.btns_height, window=self.poligonOm,
                               tags=('filter', 'typeCombobox'))

    def placeTypeOm(self):
        listname = ['вид груза'] + list(self.operator.trashTypesDict.keys())
        self.trashTypeStat = StringVar()
        self.trashTypeOm = AutocompleteCombobox(self.root,
                                                textvariable=self.trashTypeStat)
        self.trashTypeOm['style'] = 'statwin.TCombobox'
        self.trashTypeOm.set('вид груза')
        self.trashTypeOm.config(width=9, height=30, font=fonts.statistic_filtres)
        self.trashTypeOm.set_completion_list(listname)
        self.can.create_window(self.w / 3.435, self.btns_height, window=self.trashTypeOm,
                               tags=('filter', 'typeCombobox'))

    def placeCatOm(self, bg, deffvalue='кат. груза'):
        listname = ['кат. груза'] + list(self.operator.trashCatsDict.keys())
        self.trashCatStat = StringVar()
        self.trashCatOm = AutocompleteCombobox(self.root,
                                               textvariable=self.trashCatStat)
        self.trashCatOm['style'] = 'statwin.TCombobox'
        self.trashCatOm.set('кат. груза')
        self.trashCatOm.config(width=9, height=30, font=fonts.statistic_filtres)
        self.trashCatOm.set_completion_list(listname)
        self.can.create_window(self.w / 5.45, self.btns_height, window=self.trashCatOm,
                               tags=('filter', 'catOm'))

    def placeContragentCombo(self):
        listname = ['перевозчики'] + self.operator.contragentsList
        self.contragentVar = StringVar()
        self.contragentCombo = AutocompleteCombobox(self.root,
                                                    textvariable=self.contragentVar)
        self.contragentCombo['style'] = 'statwin.TCombobox'
        self.contragentCombo.set('перевозчики')
        self.contragentCombo.config(width=11, height=20, font=fonts.statistic_filtres)
        self.contragentCombo.set_completion_list(listname)
        self.can.create_window(self.w / 1.91, self.btns_height, window=self.contragentCombo,
                               tags=('filter', 'contragentVar'))

    def placeCarnumCombo(self):
        self.carnumCombo = AutocompleteCombobox(self.root)
        self.carnumCombo.set('гос. номер')
        self.carnumCombo.set_completion_list(self.carnums)
        self.carnumCombo['style'] = 'statwin.TCombobox'
        self.carnumCombo.config(width=11, height=20, font=fonts.statistic_filtres)
        self.can.create_window(self.w / 1.53, self.btns_height, window=self.carnumCombo, tags=('carnumCombo', 'filter'))

    def changeOmColor(self, om, var, *args):
        varname = eval(var).get()
        if om == 'catOm':
            self.trashCatOm.config(bg=self.filterColA)

    def changeCatOmColor(self, *args):
        self.changeOmColor(om='catOm', var='self.trashCatStat')

    def showStat(self):
        contragent = self.contragentCombo.get()
        trashcat = self.trashCatStat.get()
        trashtype = self.trashTypeStat.get()
        startDate = self.startCal.get_date()
        endDate = self.endCal.get_date()
        carnum = self.carnumCombo.get()
        self.can.delete('tree')
        self.drawStatTree(mode='sort', trashcat=trashcat, trashtype=trashtype,
                          contragent=contragent, startDate=startDate, endDate=endDate,
                          carnum=carnum)

    # self.can.delete('carnumCombo')
    # self.placeCarnumCombo()

    def placeDefTexts(self):
        for btn in self.stBtns:
            if btn[0] != 'Ок':
                xpos = btn[1] - 10
            else:
                xpos = btn[1]
            self.can.create_text(xpos, btn[2], text=btn[0], font=self.font, fill='white')

    def drawStatTree(self, mode='usual', trashcat='кат. груза', trashtype='вид груза',
                     contragent='перевозчики', startDate='', endDate='', carnum=''):
        self.can.delete('tree')
        if mode == 'usual':
            history = self.getHistoryData(typeMode='id', catMode='id')
            self._getCarnums(history)
            self.tar.fillTree(history)
        elif mode == 'sort':
            print('enddate', endDate)
            print('startDate', startDate)
            diff = endDate - startDate
            diffdays = diff.days
            print('diffdays', diffdays)
            # if diffdays == 0:
            #	history = self.getHistoryData()
            # else:
            endDate = datetime.combine(endDate, datetime.max.time())
            print('type of enddate', type(endDate))
            history = self.tar.getRangeHistory(startDate, endDate, typeMode='id', catMode='id')
            self._getCarnums(history)
            print('\ngot history', history)
            self.tar.fillTree(history, trashcat, trashtype, contragent, carnum)
        recs = self.tree.get_children()
        weight = 0
        for child in recs:
            listname = self.tree.item(child)["values"]
            w = listname[4]
            try:
                weight += abs(int(w))
            except:
                pass
        self.tar.sortId(self.tree, '#0', reverse=True)
        self.tree.config(height=28)
        self.can.create_window(self.w / 1.9, self.h / 1.7, window=self.tree,
                               tag='tree')
        self.placeTotalWeight(str(weight), str(len(recs)))
        self.carnumCombo.set_completion_list(self.carnums)

    def getTotalWeight(self, history):
        weight = 0
        for rec in history:
            try:
                weight += abs(rec[3])
            except:
                pass
        weight = str(weight) + ' kg.'
        return weight

    def placeTotalWeight(self, weight, amount, tag='tree'):
        # self.placeText('Количество взвешfиваний: {}'.format(amount), self.w/5.1,
        #	self.h/1.1, tag=tag, color=self.textcolor)
        weight = self.formatWeight(weight)
        text = 'ИТОГО: {} ({} взвешиваний)'.format(weight, amount)
        self.placeText(text, self.w / 2, self.h / 1.113, tag=tag,
                       color=self.textcolor, anchor='s')

    def formatWeight(self, weight):
        weight = str(weight)
        print('**WEIGHT', weight)
        if len(weight) < 4:
            ed = 'кг'
        elif len(weight) >= 4:
            weight = int(weight) / 1000
            ed = 'тонн'
        weight = str(weight) + ' ' + ed
        return weight

    def placeText(self, text, xpos, ypos, tag='maincanv', color='black',
                  font='deff', anchor='center'):
        if font == 'deff': font = self.font
        xpos = int(xpos)
        ypos = int(ypos)
        self.can.create_text(xpos, ypos, text=text, font=self.font, tag=tag,
                             fill=color, anchor=anchor)

    def placeCalendars(self):
        self.startCal = MyDateEntry(self.root, date_pattern='dd/mm/yy')
        self.startCal.config(width=7, font=fonts.statistic_calendars)
        self.endCal = MyDateEntry(self.root, date_pattern='dd/mm/yy')
        self.endCal.config(width=7, font=fonts.statistic_calendars)
        self.startCal['style'] = 'stat.TCombobox'
        self.endCal['style'] = 'stat.TCombobox'
        self.can.create_window(self.w / 3.86, self.h / 3.85, window=self.startCal,
                               tags=('statCal'))
        self.can.create_window(self.w / 2.75, self.h / 3.85, window=self.endCal,
                               tags=('statCal'))
        self.statisticInteractiveWidgets.append(self.startCal)
        self.statisticInteractiveWidgets.append(self.endCal)
        self.calendarsDrawn = True

    def drawing(self):
        Terminal.drawing(self)
        self.drawWin('maincanv', 'statisticwin')
        self.hiden_widgets += self.buttons_creation(tagname='winBtn')
        self.drawStatTree()
        if not self.calendarsDrawn:
            self.placeCalendars()
        self.show_widgets(self.statisticInteractiveWidgets)

    def openWin(self):
        Terminal.openWin(self)
        self.root.bind("<Button-1>", lambda event: self.clear_optionmenu(event))

    def page_close_operations(self):
        self.hide_widgets(self.statisticInteractiveWidgets)
        self.root.unbind("<Button-1>")

    def initBlockImg(self, name, btnsname, slice='shadow', mode='new', seconds=[], hide_widgets=[], **kwargs):
        print('CASSADOR')
        Terminal.initBlockImg(self, name, btnsname, hide_widgets=self.statisticInteractiveWidgets)


class AuthWin(Terminal):
    '''Окно авторизации'''

    def __init__(self, root, settings, operator, can):
        Terminal.__init__(self, root, settings, operator, can)
        self.name = 'AuthWin'
        self.buttons = settings.authBtns
        self.s = settings
        self.r = root
        self.currentUser = 'Андрей'
        self.font = '"Montserrat Regular" 14'
        self.users = self.operator.send_ar_sql_comm('SELECT username FROM users WHERE active=True')
        print('self.users', self.users)

    def createPasswordEntry(self):
        var = StringVar(self.r)
        bullet = '\u2022'
        pwEntry = Entry(self.r, border=0, width=24, show=bullet,
                        textvariable=var, bg=cs.auth_background_color, font=self.font, fg='#BABABA',
                        insertbackground='#BABABA', highlightthickness=0)
        return pwEntry

    def createListBox(self):
        users = [user[0] for user in self.users]
        self.contragentVar = StringVar()
        self.usersComboBox = AutocompleteCombobox(self.root,
                                                  textvariable=self.contragentVar)
        self.usersComboBox['style'] = 'authwin.TCombobox'
        self.usersComboBox.set("")
        self.usersComboBox.config(width=24, height=10, font=self.font)
        self.usersComboBox.set_completion_list(users)
        self.usersComboBox.bind('<Return>', lambda event: self.tryLogin())
        return self.usersComboBox

    def tryLogin(self):
        print('\nTrying to login')
        pw = self.loginEntry.get()
        login = self.contragentVar.get()
        command = "SELECT role,password = crypt('{}', password),id ".format(pw)
        command += "FROM users where username='{}'".format(login)
        data = self.operator.send_ar_sql_comm(command)[0]
        if len(data) > 0 and data[1] == True:
            self.send_auth_comm(login, data[2])
            self.currentUser = login
            self.drawToolbar()
            self.operator.mainPage.openWin()
            self.operator.userRole = data[0]
            print('Success login', self.currentUser, login)
            self.operator.status = 'Готов'
            self.rebinding()
            if not self.clockLaunched:
                self.start_clock()
                self.clockLaunched = True

    def rebinding(self):
        self.usersComboBox.unbind('<Return>')
        self.loginEntry.unbind('<Return>')
        self.bindArrows()

    def drawing(self):
        Terminal.drawing(self)
        self.loginEntry = self.createPasswordEntry()
        self.loginEntry.bind('<Return>', lambda event: self.tryLogin())
        self.usersChooseMenu = self.createListBox()
        self.can.create_window(self.s.w / 2.0225, self.s.h / 1.60,
                               window=self.loginEntry, tag='maincanv')
        self.can.create_window(self.s.w / 2.01, self.s.h / 1.94,
                               window=self.usersChooseMenu, tag='maincanv')
        self.drawSlices(mode=self.name)
        self.buttons_creation(tagname='winBtn')

    def openWin(self):
        Terminal.openWin(self)
        self.can.delete('toolbar')
        self.can.delete('clockel')
        self.can.itemconfigure('btn', state='hidden')

    def page_close_operations(self):
        self.can.itemconfigure('btn', state='normal')


class MainPage(Terminal):
    def __init__(self, root, settings, operator, can):
        Terminal.__init__(self, root, settings, operator, can)
        self.name = 'MainPage'
        self.buttons = settings.gateBtns + settings.manual_gate_control_btn
        self.count = 0
        self.orupState = False
        self.errorShown = False
        self.chosenTrashCat = 'deff'
        self.tar = CurrentTreeview(self.root, operator)
        self.tar.createTree()
        self.tree = self.tar.get_tree()
        self.tree.config(height=18)
        self.tree.bind("<Double-1>", self.OnDoubleClick)
        self.win_widgets.append(self.tree)
        self.btn_name = self.settings.mainLogoBtn
        self.get_carnums()

    def drawMainTree(self):
        date = self.get_timenow()
        self.tar.fillTree()
        self.can.create_window(self.w / 1.495, self.h / 2.8, window=self.tree, tag='tree')
        self.tar.sortId(self.tree, '#0', reverse=True)

    def drawing(self):
        Terminal.drawing(self)
        print('Создаем основное дерево')
        self.drawMainTree()
        self.drawWin('win', 'road', 'order', 'currentEvents', 'entry_gate_base', 'exit_gate_base')
        self.hiden_widgets += self.buttons_creation(tagname='winBtn')

    # self.draw_gate_arrows()

    def drawRegWin(self):
        self.draw_block_win(self, 'regwin')

    def destroyBlockImg(self, mode='total'):
        Terminal.destroyBlockImg(self, mode)
        self.drawMainTree()

    def updateTree(self):
        print('updating tree')
        self.tar.fillTree()
        self.tar.sortId(self.tree, '#0', reverse=True)

    def OnDoubleClick(self, event):
        '''Реакция на дабл-клик по текущему заезду'''
        item = self.tree.selection()[0]
        self.chosenStr = self.tree.item(item, "values")
        print('chosenStr -', self.chosenStr)
        self.record_id = self.tree.item(item, "text")
        print('self.record_id', self.record_id)
        self.draw_rec_close_win()

    def draw_rec_close_win(self):
        btnsname = 'closeRecBtns'
        self.initBlockImg(name='ensureCloseRec', btnsname=btnsname, seconds=('second'),
                          hide_widgets=self.win_widgets)
        self.root.bind('<Return>', lambda event: self.closeRecord(self.record_id))
        self.root.bind('<Escape>', lambda event: self.destroyBlockImg(mode="total"))

    def page_close_operations(self):
        self.can.delete('win', 'statusel')
        self.unbindArrows()

    def openWin(self):
        Terminal.openWin(self)
        self.bindArrows()
        self.operator.draw_road_anim()
        self.draw_gate_arrows()
        self.draw_weight()
        if not self.operator.main_btns_drawn:
            self.create_main_buttons()
            self.operator.main_btns_drawn = True


class ManualGateControl(Terminal):
    def __init__(self, root, settings, operator, can):
        Terminal.__init__(self, root, settings, operator, can)
        self.name = 'ManualGateControl'
        self.buttons = self.settings.auto_gate_control_btn + self.settings.manual_open_internal_gate_btn + self.settings.manual_close_internal_gate_btn + self.settings.manual_open_external_gate_btn + self.settings.manual_close_external_gate_btn
        self.btn_name = self.settings.mainLogoBtn
        self.external_gate_state = 'close'
        self.enternal_gate_state = 'close'

    def send_gate_comm(self, gate_num, operation):
        """ Отправить на AR комманду закрыть шлагбаум """
        msg = {}
        msg['gate_manual_control'] = {'gate_name': gate_num, 'operation': operation}
        response = self.send_ar_sys_comm(msg)
        print(response)

    def drawing(self):
        Terminal.drawing(self)
        self.drawWin('maincanv', 'road', 'manual_control_info_bar', 'entry_gate_base', 'exit_gate_base')
        self.hiden_widgets += self.buttons_creation(tagname='winBtn')

    def openWin(self):
        Terminal.openWin(self)
        self.operator.draw_road_anim()
        self.draw_gate_arrows()
        self.draw_weight()

    def page_close_operations(self):
        self.can.delete('win', 'statusel')