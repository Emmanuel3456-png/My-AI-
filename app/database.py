import hashlib, json, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'quantum_data.json')

def hash_pass(p): return hashlib.sha256(p.encode('utf-8')).hexdigest()
def load_data():
    default={'users':{'admin':{'password':hash_pass('admin123'),'role':'admin'}},'memory':{},'knowledge':{},'settings':{}}
    try:
        with open(DB_FILE,'r',encoding='utf-8') as f: d=json.load(f)
        for k,v in default.items(): d.setdefault(k,v)
        return d
    except Exception: return default

def save_data(data):
    tmp=DB_FILE+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(data,f,indent=2,ensure_ascii=False)
    os.replace(tmp,DB_FILE)
def load_users(): return load_data()['users']
def save_users(v): d=load_data(); d['users']=v; save_data(d)
def load_memory(): return load_data()['memory']
def save_memory(v): d=load_data(); d['memory']=v; save_data(d)
def load_knowledge(): return load_data()['knowledge']
def save_knowledge(v): d=load_data(); d['knowledge']=v; save_data(d)
def load_settings(): return load_data()['settings']
def save_settings(v): d=load_data(); d['settings']=v; save_data(d)
