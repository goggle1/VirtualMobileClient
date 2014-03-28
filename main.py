#!/usr/bin/env python
import string
import urllib
import json
import base64
import re
import db

g_msmaster_db   = None
g_video_list    = []
g_video_dict    = {}

g_media_dict    = {}

class video_t():
    def __init__(self, hash_id, section_type, section_title, media_id, media_title, serial_id, language):
        self.m_hash_id      = hash_id
        self.m_section_type = section_type
        self.m_section_title= section_title
        self.m_media_id     = media_id
        self.m_media_title  = media_title
        self.m_serial_id    = serial_id
        self.m_language     = language


class section_t():
    def __init__(self, v_type, v_title):
        self.m_type       = v_type
        self.m_title      = v_title

        
class block_t(section_t):
    def __init__(self, block_type, block_title, channel_title):
        section_t.__init__(self, block_type, block_title)
        self.m_channel_title    = channel_title
        self.m_movie_list       = None
        
                

class channel_t(section_t):
    def __init__(self, channel_type, channel_title):
        section_t.__init__(self, channel_type, channel_title)
        self.m_list_recommended = None
        self.m_list_ordinary    = None
        self.m_list_special     = None
        self.m_list_rank        = None
        
        
class movie_t():
    def __init__(self, media_id, media_name):
        self.m_media_id     = media_id
        self.m_media_name   = media_name
        self.m_serial_list  = None

        
class serial_t():
    def __init__(self, serial_id, serial_name):
        self.m_serial_id    = serial_id
        self.m_serial_name  = serial_name
        

class language_t():
    def __init__(self, language_name, languange_cid):
        self.m_language_name    = language_name
        self.m_languange_cid    = languange_cid
                
        
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
    content = ''
    try:
        fp = urllib.urlopen(url)
        content = fp.read()    
        fp.close()
        #print 'content: \n%s\n'  %(content)
    except:
        print 'client_get_url meet error!'
        content = ''
    
    return content
    
                
def client_decode_content(content):
    result = None
    try:
        result = json.loads(content)
    except:
        return ''
    
    if(result == None):
        return ''
    
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

        
def client_show_hash(url, one_block, one_movie, one_serial, one_language):
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
    
    serial_id = ''
    if(one_serial!=None):
        serial_id = one_serial.m_serial_id
    language_name = ''
    if(one_language!=None):
        language_name = one_language.m_language_name
    one_video = video_t(only_hash, one_block.m_type, one_block.m_title, one_movie.m_media_id, one_movie.m_media_name, serial_id, language_name) 
       
    if 'hash' not in task1:
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (only_hash, one_block.m_type, one_block.m_title, one_movie.m_media_id, serial_id, language_name, one_movie.m_media_name, 'NotFound')
    else:
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%e\t%s\t%s' % (only_hash, one_block.m_type, one_block.m_title, one_movie.m_media_id, str(serial_id), language_name, one_movie.m_media_name, \
                                                         task1['temperature0'], str(task1['online_time']), str(task1['PayOrFree']))    
    global g_video_list
    global g_video_dict
    g_video_list.append(one_video)
    g_video_dict[only_hash] = one_video
    

def client_show_playlist(data, one_block, one_movie, one_serial = None, one_language = None):
    if 'cdn_tv' in data:        
        #print 'cdn_tv: %s' % (data['cdn_tv'])        
        client_show_hash(data['cdn_tv'], one_block, one_movie, one_serial, one_language)
    if 'cdn_dvd' in data:
        #print 'cdn_dvd: %s' % (data['cdn_dvd'])
        client_show_hash(data['cdn_dvd'], one_block, one_movie, one_serial, one_language)
    if 'cdn_hd' in data:
        #print 'cdn_hd: %s' % (data['cdn_hd'])
        client_show_hash(data['cdn_hd'], one_block, one_movie, one_serial, one_language)
    if 'cdn_super_dvd' in data:
        #print 'cdn_super_dvd: %s' % (data['cdn_super_dvd'])
        client_show_hash(data['cdn_super_dvd'], one_block, one_movie, one_serial, one_language)
        
        
        
def client_show_single(one_block, one_movie):
    url = "http://jsonfe.funshion.com/v3/video/get_playurl?cli=aphone&ver=2.1.1.2&sid=1029&videoid=%s&ta=2" % (one_movie.m_media_id)
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    data    = client_decode_content(content)
    result = json.loads(data)  
    if 'data' not in result:
        return False
      
    data = result['data']
    client_show_playlist(data, one_block, one_movie)
    


def client_show_season_episode(one_block, one_movie, one_serial, one_language):
    url = "http://jsonfe.funshion.com/v3/media/get_serial_play?cli=aphone&ver=2.1.1.2&sid=1029&serialid=%s&langtype=%s&ta=2" % (one_serial.m_serial_id, one_language.m_language_name)
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    #print 'content:\n %s' % (content)  
    if(len(content) == 0):
        return False  
    data    = client_decode_content(content)
    if(len(data) == 0):
        return False
    result = json.loads(data) 
    if 'list' not in result:
        return False
    if one_serial.m_serial_id not in result['list']:
        return False    
    play_list = result['list'][one_serial.m_serial_id]
    client_show_playlist(play_list, one_block, one_movie, one_serial, one_language)
    return True
    

def client_show_season(one_block, one_movie):
    serial_list = []
    url = "http://jsonfe.funshion.com/v3/media/get_serials?cli=aphone&ver=2.1.1.2&sid=1029&mediaid=%s&page=1&pagesize=500&langtype=all_type&plots=0&ta=2" % (one_movie.m_media_id)
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    if(len(content) == 0):
        return False
    
    data    = client_decode_content(content)
    
    result = None
    try:
        result = json.loads(data)
    except:
        return False
        
    if(result == None):
        return False
     
    if 'list' not in result:
        return False
        
    serial_info_list = result['list']
    for serial_info in serial_info_list:
        one_serial = serial_t(serial_info['serialid'], serial_info['title'])
        serial_list.append(one_serial)
        language_list = []
        language_info_list = serial_info['languages']
        for language_info in language_info_list:
            one_language = language_t(language_info['language'], language_info['cid'])   
            language_list.append(one_language)         
            #print 'language: %s, cid: %s' % (language_info['language'], language_info['cid'])
            client_show_season_episode(one_block, one_movie, one_serial, one_language)
        one_serial.m_language_list = language_list
    one_movie.m_serial_list = serial_list
    return True 

    
def client_show_one_movie(one_block, one_movie):
    if(one_block.m_type == 'tv'):
        client_show_season(one_block, one_movie)
    elif(one_block.m_type == 'movie'):
        client_show_season(one_block, one_movie)
    elif(one_block.m_type == 'cartoon'):
        client_show_season(one_block, one_movie)
    elif(one_block.m_type == 'variety'):
        client_show_season(one_block, one_movie)
    else:        
        client_show_single(one_block, one_movie)        
    return True
    

def client_show_one_special(one_block, one_movie):
    global g_media_dict
    
    movie_list = [] 
    
    url = "http://jsonfe.funshion.com/v3/phone/get_special?id=%s&type=mspec&cli=aphone&ver=2.1.1.2&page=1&pagesize=9&sid=1029&ta=2" % (one_movie.m_media_id)
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    if(len(content) == 0):
        return False
    #print 'content: \n%s\n'  %(content)
    data    = client_decode_content(content) 
    #print 'data: \n%s\n'  %(data)
    result = json.loads(data)
    media_list = result['list']
    for media_info in media_list: 
        o_movie = movie_t(media_info['media_id'], media_info['name_cn'])
        movie_list.append(o_movie)
        if(g_media_dict.has_key(o_movie.m_media_id) == False):
            g_media_dict[o_movie.m_media_id] = o_movie
            client_show_one_movie(one_block, o_movie)
    one_movie.m_list_special = movie_list
    
    return True

            
def client_show_index(content):
    block_list = []
    
    result = json.loads(content)
    block_info_list = result['block_list']
    for block_info in block_info_list:  
        movie_list = []      
        one_block = block_t(block_info['type'], block_info['title'], block_info['channel_title'])
        #print 'block:\t%10s,\t%s,\t%s' % (one_block.m_type, one_block.m_title, one_block.m_channel_title)
        block_list.append(one_block)
        program_list = block_info['list']
        for one_item in program_list:       
            one_movie = movie_t(one_item['obj_id'], one_item['title'])
            client_show_one_movie(one_block, one_movie)
            movie_list.append(one_movie)
        one_block.m_movie_list = movie_list
            
    return True


def client_show_channel_movie(one_channel):
    global g_media_dict
    
    section_type = 'recommended'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/operation/get_recommended?cli=aphone&ver=2.1.1.2&type=%s&page=1&sid=1029&deviceid=25B17C690FBC0DBC0BB80EBC684C84EE88FB79BD1DFA8C02A5A89EA129FDC656&ta=2" % (one_channel.m_type)
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0):
        data    = client_decode_content(content)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['mediaid'], movie_info['media_name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_recommended = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
    
    section_type = 'list_hottest'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/media/get_list?cli=aphone&ver=2.1.1.2&sid=1029&type=%s&order=%s&page=1&pagesize=16&rdate=all&region=all&cate=all&ta=2" % (one_channel.m_type, 'pl')
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0):
        data    = client_decode_content(content)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['media_id'], movie_info['name_cn']) 
            movie_list.append(one_movie)   
        one_channel.m_list_ordinary = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
    
    section_type = 'list_newest'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/media/get_list?cli=aphone&ver=2.1.1.2&sid=1029&type=%s&order=%s&page=1&pagesize=16&rdate=all&region=all&cate=all&ta=2" % (one_channel.m_type, 'mo')
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0):
        data    = client_decode_content(content)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['media_id'], movie_info['name_cn']) 
            movie_list.append(one_movie)   
        one_channel.m_list_ordinary = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
    
    section_type = 'list_rate'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/media/get_list?cli=aphone&ver=2.1.1.2&sid=1029&type=%s&order=%s&page=1&pagesize=16&rdate=all&region=all&cate=all&ta=2" % (one_channel.m_type, 'sc')
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0):
        data    = client_decode_content(content)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['media_id'], movie_info['name_cn']) 
            movie_list.append(one_movie)   
        one_channel.m_list_ordinary = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
            
    section_type = 'special'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/operation/get_special_list?type=%s&cli=aphone&ver=2.1.1.2&page=1&pagesize=10&sid=1029&ta=2" % (one_channel.m_type)
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0):
        data    = client_decode_content(content)
        result = json.loads(data)
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['special_id'], movie_info['name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_special = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_special(one_channel, one_movie)
        
    section_type = 'rank_day'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/rank?cli=aphone&sid=1029&ver=2.1.1.2&mtype=%s&rank=%s&ta=2" % (one_channel.m_type, 'day')
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)  
    if(len(content) > 0):  
        result = json.loads(content)
        movie_info_list = result['data']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['mediaid'], movie_info['name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_rank = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
        
    section_type = 'rank_week'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/rank?cli=aphone&sid=1029&ver=2.1.1.2&mtype=%s&rank=%s&ta=2" % (one_channel.m_type, 'week')
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)   
    if(len(content) > 0): 
        result = json.loads(content)
        movie_info_list = result['data']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['mediaid'], movie_info['name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_rank = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
        
    section_type = 'rank_all'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/rank?cli=aphone&sid=1029&ver=2.1.1.2&mtype=%s&rank=%s&ta=2" % (one_channel.m_type, 'all')
    #print 'url: \n%s\n'  %(url)
    content = client_get_url(url)  
    if(len(content) > 0):   
        result = json.loads(content)
        movie_info_list = result['data']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['mediaid'], movie_info['name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_rank = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
        
    return True
    

def client_show_channel_variety(one_channel):
    global g_media_dict
    
    section_type = 'newest'
    movie_list = []
    url = "http://jsonfe.funshion.com/v3/media/get_list?cli=aphone&ver=2.1.1.2&sid=1029&type=%s&order=%s&page=1&pagesize=16&rdate=all&region=all&cate=all&ta=2" % (one_channel.m_type, 'pl')
    #print 'url:\n %s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0): 
        #print 'content:\n %s\n'  %(content)
        data    = client_decode_content(content)
        #print 'data:\n %s\n'  %(data)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['media_id'], movie_info['name_cn']) 
            movie_list.append(one_movie)   
        one_channel.m_list_recommended = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
        
    section_type = 'hottest'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/media/get_list?cli=aphone&ver=2.1.1.2&sid=1029&type=%s&order=%s&page=1&pagesize=16&rdate=all&region=all&cate=all&ta=2" % (one_channel.m_type, 'mo')
    #print 'url:\n %s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0): 
        #print 'content:\n %s\n'  %(content)
        data    = client_decode_content(content)
        #print 'data:\n %s\n'  %(data)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['media_id'], movie_info['name_cn']) 
            movie_list.append(one_movie)   
        one_channel.m_list_recommended = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
    
    section_type = 'rank'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/media/get_list?cli=aphone&ver=2.1.1.2&sid=1029&type=%s&order=%s&page=1&pagesize=16&rdate=all&region=all&cate=all&ta=2" % (one_channel.m_type, 'sc')
    print 'url:\n %s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0): 
        #print 'content:\n %s\n'  %(content)
        data    = client_decode_content(content)
        #print 'data:\n %s\n'  %(data)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['media_id'], movie_info['name_cn']) 
            movie_list.append(one_movie)   
        one_channel.m_list_recommended = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
            
    return True


def client_show_channel_news(one_channel):
    global g_media_dict
    
    section_type = 'recommended'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/get_videos?cli=aphone&ver=2.1.1.2&videotype=%s&sid=1029&page=1&pagesize=10&order=%s&cate=%%E5%%85%%A8%%E9%%83%%A8&ta=2" % (one_channel.m_type, 'hot')
    #print 'url:\n %s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0): 
        #print 'content:\n %s\n'  %(content)
        data    = client_decode_content(content)
        #print 'data:\n %s\n'  %(data)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['video_id'], movie_info['video_name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_recommended = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
    
    section_type = 'newest'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/get_videos?cli=aphone&ver=2.1.1.2&videotype=%s&sid=1029&page=1&pagesize=10&order=%s&cate=%%E5%%85%%A8%%E9%%83%%A8&ta=2" % (one_channel.m_type, 'mo')
    #print 'url:\n %s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0): 
        #print 'content:\n %s\n'  %(content)
        data    = client_decode_content(content)
        #print 'data:\n %s\n'  %(data)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['video_id'], movie_info['video_name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_recommended = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
            
    section_type = 'hottest'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/get_videos?cli=aphone&ver=2.1.1.2&videotype=%s&sid=1029&page=1&pagesize=10&order=%s&cate=%%E5%%85%%A8%%E9%%83%%A8&ta=2" % (one_channel.m_type, 'pl')
    #print 'url:\n %s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0): 
        #print 'content:\n %s\n'  %(content)
        data    = client_decode_content(content)
        #print 'data:\n %s\n'  %(data)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['video_id'], movie_info['video_name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_recommended = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
    
    return True


def client_show_channel_entertainment(one_channel, catelogy):
    global g_media_dict
    
    section_type = 'newest'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/get_videos?cli=aphone&ver=2.1.1.2&videotype=%s&sid=1029&page=1&pagesize=10&order=%s&date=total&cate=%s&ta=2" % (one_channel.m_type, 'mo', catelogy)
    #print 'url:\n %s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0): 
        #print 'content:\n %s\n'  %(content)
        data    = client_decode_content(content)
        #print 'data:\n %s\n'  %(data)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['video_id'], movie_info['video_name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_recommended = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
        
    section_type = 'hottest'
    movie_list = [] 
    url = "http://jsonfe.funshion.com/v3/get_videos?cli=aphone&ver=2.1.1.2&videotype=%s&sid=1029&page=1&pagesize=10&order=%s&date=total&cate=%s&ta=2" % (one_channel.m_type, 'pl', catelogy)
    #print 'url:\n %s\n'  %(url)
    content = client_get_url(url)
    if(len(content) > 0): 
        #print 'content:\n %s\n'  %(content)
        data    = client_decode_content(content)
        #print 'data:\n %s\n'  %(data)
        result = json.loads(data) 
        movie_info_list = result['list']
        for movie_info in movie_info_list: 
            one_movie = movie_t(movie_info['video_id'], movie_info['video_name']) 
            movie_list.append(one_movie)   
        one_channel.m_list_recommended = movie_list    
        for one_movie in movie_list:
            #print '%s:\t%s:\t%s\t%s' % (one_channel.m_type, section_type, one_movie.m_media_id, one_movie.m_media_name)
            if(g_media_dict.has_key(one_movie.m_media_id) == False):
                g_media_dict[one_movie.m_media_id] = one_movie          
                client_show_one_movie(one_channel, one_movie)
    
    return True


                        
def client_show_channels(content):
    channel_list = []    
    
    result = json.loads(content)
    channel_info_list = result['channels']
    for channel_info in channel_info_list:        
        #print '%s\t%s' % (channel_info['type'], channel_info['title'])
        one_channel = channel_t(channel_info['type'], channel_info['title']) 
        channel_list.append(one_channel)   
    
    for one_channel in channel_list:
        if(one_channel.m_type == 'movie'):
            client_show_channel_movie(one_channel)
        elif(one_channel.m_type == 'tv'):
            client_show_channel_movie(one_channel)
        elif(one_channel.m_type == 'variety'):
            client_show_channel_variety(one_channel)        
        elif(one_channel.m_type == 'cartoon'):
            client_show_channel_movie(one_channel)
        elif(one_channel.m_type == 'news'):
            client_show_channel_news(one_channel)
        elif(one_channel.m_type == 'ent'):
            client_show_channel_entertainment(one_channel, 'star')
        elif(one_channel.m_type == 'sport'):
            client_show_channel_entertainment(one_channel, 'all')
        elif(one_channel.m_type == 'ugc'):
            client_show_channel_entertainment(one_channel, '%E6%90%9E%E7%AC%91')           
        
        
    return True

        
def main():
    global g_msmaster_db
    g_msmaster_db = db.DB_MYSQL()
    g_msmaster_db.connect(db.DB_CONFIG_MSMASTER.host, db.DB_CONFIG_MSMASTER.port, db.DB_CONFIG_MSMASTER.user, db.DB_CONFIG_MSMASTER.password, db.DB_CONFIG_MSMASTER.db)
        
    #url = "http://jsonfe.funshion.com/v3/operation/get_index?cli=aphone&ver=2.1.1.2&sid=1029&ta=2"
    #print '%s'  %(url)
    #content = client_get_url(url)
    #data    = client_decode_content(content)
    #client_show_index(data)
    
    url = "http://jsonfe.funshion.com/v3/operation/get_homepage?cli=aphone&ver=2.1.1.2&sid=1029&deviceid=25B17C690FBC0DBC0BB80EBC684C84EE88FB79BD1DFA8C02A5A89EA129FDC656&ta=2"
    #print '%s'  %(url)
    content = client_get_url(url)
    data    = client_decode_content(content)
    client_show_channels(data)    
    
    global g_media_dict
    global g_video_list
    global g_video_dict
    print 'g_media_dict count=%d, g_video_list count=%d, g_video_dict count=%d' % (len(g_media_dict), len(g_video_list), len(g_video_dict))
    
    g_msmaster_db.close()
    
    
if __name__ == "__main__":
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    
    main()