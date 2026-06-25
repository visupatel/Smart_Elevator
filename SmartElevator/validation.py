
# type conversion, if invalid type then raise ValueError
def isValid_type(type,value,type_field,value_field):      
    try:
        return type(value)
    except:
        raise ValueError(f"'{value_field}' must be in {type_field}")

