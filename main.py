#!/usr/bin/env python
import string
import urllib
import json
import base64
import re
import db

g_msmaster_db   = None
g_video_list    = []

class video_t():
    def __init__(self, hash_id, block_type, block_title, media_id, media_title, serial_id, language):
        self.m_hash_id      = hash_id
        self.m_block_type   = block_type
        self.m_block_title  = block_title
        self.m_media_id     = media_id
        self.m_media_title  = media_title
        self.m_serial_id    = serial_id
        self.m_language     = language
        

def hill2_decrypt(decypt_key, plain_text):
    plain_len = len(plain_text)
    cal_len = plain_len
    cipher_text = [0] * plain_len
    result = ''
    
    x1 = 0
    x2 = 0
    y1 = 0
    y2 = 0
    plain_index = 0
    
    if(plain_len%2 == 1):
        cal_len = plain_len - 1
    for plain_index in range(0, cal_len, 2):
        x1 = ord(plain_text[plain_index+0])
        x2 = ord(plain_text[plain_index+1])
        y1 = x1 * decypt_key[0][0] + x2 * decypt_key[1][0]
        y2 = x1 * decypt_key[0][1] + x2 * decypt_key[1][1]
        #print 'y1: %d, y2: %d' % (y1%256, y2%256)
        cipher_text[plain_index+0] = y1%256
        cipher_text[plain_index+1] = y2%256
        
    if(plain_len%2 == 1):
        cipher_text[plain_len-1] = ord(plain_text[plain_len-1])
    
    for one in cipher_text:
        result += chr(one)
    
    return result
    
            
def client_get_url(url):
    fp = urllib.urlopen(url)
    content = fp.read()    
    fp.close()
    #print 'content: \n%s\n'  %(content)
    
    result = json.loads(content)
    if 'encrypt' not in result:
        return ''
        
    encrypt = result['encrypt']
    token   = result['token']
    data    = result['data']    
    #print 'encrypt: %s' % (encrypt)
    #print 'token: %s' % (token)
    #print 'data: %s' % (data)
    
    token2  = urllib.unquote(token)
    data2   = urllib.unquote(data)   
    #print 'token2: %s' % (token2)
    #print 'data2: %s' % (data2)   
    
    key_data = [[0, 0], [0, 59]]
    str_num1 = data2[0:2]
    str_num2 = data2[2:4]
    str_num3 = data2[4:6]
    str_num4 = data2[6:8]
    key_data[0][0] = string.atoi(str_num1, 16)
    key_data[0][1] = string.atoi(str_num2, 16)
    key_data[1][0] = string.atoi(str_num3, 16)
    key_data[1][1] = string.atoi(str_num4, 16)
    
    token3  = base64.decodestring(token2)
    data3   = base64.decodestring(data2[8:])    
    
    key_token = [[145, 245], [166, 59]]
    token4  = hill2_decrypt(key_token, token3)
    #print 'token4: %s\n' % (token4)
        
    data4   = hill2_decrypt(key_data, data3)    
    #print 'data4: %s\n' % (data4) 

    return data4

        
def client_show_hash(url, block_type, block_title, media_id, media_title, serial_id, language):
    if(len(url) == 0):
        return False
    
    parts = url.split('?')
    simple_url = parts[0]
    parts = simple_url.split('/')
    hash_json = parts[6]
    parts = hash_json.split('.')
    only_hash = parts[0]
    #print only_hash
    '''
    pattern = re.compile(r'\/S+\.json')
    match = pattern.match(url)
    if(match):
        group = match.group()
        print group
    '''    
    
    sql = 'select hash, temperature0, online_time, PayOrFree from mobile_task_temperature where hash="%s"' % (only_hash)
    #print sql
    global g_msmaster_db
    g_msmaster_db.execute(sql)
    task1 = {}
    query_set_1 = g_msmaster_db.cur.fetchall()
    for row1 in query_set_1:         
        r1_index = 0
        for r1 in row1:
            if(r1_index == 0):
                task1['hash'] = r1
            elif(r1_index == 1):
                task1['temperature0'] = r1
            elif(r1_index == 2):
                task1['online_time'] = r1
            elif(r1_index == 3):
                task1['PayOrFree'] = r1
            r1_index += 1
    
    one_video = video_t(only_hash, block_type, block_title, media_id, media_title, serial_id, language)
    if 'hash' not in task1:
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (only_hash, block_type, block_title, media_id, str(serial_id), str(language), media_title, 'NotFound')
    else:
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%e\t%s\t%s' % (only_hash, block_type, block_title, media_id, str(serial_id), str(language), media_title, \
                                                         task1['temperature0'], str(task1['online_time']), str(task1['PayOrFree']))
    
    g_video_list.append(one_video)
    

def client_show_playlist(data, block_type, block_title, media_id, media_title, serial_id = None, language = None):
    if 'cdn_tv' in data:        
        #print 'cdn_tv: %s' % (data['cdn_tv'])        
        client_show_hash(data['cdn_tv'], block_type, block_title, media_id, media_title, serial_id, language)
    if 'cdn_dvd' in data:
        #print 'cdn_dvd: %s' % (data['cdn_dvd'])
        client_show_hash(data['cdn_dvd'], block_type, block_title, media_id, media_title, serial_id, language)
    if 'cdn_hd' in data:
        #print 'cdn_hd: %s' % (data['cdn_hd'])
        client_show_hash(data['cdn_hd'], block_type, block_title, media_id, media_title, serial_id, language)
    if 'cdn_super_dvd' in data:
        #print 'cdn_super_dvd: %s' % (data['cdn_super_dvd'])
        client_show_hash(data['cdn_super_dvd'], block_type, block_title, media_id, media_title, serial_id, language)
        
        
        
def client_show_other(block_type, block_title, media_id, media_title):
    url = "http://jsonfe.funshion.com/v3/video/get_playurl?cli=aphone&ver=2.1.1.2&sid=1029&videoid=%s&ta=2" % (media_id)
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    result = json.loads(content)  
    if 'data' not in result:
        return False
      
    data = result['data']
    client_show_playlist(data, block_type, block_title, media_id, media_title)
    


def client_show_tv_episode(serial_id, language, block_type, block_title, media_id, media_title):
    url = "http://jsonfe.funshion.com/v3/media/get_serial_play?cli=aphone&ver=2.1.1.2&sid=1029&serialid=%s&langtype=%s&ta=2" % (serial_id, language)
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    if(len(content) == 0):
        return False
    
    result = json.loads(content)
    if 'list' not in result:
        return False
    if serial_id not in result['list']:
        return False
    
    data = result['list'][serial_id]
    client_show_playlist(data, block_type, block_title, media_id, media_title, serial_id, language)
    

def client_show_tv(block_type, block_title, media_id, media_title):
    url = "http://jsonfe.funshion.com/v3/media/get_serials?cli=aphone&ver=2.1.1.2&sid=1029&mediaid=%s&page=1&pagesize=500&langtype=all_type&plots=0&ta=2" % (media_id)
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    result = json.loads(content)
    if 'list' not in result:
        return False
    
    serial_list = result['list']
    for one_serial in serial_list:
        #print 'serail_id: %s, %s' % (one_serial['serialid'], one_serial['title'])
        language_list = one_serial['languages']
        for one_language in language_list:
            #print 'language: %s, cid: %s' % (one_language['language'], one_language['cid'])
            client_show_tv_episode(one_serial['serialid'], one_language['language'], block_type, block_title, media_id, media_title)
     

    
def client_show_item(block_type, block_title, media_id, media_title):
    if(block_type == 'tv'):
        client_show_tv(block_type, block_title, media_id, media_title)
    elif(block_type == 'movie'):
        client_show_tv(block_type, block_title, media_id, media_title)
    elif(block_type == 'cartoon'):
        client_show_tv(block_type, block_title, media_id, media_title)
    elif(block_type == 'variety'):
        client_show_tv(block_type, block_title, media_id, media_title)
    else:        
        client_show_other(block_type, block_title, media_id, media_title)
        
    return True
    
            
def client_show_index(content):
    result = json.loads(content)
    block_list = result['block_list']
    for one_block in block_list:
        #print 'block: %s, %s, %s' % (one_block['channel_title'], one_block['type'], one_block['title'])
        program_list = one_block['list']
        for one_item in program_list:
            #print '\t obj_id: %s, title: %s' % (one_item['obj_id'], one_item['title'])
            client_show_item(one_block['type'], one_block['title'], one_item['obj_id'], one_item['title'])
            
    return True

        
def main():
    global g_msmaster_db
    g_msmaster_db = db.DB_MYSQL()
    g_msmaster_db.connect(db.DB_CONFIG_MSMASTER.host, db.DB_CONFIG_MSMASTER.port, db.DB_CONFIG_MSMASTER.user, db.DB_CONFIG_MSMASTER.password, db.DB_CONFIG_MSMASTER.db)
    
    #url = "http://jsonfe.funshion.com/v3/media/get_serials?cli=aphone&ver=2.1.1.2&sid=1029&mediaid=104541&page=1&pagesize=500&langtype=all_type&plots=0&ta=2"
    #print 'url: \n%s\n'  %(url)
    #content = client_get_url(url)
        
    url = "http://jsonfe.funshion.com/v3/operation/get_index?cli=aphone&ver=2.1.1.2&sid=1029&ta=2"
    print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    client_show_index(content)
    
    #url_homepage = "http://jsonfe.funshion.com/v3/operation/get_homepage?cli=aphone&ver=2.1.1.2&sid=1029&deviceid=25B17C690FBC0DBC0BB80EBC684C84EE88FB79BD1DFA8C02A5A89EA129FDC656&ta=2"
    #print 'url: \n%s\n'  %(url_homepage)
    #homepage_content = client_get_url(url_homepage)
    
    g_msmaster_db.close()
    
    
if __name__ == "__main__":
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    
    main()