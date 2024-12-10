import requests
import json
import os
import time
import signal
import whcnethelper.LoggingUtils as logutils
import whcnethelper.LoginLogoutHandler as LLH
import whcnethelper.HelperMain as Main
import whcnethelper.ShellScriptHandler as ShellSH


def post_login_living_checker(url):
	LLH_status = LLH.connectivity204_check(url)
	status_url = "http://172.16.1.100/api/account/status"
	try:
		statusApiResponse = requests.get(status_url)
		statusApiResponse.raise_for_status()
		logutils.info("Status check request successfully sent!")
		statusApiResponse = statusApiResponse.json()
		if 'macOnlineCount' in statusApiResponse:
			return [LLH_status, statusApiResponse['code'], statusApiResponse['macOnlineCount']]
		else:
			return [LLH_status, statusApiResponse['code']]
	except requests.exceptions.RequestException as e:
		logutils.error("An error occurred while making the request:", e)
	except Exception as e:
		logutils.error("An error occurred:", e)


def stop_checker(signum, frame):
	logutils.info(f"Received SIGNAL {signum}.")
	if not LLH.send_logout_get():
		logutils.error("Can not logout.")


def KeepAliveCheckerMain(interval, maxDevice, head_payload, pid_file):

	# Catch SIGTERM
	signal.signal(signal.SIGTERM, stop_checker)

	while True:
		Main.check_pid_file(pid_file)
		status = post_login_living_checker()
		if not status:
			logutils.error("Failed to retrieve status. Exiting check loop.")
			logutils.info("Perform on-Disconnect scripts....")
			ShellSH.on_Disconnect()
			return 'checker_error'

		if status[0] != 'is_204' and status[1] != 0:
			logutils.warn("You have been kicked off from the server. Attempting to re-login...")
			retried_times = 0
			IS_DONE = False
			while retried_times < 5:
				csrf_cookies = LLH.get_csrf_cookies()
				login_status = LLH.send_login_post(csrf_cookies, LLH.build_header_payload(Main.USERNAME, Main.PASSWORD, csrf_cookies, status[0]))
				if not LLH.postLogin_check(login_status):
					IS_DONE = False
					retried_times += 1
				else:
					IS_DONE = True
					break
			if not IS_DONE:
				logutils.info("Perform on-Disconnect scripts....")
				ShellSH.on_Disconnect()
				return 'fail-relogin'
		elif status[0] != 'is_204' and status[1] == 0:
			logutils.warn("The connectivity 204 server did not return 204, but you are still online. Please be aware!")
			time.sleep(interval)
			continue
		elif status[1] == 0 and len(status) > 2 and status[2] == maxDevice:
			logutils.warn("You have reached the maximum allowed devices limit. Other devices or this device may kick off.")
		else:
			logutils.info("You are still online. No action needed.")
			time.sleep(interval)
			continue
