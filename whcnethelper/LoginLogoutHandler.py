import requests
import json
from bs4 import BeautifulSoup
import whcnethelper.LoggingUtils as logutils


def connectivity204_check(url):
	preURL = url

	preTest = requests.get(preURL)

	if preTest.status_code != 204:
		logutils.info("Not login, been redirected!")
		soup = BeautifulSoup(preTest.text, 'html.parser')
		meta_tag = soup.find('meta', attrs={'http-equiv': 'refresh'})
		try:
			if meta_tag:
				capContent = meta_tag['content']
				capURL = capContent.split('url=')[1].strip() + "url="
				logutils.info(f"Redirect URL: {capURL}")

				# Repeat request to fetch login home page URL
				capURL = requests.get(capURL).url
				logutils.info(f"Extracted URL: {capURL}")

				return capURL
			else:
				logutils.error("Meta tag not found")
				logutils.error("Meta tag with http-equiv='refresh' not found")
		except Exception as e:
			logutils.error(f"An error occurred: {e}")
	else:
		return 'is_204'


def account_status():
	status_url = "http://172.16.1.100/api/account/status"
	try:
		statusApiResponse = requests.get(status_url)
		statusApiResponse.raise_for_status()
		logutils.info("Status check request successfully sent!")
		statusApiResponse = statusApiResponse.json()
		return statusApiResponse['code']
	except requests.exceptions.RequestException as e:
		logutils.error(f"An error occurred while making the request: {e}")
	except Exception as e:
		logutils.error(f"An error occurred: {e}")
	return None


def get_csrf_cookies():
	capApiURL = "http://172.16.1.100/api/csrf-token"

	try:
		capApiResponse = requests.get(capApiURL)

		# Check the request is successfully sent.
		capApiResponse.raise_for_status()

		# Get Cookies
		capCookies = capApiResponse.cookies

		# Get CSRF Token
		capCSRFToken = capApiResponse.json().get('csrf_token')

		return [capCookies, capCSRFToken]
	except requests.exceptions.RequestException as e:
		logutils.error(f"An error occurred while making the request: {e}")
	except Exception as e:
		logutils.error(f"An error occurred: {e}")

	return None


def build_header_payload(username, password, csrf_cookies, capURL):
	# First set header
	headers = {
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0',
		'Accept': '*/*',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'X-CSRF-Token': csrf_cookies[1],
		'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
		'X-Requested-With': 'XMLHttpRequest',
		'Origin': 'http://172.16.1.100',
		'Connection': 'keep-alive',
		'Referer': capURL
	}

	# Next payload
	payload = {
		'username': username,
		'password': password,
		'nasId': '1',
		'isp': 'local'
	}

	return [headers, payload]


# Variable `cookies` at here should use the return of get_csrf_cookies()
def send_login_post(cookies, head_payload):
	login_url = "http://172.16.1.100/api/account/login"

	try:
		login_response = requests.post(login_url, headers=head_payload[0], cookies=cookies[0], data=head_payload[1])
		login_response.raise_for_status()
		logutils.info("Login request successfully sent!")

		# Store server response
		auth_response = login_response.json()

		return auth_response
	except requests.exceptions.RequestException as e:
		logutils.error(f"An error occurred while making the request: {e}")
	except Exception as e:
		logutils.error(f"An error occurred: {e}")

	return None


def postLogin_check(auth_response):
	authCode = auth_response.get('authCode')
	login_code = auth_response.get('code')
	login_msg = auth_response.get('msg')
	devices_count = auth_response.get('macOnlineCount')

	if authCode == 'ok:radius' and login_code == 0:
		logutils.info("Login is successfully with response:")
		logutils.info(f"Login status: {authCode}\nMessage: {login_msg}\nOnline devices: {devices_count}")
		for key in auth_response.get('online'):
			logutils.info(f"{key}: {auth_response.get('online').get(key)}")
		return True
	else:
		logutils.warn(f"Authentication Server returned with status {authCode} and message {login_msg}.")
		logutils.warn("May be something is wrong due login! Check your account informations!")
		return False


def send_logout_get():
	logout_url = "http://172.16.1.100/api/account/logout"

	try:
		logout_response = requests.get(logout_url)
		logout_response.raise_for_status()
		logutils.info("Logout request successfully sent!")
		logout_response = logout_response.json()
		logout_code = logout_response.get('code')
		logout_msg = logout_response.get('msg')

		if logout_code == 0:
			logutils.info(f"Log out successfully with message {logout_msg}.")
			return True
		else:
			logutils.info(f"Can not logout, reason is {logout_msg}")
			return False
	except requests.exceptions.RequestException as e:
		logutils.error(f"An error occurred while making the request: {e}")
	except Exception as e:
		logutils.error(f"An error occurred: {e}")

	return False
