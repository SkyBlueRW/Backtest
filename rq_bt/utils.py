"""
rqalpha回测工具
"""

def _switch_code_to_rq(code: str):
    """将股票代码转换成rqalpha中可用的，XSHG 为上证，XSHE 为深证"""
    # 
    if code[:2] in {'60', '90'}:
        suffix = '.XSHG'
    elif code[:3] in {'688'}:
        suffix = '.XSHG'
    elif code[:2] in {'00', '20', '30'}:
        suffix = '.XSHE'
    else:
        raise Exception("The code is not supported: {0}.".format(code))
        
    return code.split('.')[0] + suffix


def _switch_code_to_wind(code:str):
    """
    将股票代码转化为wind的格式, SH为上证，SZ为深证
    """
    if code[0] in ('6', '9'):
        suffix = ".SH"
    elif code[0] in ('0', '2', '3'):
        suffix = ".SZ"
    else:
        raise Exception("代码为不支持的格式: {}".format(code))
    
    return code.split(".")[0] + suffix


def _switch_code_to_jy(code:str):
    """
    将股票代码转化为聚源支持的格式(000001)
    """
    return code.split(".")[0]


def convert_to_rq_code(code):
    """
    将股票代码转换为rqalpha可用格式

    Parameters
    ----------
    code: str, list
        待转换的代码
    """
    if isinstance(code, str):
        return _switch_code_to_rq(code)
    else:
        return [_switch_code_to_rq(x) for x in code]

def convert_to_wind_code(code):
    """
    将股票代码转换为wind的格式

    Parameters
    ---------
    code: str, list
        待转换的代码
    """
    if isinstance(code, str):
        return _switch_code_to_wind(code)
    else:
        return [_switch_code_to_wind(x) for x in code]

def convert_to_jy_code(code):
    """
    将股票代码转化为聚源支持的格式

    Parameters
    ----------
    code: str, list 
        待转换的代码
    """
    if isinstance(code, str):
        return _switch_code_to_jy(code)
    else:
        return [_switch_code_to_jy(x) for x in code]


