from gravity_interface.configs import config as s
from datetime import datetime
'''Модуль, содержащий все команды взаимодействия Watchman с СУБД'''

#Выводим форматирование в инициализацию, что бы не перегружать лишний раз
#функцию getOrupAutoUpdComm
autoUpdOrupjoining = "inner join {} as tt on r.trash_type = tt.id ".format(
    s.trash_types_table
)
autoUpdOrupjoining += 'inner join {} as tc on r.trash_cat = tc.id '.format(
    s.trash_cats_table
)
autoUpdOrupjoining += 'inner join {} as c on r.carrier=c.id'.format(
    s.clients_table
)
#ОРУП НА ВЪЕЗДЕ

#Команда на автообновление опций во въездном ОРУП
def getOrupAutoUpdComm(carnum):
    '''Возвращает команду для получения данных с последнего заезда для
    подстановки в опции'''
    tablenames = '{}'.format(s.book)
    #ident = "car_number = '{}'".format(carnum)
    autoUpdOrupComm = "select c.short_name, tt.name, tc.cat_name from last_events le " \
                      "INNER JOIN auto a ON (le.car_id=a.id) INNER JOIN clients c ON (le.carrier = c.id) " \
                      "INNER JOIN trash_types tt ON (le.trash_type = tt.id) " \
                      "INNER JOIN trash_cats tc ON (le.trash_cat = tc.id) where car_number='{}'".format(carnum)
    return autoUpdOrupComm

def get_days_with_disputs(month):
    '''Возвращает команду для получения данных о диспутах за месяц'''
    command = "select date, records_id, result "
    command += "from {} ".format(s.disputs_table)
    command += "where extract(month from date) = {}".format(month)
    print(command)
    return command

def getAlertsComm(rec_id):
    '''Обращается в таблицу disputs, извлекает диспуты по records_id и возвращает алерты'''
    command = "SELECT alerts "
    command += "FROM {} ".format(s.disputs_table)
    command += "where {}.records_id={}".format(s.disputs_table, rec_id)
    return command

def getResultSet(rec_id, result):
    '''Возвращает команду для сеттинга результата по диспуту'''
    timenow = datetime.now()
    command = "UPDATE {} ".format(s.disputs_table)
    command += "SET result={}, result_date='{}' ".format(result, timenow)
    command += "where records_id={}".format(rec_id)
    return command

def getDisputsDay(day):
    '''Возвращает команду для получения диспутов, удовлетворяющих идентификатору (ident). Как правило, это диспуты
    за какой либо день'''
    print('DAY -', day, 'type-', type(day))
    st_date = '{} 01:00:00'.format(day)
    end_date = '{} 23:00:00'.format(day)
    command = "SELECT {}.records_id, {}.alerts, {}.result, ".format(s.disputs_table, s.disputs_table, s.disputs_table)
    command += "{}.short_name, {}.cargo, {}.car_number, ".format(s.clients_table, s.book, s.book)
    command += "{}.time_in, {}.time_out, {}.brutto, {}.tara ".format(s.book, s.book, s.book, s.book)
    command += "FROM {} INNER JOIN {} ON ".format(s.disputs_table, s.book)
    command += "({}.records_id = {}.id) ".format(s.disputs_table, s.book)
    command += "INNER JOIN {} ".format(s.clients_table)
    command += "ON ({}.carrier={}.id) ".format(s.book, s.clients_table)
    command += "WHERE time_out > '{}' and time_out < '{}'".format(st_date, end_date)
    print('command', command)
    return command

def getDisputsDate(date):
    '''Возвращает записи из records, у которых есть алерты в disputs'''
    pass
"""
def getAlertsComm(rec_id):
    '''Обращается в таблицу disputs, извлекает диспуты по records.id и возвращает алерты'''
    command = "SELECT {}.alerts ".format(s.disputs_table)
    command += "FROM {} INNER JOIN ".format(s.book)
    command += "{} ON ({}.id = {}.records_id) ".format(s.disputs_table, s.book,s.disputs_table)
    command += "where {}.id={}".format(s.disputs_table, rec_id)
    return command
"""

