import requests

whl = 'dist/klyd-0.2.2-py3-none-any.whl'
token = 'pypi-AgEIcHlwaS5vcmcCJDVkMmNiMjc3LWNiMGQtNDA3NS05MmYzLWNjYWRhNDczYjAzYwACKlszLCI2NzRjMTRmNi0zODE5LTQxZjAtODQ5Ni0zYjY1Y2MzNTkxZjMiXQAABiBa1diqBfxBY6VG_QraVS-Kih9g5u2RbhGdBK4J9KWXE'

with open(whl, 'rb') as f:
    file_content = f.read()

files = {'file': ('klyd-0.2.2-py3-none-any.whl', file_content, 'application/octet-stream')}

response = requests.post(
    'https://upload.pypi.org/legacy/',
    files=files,
    auth=('__token__', token)
)

print(f'Status: {response.status_code}')
print(response.text)