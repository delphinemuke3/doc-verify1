import requests, warnings
warnings.filterwarnings('ignore')
s = requests.Session()
r = s.get('https://graduate.rp.ac.rw/?certificate_no=19941', verify=False, timeout=15)
token = r.text.split('name="_token" value="')[1].split('"')[0]
print("TOKEN:", token)
r2 = s.post('https://graduate.rp.ac.rw/check', data={'_token': token, 'certificate_id': '19941'}, verify=False, timeout=15)
print(r2.text[:3000])