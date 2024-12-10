import os
import subprocess
import sys
import whcnethelper.ConfigFileManager as CFM
import whcnethelper.LoggingUtils as logutils


def exec(dir):
	config_dir = CFM.config_dir
	profile_dir = os.path.join(config_dir, dir)
	scripts_runner = os.path.join(profile_dir, 'runner.sh')
	if not os.path.exists(scripts_runner):
		return True
	try:
		result = subprocess.run(['sh', scripts_runner], capture_output=True, text=True)
		if result.returncode != 0:
			logutils.error(f"Error executing {scripts_runner}: {result.stderr}")
			raise Exception
		else:
			logutils.info(f"Output of {scripts_runner}: {result.stdout}")
	except Exception as e:
		logutils.error(f"Failed to execute {scripts_runner}: {e}")
		logutils.error("To ensure overall stability, the program will exit. Please check for script errors.")
		sys.exit(3)

	return True


def pre_Login():
	return exec('pre-login')


def post_Login_Success():
	return exec('post-login-success')


def post_Login_Failure():
	return exec('post-login-failure')


def on_Disconnect():
	return exec('on-disconnect')


def pre_Logout():
	return exec('pre-logout')


def post_Logout():
	return exec('post-logout')
