import browser_cookie3
import requests

cj = browser_cookie3.chrome(domain_name='.strava.com')
for c in cj:
    print(f"{c.name} = {c.value[:30] if c.value else 'EMPTY'}...")

s = requests.Session()
s.cookies = cj
r = s.get('https://www.strava.com/dashboard', allow_redirects=False)
print(f"\nStatus: {r.status_code}")
print(f"Location: {r.headers.get('Location', 'none')}")
