import hashlib


def singleton(klass):
    """
    singleton function
    :param klass: instance of class
    :return: object is create or object is exits
    """
    if not klass._instance:
        klass._instance = klass()
    return klass._instance


def convert_utf8(data):
    if isinstance(data, dict):
        return {convert_utf8(key): convert_utf8(value) for key, value in data.iteritems()}
    elif isinstance(data, list):
        return [convert_utf8(element) for element in data]
    elif isinstance(data, unicode):
        return data.encode('utf-8')
    else:
        return data


def convert_string(data):
    if isinstance(data, dict):
        return {convert_string(key): convert_string(value) for key, value in data.iteritems()}
    elif isinstance(data, list):
        return [convert_string(element) for element in data]
    elif isinstance(data, unicode):
        return str(data)
    else:
        return data


# from mechanize import Browser, Request, urlopen
#
# browser = Browser()
# response = browser.open('http://testphp.vulnweb.com/')
# print response.code
#
# req = Request('http://testphp.vulnweb.com/')
# response_= urlopen(req, timeout=2)
# print response.code

def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()
