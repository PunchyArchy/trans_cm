from gravity_interface.modules import *
import os
import threading
import socket
import pickle
from time import sleep
from gravity_interface.wlistener import WListener
from gravity_interface.configs import config as s, config as ars
from traceback import format_exc
from gravity_interface.styles import fonts



class Operator():
    """ Основной оператор взaимодействия между окнами, его экземляр распределяется
	между всеми модулями и используются для их взаимной обработки """
    def __init__(self, root, settings, scale, can, deffaultScreenSize, ar_ip):
        self.root = root
        self.trashCatsDict = {}
        self.trashTypesDict = {}
        self.trash_info = {}
        self.operatorsDict = {}
        self.debtorsList = []
        self.poligon_objects_list = []
        self.contragentsList = []
        self.deffaultScreenSize = deffaultScreenSize
        self.current = 'main'
        self.settings = settings
        self.smlist = ['0', ]
        self.ar_ip = ar_ip
        self.make_ar_comm_send_socket()
        self.make_ar_sql_send_socket()
        self.make_ar_status_get_socket()
        self.get_trash_info()
        self.define_all_trash_types()
        self.terminal = Terminal(root, settings, self, can)
        self.terminal.launchingOperations()
        self.main_btns_drawn = False
        self.getTrashInfo()
        self.exitFlag = False
        print('Подключаемся к Watchman Core')
        self.road_anim_info = {self.settings.exit_gate: {'pos': 0, 'img': ...},
                               self.settings.entry_gate: {'pos': 0, 'img': ...},
                               'active': False}
        self.animation = 'off'

        self.scale = scale
        self.current = 'main'
        self.status = 'Не авторизован'
        self.wr = WListener(ip=s.wrip, port=s.wrport, ar_ip=self.ar_ip)
        self.aborted = False
        self.userRole = 'moder'

        ###################### PAGES ###################################
        self.authWin = AuthWin(root, settings, self, can)
        self.mainPage = MainPage(root, settings, self, can)
        self.statP = Statistic(root, settings, self, can)
        self.sysNot = SysNot(root, settings, self, can)
        self.manual_gate_control = ManualGateControl(root, settings, self, can)
        #########################LAUNCHING##############################
        self.authWin.openWin()

        threading.Thread(target=self.tcpClient, args=()).start()  # Для статуса
        threading.Thread(target=self.wr.scale_reciever,
                         args=()).start()  # Запуск сервера для получения данных о сервере
        threading.Thread(target=self.scaleRecieving, args=()).start()  # Запуск демона для обработки показания весов
        # Данные для рисования грузовика на весовой платформе
        self.car_was_weigh = False

    def scaleRecieving(self):
        '''Добавляет данные из сервера принятия весов в список для дальнейшей обработки'''
        while True:
            data = self.wr.wlisten_tcp()
            self.smlist.append(data)
            sleep(1)
            self.smlist = self.smlist[15:]

    def getToolBarBtns(self):
        '''Получить кнопки тул-бара'''
        toolBarBtns = self.settings.toolBarBtns
        return toolBarBtns

    def tcpClient(self):
        ''' Клиент для подключения к API AR и обработки от нее команд '''
        print('Ожидаются данные от API AR')
        while True:
            data = self.getData(self.sfs)
            print('Получены данные от API AR', data)
            if not data:
                print('Нет данных. Прерывание цикла')
                break
            else:
                threading.Thread(target=self.operateARCommand, args=(data,)).start()
        print('Обрыв связи с AR')

    def operateARCommand(self, data):
        '''Обработчик и парсер комманд, приходящих от AR. Комманды приходят в
		виде словаря, где ключ - комманда, значение - информация по команде,
		тоже в виде словаря'''
        for comm, info in data.items():
            if comm == 'updateStatus':
                self.update_status_operate(info)
            elif comm == 'carDetected' and self.ifORUPcanAppear():
                self.car_detected_operate(info)
            elif comm == 'faultDetected':
                print('FAULT DETECTED!', data)
                self.terminal.errors += [{'level1': info}]
            elif comm == 'sysInfo':
                self.operate_ar_sys_info(info)
            else:
                print('Получена неизвестная команда от AR:', comm, 'ORUP CAN APPEAR:', self.ifORUPcanAppear())

    def operate_ar_sys_info(self, info):
        for k, v in info.items():
            if k == 'data' and 'Внешний' in v and 'открывается.' in v:
                print('Внешний открывается')
                self.terminal.open_entry_gate_operation_start()
            elif k == 'data' and 'Внешний' in v and 'закрывается.' in v:
                print('Внешний закрывается')
                self.terminal.close_entry_gate_operation_start()
            elif k == 'data' and 'Внутренний' in v and 'открывается.' in v:
                print('Внутренний открывается')
                self.terminal.open_exit_gate_operation_start()
            elif k == 'data' and 'Внутренний' in v and 'закрывается.' in v:
                print('Внутренний закрывается')
                self.terminal.close_exit_gate_operation_start()

    def update_status_operate(self, info):
        # Если получена команда на обновление статуса заезда
        self.status = 'Занят'
        self.road_anim_info['active'] = True
        for k, v in info.items():
            self.road_anim_info[k] = v
        if (info['protocol'].strip() == 'Машина заезжает.' or info['protocol'].strip() == 'Машина выезжает.'):
            self.updateMainTree()
        self.drawStatus()
        if info['notes'].strip() == 'Запись обновлена':
            self.updateMainTree()
        if (self.current == 'MainPage' or self.current == 'ManualGateControl') and not self.currentPage.blockImgDrawn:
            self.drawCarMoving()
        if (info['status'].strip() == 'Протокол завершен' or info['status'].strip() == 'Время истекло!'):
            self.operateStatusEnd()

    def draw_road_anim(self):
        print('drawing road anim')
        if self.road_anim_info['active']:
            print('active')
            self.drawCarMoving()
            self.drawStatus()

    def car_detected_operate(self, info):
        # Если получена команда на открытие ОРУП
        self.currentPage.orupState = True
        course = info['course']
        contragent = self.getInfoFromDict(info, 'lastContragent')
        contragent = self.get_db_info_comm('clients', 'short_name', "id='{}'".format(contragent),
                                           failure_message='Укажите перевозчика')
        trashType = self.getInfoFromDict(info, 'lastTrashType')
        trashType = self.get_db_info_comm('trash_types', 'name', "id='{}'".format(trashType),
                                          failure_message='Укажите вид груза')
        trashCat = self.getInfoFromDict(info, 'lastTrashCat')
        trashCat = self.get_db_info_comm('trash_cats', 'cat_name', "id='{}'".format(trashCat),
                                         failure_message='Укажите категорию груза')
        # Понять, есть ли у этой машины уже инициированный заезд
        have_brutto = info['have_brutto']
        self.currentPage.car_protocol = info['id_type']
        if have_brutto:
            # Если да, вызвать выездной ОРУП
            self.currentPage.orupActExit(carnum=info['carnum'], call_method="auto", course=course)
        else:
            # Если же нет (надо инициировать заезд), вызвать въездной ОРУП
            self.currentPage.orupAct(carnum=info['carnum'], contragent=contragent, trashType=trashType,
                                     trashCat=trashCat, call_method="auto", car_protocol=info['id_type'], course=course)

    def fetch_if_record_init(self, carnum):
        command = "select * from {} where car_number='{}' and inside='yes'".format(s.book, carnum)
        response = self.send_ar_sql_comm(command)
        if len(response) > 0:
            return True

    def fetch_car_protocol(self, carnum):
        command = "select id_type from {} where car_number='{}'".format(s.auto, carnum)
        response = self.send_ar_sql_comm(command)
        try:
            return response[0][0]
        except IndexError:
            return 'tails'

    def ifORUPcanAppear(self):
        # Возвращает TRUE, если можно нарисовать окно ОРУП
        if (self.current != 'AuthWin' and self.status == 'Готов' and not self.currentPage.blockImgDrawn
                and not self.currentPage.orupState):
            print("CAN show for: \ncurrent= ", self.current,
                  '\nstatus= ', self.status,
                  '\nBlockImgDrawn = ', self.currentPage.blockImgDrawn,
                  '\nOrupState = ', self.currentPage.orupState)
            return True
        else:
            print("Can not show for: \ncurrent= ", self.current,
                  '\nstatus= ', self.status,
                  '\nBlockImgDrawn = ', self.currentPage.blockImgDrawn,
                  '\nOrupState = ', self.currentPage.orupState)
            return False

    def getInfoFromDict(self, info, target):
        # Получить зачение словаря с информацией о команде по ключу
        goal = info[target]
        if goal == 'none':
            goal = 'Неизвестно'
        return goal

    def get_db_info_comm(self, table, name, id, failure_message):
        command = 'SELECT {} FROM {} WHERE {}'.format(name, table, id)
        # Получить данные из табылицы
        try:
            data = self.send_ar_sql_comm(command)
            data = data[0][0]
        except IndexError:
            data = failure_message
        return data

    def getArStatus(self):
        # Получить и вернуть статус AR
        self.send_ar_comm({'status': 'none'}, self.ais, mode='pickle')
        print('\n\t\tПолучаем статус AR')
        status = self.get_ar_response_pickle(self.ais)
        print('\tСтатус AR получен:', status)
        print('status', status)
        if status == 'Занят':
            print('\t\tЗанят статус')
            return False
        elif status == 'Готов' or status == 'waitingCM':
            print('\t\tГотов статус')
            return True
        else:
            print('\tНе удалось узнать статус AR! (', status, ')')

    def operateStatusEnd(self):
        '''Обработчик завершения заезда авто'''
        sleep(2)
        self.currentPage.can.delete('mtext', 'car_icon')
        self.status = 'Готов'
        self.road_anim_info['active'] = False
        self.car_was_weigh = False

    def updateMainTree(self, mode='usual'):
        '''Обновить таблицу текущих записей'''
        if self.current == 'MainPage' and self.mainPage.orupState == False:
            self.mainPage.updateTree()
            if mode == 'create':
                self.mainPage.drawMainTree()

    def getData(self, sock):
        '''Получает сериализированные данные и возвращает их в исходную форму'''
        data = sock.recv(4096)
        if data: data = pickle.loads(data)
        return data

    def getOrupMode(self, course, id_type):
        '''Определить атрибут, передаваемый ОРУПу, согласно курсу движения авто'''
        mode = '_'.join((id_type, course))
        return mode

    def drawStatus(self):
        '''Рисует статус заезда текстом при заезде-выезде на главном меню'''
        self.mainPage.can.delete('mtext')
        if self.current == 'MainPage' and self.mainPage.orupState == False:
            num = 'Гос. номер авто:\n' + self.road_anim_info['carnum']
            status = 'Статус:\n' + self.road_anim_info['status']
            notes = 'Примечания:\n' + self.road_anim_info['notes']
            self.mainPage.can.create_text(self.terminal.w / 9.15, self.terminal.h / 5.12,
                                          text=num, font=fonts.status_text, tag='mtext', fill='#BABABA', anchor=NW)
            self.mainPage.can.create_text(self.terminal.w / 9.15, self.terminal.h / 3.84,
                                          text=status, font=fonts.status_text, tag='mtext', fill='#BABABA', anchor=NW)
            self.mainPage.can.create_text(self.terminal.w / 9.15, self.terminal.h / 3.12,
                                          text=notes, font=fonts.status_text, tag='mtext', fill='#BABABA', anchor=NW)

    def drawCarMoving(self):
        '''Рисует грузовик на грузовой платформе при инициировании проокола
		заезда или выезда на главном меню'''
        self.car_protocol = self.road_anim_info['protocol']
        self.car_direction = self.road_anim_info['course']

        car_direction_txt = self.road_anim_info['face']
        cur_pos_txt = self.road_anim_info['pos']

        cur_pos_cm = self.settings.car_poses[cur_pos_txt]
        obj = self.settings.car_face_info[car_direction_txt]
        obj = self.terminal.getAttrByName(obj)
        self.drawCarIcon(obj, cur_pos_cm)

    def drawCarIcon(self, obj, poses):
        self.mainPage.can.delete('car_icon')
        self.mainPage.can.create_image(poses, image=obj[3], anchor=NW, tag='car_icon')

    def make_ar_comm_send_socket(self):
        self.ais = socket.socket()
        self.try_to_connect_ar_loop(self.ais, self.ar_ip, ars.cmUseInterfacePort, 'сокет отправки sql команд')

    def make_ar_sql_send_socket(self):
        self.sss = socket.socket()
        self.try_to_connect_ar_loop(self.sss, self.ar_ip, ars.sql_comm_send_port, 'сокет отправки sql команд')

    def make_ar_status_get_socket(self):
        self.sfs = socket.socket()
        self.try_to_connect_ar_loop(self.sfs, self.ar_ip, ars.statusSocketPort, 'сокет статусов')

    def try_to_connect_ar_loop(self, socket, ip, port, socket_name, sleeptime=3):
        print('Попытка подключения к {}.'.format(socket_name))
        try:
            socket.connect((ip, port))
        except:
            print('Подключение к {} не удалось.'.format(socket_name))
            sleep(sleeptime)

    def closeApp(self):
        '''Функция выполняющая завершающие операции, при закрытии программы'''
        self.terminal.send_stop_comm()
       # self.ais.close()
        os._exit(0)

    def getTrashInfo(self):
        ''' [Актуально] Сохранить данные из БД в объекты типа словари'''
        self.getTrashCats()
        self.getTrashTypes()
        self.getDebtorsList()
        self.getOperatorsList()
        self.get_pol_objects_list()

    def get_pol_objects_list(self):
        command = "SELECT name FROM duo_pol_owners"
        objects = self.send_ar_sql_comm(command)
        self.poligon_objects_list = [object[0] for object in objects]

    def getTrashCats(self):
        command = 'select cat_name, id from {}'.format(s.trash_cats_table)
        trash_cats = self.send_ar_sql_comm(command)
        for trash_cat in trash_cats:
            self.trashCatsDict[trash_cat[0]] = trash_cat[1]

    def getOperatorsList(self):
        command = 'select username, id from {}'.format(s.users_table)
        users = self.send_ar_sql_comm(command)
        for user in users:
            self.operatorsDict[user[0]] = user[1]

    def getTrashTypes(self):
        command = 'select name, id from {}'.format(s.trash_types_table)
        trash_types = self.send_ar_sql_comm(command)
        for trash_type in trash_types:
            self.trashTypesDict[trash_type[0]] = trash_type[1]

    def getDebtorsList(self):
        '''Извлекает из БД список клиентов, парсит их, сохраняет всех клиентов в self.contragents[], а
		должников - в self.debtorsList{}'''
        command = 'select * from {} WHERE active=True'.format(s.clients_table)
        clients = self.send_ar_sql_comm(command)
        for client in clients:
            self.contragentsList.append(client[2])
            try:
                if int(client[5]) == 0:
                    reason = client[4]
                    name = client[2]
                    time = client[7]
                    debtor = {'name': name, 'reason': reason, 'time': time}
                    self.debtorsList.append(debtor)
            except:
                pass

    def get_trash_info(self):
        # Получает из wdb информацию
        #command = "SELECT c.cat_name, c.wserver_id, t.name, t.category FROM {} AS t INNER JOIN {} AS c ON t.category=c.id " \
        #          "WHERE t.active=True".format(s.trash_types_table, s.trash_cats_table)
        trash_types_info = self.send_ar_sql_comm(
            "SELECT name, category from {}".format(s.trash_types_table)
        )
        trash_cats_info = self.send_ar_sql_comm(
            "SELECT cat_name, wserver_id FROM {}".format(s.trash_cats_table)
        )
        for trash_cat in trash_cats_info:
            for trash_type in trash_types_info:
                if trash_type[1] == trash_cat[1]:
                    try:
                        self.trash_info[trash_cat[0]].append(trash_type[0])
                    except KeyError:
                        self.trash_info[trash_cat[0]] = [trash_type[0]]

    def open_new_page(self, page):
        try:
            self.currentPage.page_close_operations()
        except:
            pass
        self.current = page.name
        self.currentPage = page

    def define_all_trash_types(self):
        """ Сохраняет все виды груза в переменную all_trash types и возвращает его """
        self.all_trash_types = []
        for k, v in self.trash_info.items():
            self.all_trash_types += v
        return self.all_trash_types

    def send_ar_comm(self, comm, sock, mode='bytes'):
        print('\nОтправка сообщения', comm)
        if mode == 'pickle':
            comm = pickle.dumps(comm)
        else:
            comm = bytes(comm, encoding='utf-8')
        sock.send(comm)

    def send_ar_sql_comm(self, comm):
        print('Отправка комманды', comm, '. Блокировка сокета')
        self.send_ar_comm(comm, self.sss)
        response = self.get_ar_response_pickle(self.sss)
        return response

    def get_ar_response_pickle(self, socket):
        response = self.unpickle_data(socket)
        #print('Получены данные от SQL AR', response)
        return response

    def unpickle_data(self, sock, data_size=1024):
        """Собирает большие файлы в цикле"""
        data = []
        while True:
            print('\tЖдем данные')
            packet = sock.recv(data_size)
            if not packet:
                break
            data.append(packet)
            try:
                data_arr = pickle.loads(b"".join(data))
                return data_arr
            except pickle.UnpicklingError:
                pass
            except:
                print(format_exc())
