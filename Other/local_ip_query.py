import requests

# 查询本机IP的URL
url = "http://ifconfig.me"
ipwhois_url = "http://ipwhois.app/json/{}"
ipapi_url = "http://ip-api.com/json/{}"

try:
    # 获取本机的公网IP地址
    response = requests.get(url)
    response.raise_for_status()
    public_ip = response.text.strip()
    print(f"本机的公网IP地址: {public_ip}")

    # 使用ipwhois.app API获取IP信息
    ipwhois_response = requests.get(ipwhois_url.format(public_ip))
    ipwhois_response.raise_for_status()
    ipwhois_info = ipwhois_response.json()
    print("IPWhois详细信息:", ipwhois_info)

    # 使用ip-api.com API获取IP信息
    ipapi_response = requests.get(ipapi_url.format(public_ip))
    ipapi_response.raise_for_status()
    ipapi_info = ipapi_response.json()
    print("IP-API详细信息:", ipapi_info)

    # 检查代理或VPN的可能性（来自ipwhois）
    if ipwhois_info.get('proxy') == 'yes' or ipwhois_info.get('vpn') == 'yes' or ipwhois_info.get('tor') == 'yes':
        print("IPWhois检测到代理、VPN或TOR设备正在使用")
    elif ipapi_info.get('proxy') == True:
        print("IP-API检测到代理或VPN设备正在使用")
    else:
        print("未检测到代理或VPN设备")

except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
