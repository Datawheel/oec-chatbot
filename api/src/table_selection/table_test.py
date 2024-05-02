from table import TableManager



manager = TableManager('/home/framos/datawheel/oec-chatbot/api/data/schema.json')
table = manager.get_table("trade_i_baci_a_96")

print(table.dimensions)
dim = 'HS Product'
print(table.get_drilldown_members(dim))
print(table.get_dimensions_description(dim))
print(table.get_dimension_levels(dim))
print(table.get_dimension_hierarchies(dim))
print(table.get_drilldown_members(dim))