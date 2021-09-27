import os

rootdir = os.getcwd()
CUR_DIR = os.path

#ДБ PostgreSQL
auto = 'auto'
book = 'records'
special_protocols = 'special_protocols'
clients_table = 'clients'
trash_types_table = 'trash_types'
trash_cats_table = 'trash_cats'
day_disputs_table = 'day_disputs'
disputs_table = 'disputs'
users_table = 'users'

#Настройки сокета для получения комманд от Watchman-CM
ar_ip = '192.168.100.118'
cmUseInterfacePort = 2292

#Настройка сокета для передачи статуса  Watchman-CM
statusSocketPort = 2291

# Настройка сокета для передачи комманд SQL на Watchman-AR
sql_comm_send_port = 2293

# Сервер рассылки показаний с весов
scale_splitter_port = 2297


'''Пакет конфигурации для Watchman-MC'''

wrip = 'localhost'
wrport = 2296


#ОРУП
allowed_carnum_symbols = ['А', 'В', 'Е', 'К', 'М', 'Н', 'О', 'Р', 'С', 'Т', 'У',
    'Х', 'а','в','е','к','м','н','о','р','с','т','у','х']

gates_info = {'entry': {'name': 'entry', 'num': 1, 'open_anim_command': 'self.open_entry_gate_operation_start()',
                        'close_anim_command': 'self.close_entry_gate_operation_start()'},
              'exit': {'name': 'exit', 'num': 2, 'open_anim_command': 'self.open_exit_gate_operation_start()',
                        'close_anim_command': 'self.close_exit_gate_operation_start()'},
              }