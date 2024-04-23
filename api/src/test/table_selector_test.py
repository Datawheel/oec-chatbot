
from table_selection.table_selector import *

def table_test():
    TABLE_PATH = '/home/framos/datawheel/oec-chatbot/api/data/schema.json'
    tm = TableManager(TABLE_PATH)
    tb = request_tables_to_lm_from_db("What are the top five exporting countries for cars in terms of value?",
                                tm)

    print(tb.get_drilldown_members())

    assert tb == None