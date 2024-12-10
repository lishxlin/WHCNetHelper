from __future__ import absolute_import


import os
import sys
import time
import signal
import multiprocessing
import subprocess
import shutil
import argparse
from whcnethelper import __version__
import whcnethelper.ConfigFileManager as cfgmgr
import whcnethelper.LoggingUtils as logutils
import whcnethelper.LoginLogoutHandler as LLH
import whcnethelper.KeepAliveCheck as KAC
import whcnethelper.ShellScriptHandler as ShellSH

global PID_FILE
PID_FILE = None


def check_pid_file(pid_file):
	if not os.path.exists(pid_file):
		logutils.error("PID file missing, exiting daemon with error.")
		logutils.error("Critical Error: PID file missing.")
		sys.exit(2)


def daemon_process(interval, maxDev, head_payload, pid_file):
	logutils.info(f"Daemon started with PID {os.getpid()}.")
	KAC.KeepAliveCheckerMain(interval, maxDev, head_payload, pid_file)


def start_daemon(interval, maxDev, head_payload, pid_file):
	global PID_FILE
	PID_FILE = pid_file
	process = multiprocessing.Process(target=daemon_process, args=(interval, maxDev, head_payload, PID_FILE))
	process.start()
	logutils.info(f"Started daemon process with PID {process.pid}.")
	with open(PID_FILE, "w") as f:
		f.write(str(process.pid))


def stop_daemon():
	try:
		with open(PID_FILE, "r") as f:
			pid = int(f.read())
		logutils.info(f"Stopping daemon process with PID {pid}...")

		start_time = time.time()
		while time.time() - start_time < 2:
			try:
				os.kill(pid, signal.SIGTERM)
				time.sleep(0.1)
			except ProcessLookupError:
				break
		else:
			print(f"Process {pid} did not terminate within 2 seconds. Sending SIGKILL...")
			os.kill(pid, signal.SIGKILL)

		os.remove(PID_FILE)
		logutils.info("Daemon process stopped.")
		return True
	except FileNotFoundError:
		logutils.error("No running daemon process found.")
	except ProcessLookupError:
		logutils.error("No process with the given PID found.")


def parse_arguments():
	parser = argparse.ArgumentParser(
		description=f"WHCNetHelper: A tool for automated login, keep-alive checks, and script execution.\nVersion: {__version__}\n\n** Current release of this tool take /var/run to store its PID file. **",
		formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument("action", choices=["start", "stop"], help="start: Execute login and start keep-alive checks\nstop: Perform logout operation and exit")
	parser.add_argument('--config-dir', type=str, help='Path to the configuration directory')
	parser.add_argument('--system-managed-config-dir', action='store_true', help='Use system-managed configuration directory (/etc/whcnethelper)')

	# The following two arguments should be implemented:
	# parser.add_argument('--ramdisk-dir', type=str, help="Specify the directory to use for the RAM disk. The user is responsible for mounting the RAM disk (ramfs).")
	# parser.add_argument('--no-ramdisk', action='store_true', help="Disable the use of a RAM disk.")
	parser.add_argument("--allow-host-os", action="store_true", help="Allow running directly on the Host OS, bypassing virtualization checks.")
	parser.add_argument("--allow-non-privileged", action="store_true", help="Allow running without elevated privileges. This option also implicitly allows running on the Host OS.")
	parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

	# Return Namespace(action='start', config_dir=None, system_managed_config_dir=False, ramdisk_dir=None, no_ramdisk=False, allow_host_os=False, allow_non_privileged=False)
	return parser.parse_args()


def main():
	prog_args = parse_arguments()
	ALLOW_BARE = prog_args.allow_host_os
	ALLOW_UNPRIV = prog_args.allow_non_privileged
	ACTION = prog_args.action

	logutils.initialize_module()

	if ALLOW_UNPRIV is not True:
		if os.getuid() != 0:
			print("This script should be run as root.")
			sys.exit(1)
			_PIDFILE = "/var/run/whcnethelper.pid"
	else:
		if prog_args.system_managed_config_dir is True:
			print("Non privileged environment can not use system-managed config dir.")
			sys.exit(1)
		print("*** Running as a non-privileged user will cause some shell scripts to fail if they require privileged permissions. ***")
		_PIDFILE = '/tmp/.whcnethelper.pid'
		ALLOW_BARE = True

	if ALLOW_BARE is not True:
		if not shutil.which('virt-what'):
			print("virt-what is not installed. Please install it first.")
			sys.exit(1)
		virt_check_result = subprocess.run(['virt-what'], capture_output=True, text=True)
		if virt_check_result.returncode == 0:
			print("This script SHOULD BE run in a virtualized environment or container.")
			sys.exit(1)
	else:
		print("*** Running on bare metal may cause security issues. Shell script security is not guaranteed. Use with caution! ***")

	# Process config file and scripts directories.
	global cfgmgr_content
	cfgmgr_content = cfgmgr.cfgmgrMain(prog_args)

	if not cfgmgr_content:
		raise Exception("There're some errors in this program, please provide feedback!")

	if ACTION == 'start':
		logutils.info("Welcome to WHCNetHelper: A tool for automated login, keep-alive checks, and script execution.")
		logutils.info(f"Current version is {__version__}")
		logutils.info("Perform Pre-Login scripts....")
		ShellSH.pre_Login()
		global USERNAME
		global PASSWORD
		USERNAME = cfgmgr_content['username']
		PASSWORD = cfgmgr_content['password']
		if 'maxOnlineDevices' in cfgmgr_content:
			MAX_ONLINE_DEV = cfgmgr_content['maxOnlineDevices']
		else:
			MAX_ONLINE_DEV = 2

		if 'refreshInterval' in cfgmgr_content:
			REFRESH_INTERVAL = cfgmgr_content['refreshInterval']
		else:
			REFRESH_INTERVAL = 5

		if 'captivePortalServer' in cfgmgr_content:
			CAP_PORTAL_SERVER = cfgmgr_content['captivePortalServer']
		else:
			CAP_PORTAL_SERVER = "http://connect.rom.miui.com/generate_204"

		# Start Login Process
		# Check first
		return_of_204_check = LLH.connectivity204_check(CAP_PORTAL_SERVER)
		if return_of_204_check != 'is_204':
			logutils.info("You seem to need to log in.")

			# Double check account status
			accStatus = LLH.account_status()
			if accStatus is not None and accStatus != 0:
				logutils.info("You really need to login!")

				# First time login
				csrf_cookie = LLH.get_csrf_cookies()
				login_post_request = LLH.send_login_post(csrf_cookie, LLH.build_header_payload(USERNAME, PASSWORD, csrf_cookie, return_of_204_check))
				if login_post_request is not None:
					if not LLH.postLogin_check(login_post_request):
						logutils.error("Can not login at early start, program will exit....")
						logutils.info("Perform Post-Login-Failure scripts....")
						ShellSH.post_Login_Failure()
						sys.exit(1)
					else:
						logutils.info("Perform Post-Login-Success scripts....")
						ShellSH.post_Login_Success()

						# Start a monitor daemon
						daemon_status = start_daemon(REFRESH_INTERVAL, MAX_ONLINE_DEV, LLH.build_header_payload(USERNAME, PASSWORD, csrf_cookie, return_of_204_check), _PIDFILE)
						if daemon_status == 'checker_error':
							logutils.error("Critical Error happened, program will exit.....")
							sys.exit(1)
						elif daemon_status == 'fail-relogin':
							logutils.error("Failed to relogin, program will exit....")
							sys.exit(1)
			else:
				logutils.error("Can not check account status, program will exit....")
				sys.exit(1)
		else:
			logutils.info("You may not need login.")
			csrf_cookie = LLH.get_csrf_cookies()
			daemon_status = start_daemon(REFRESH_INTERVAL, MAX_ONLINE_DEV, LLH.build_header_payload(USERNAME, PASSWORD, csrf_cookie, return_of_204_check), _PIDFILE)
			if daemon_status == 'checker_error':
				logutils.error("Critical Error happened, program will exit.....")
				sys.exit(1)
			elif daemon_status == 'fail-relogin':
				logutils.error("Failed to relogin, program will exit....")
				sys.exit(1)
	elif ACTION == 'stop':
		logutils.info("Perform Pre-Stop scripts...")
		ShellSH.pre_Logout()
		if stop_daemon():
			logutils.info("Perform Post-Stop scripts...")
			ShellSH.post_Logout()
			logutils.info("Program Stopped.")
		else:
			logutils.error("Error happened when stopping!")
			sys.exit(1)
	else:
		pass
