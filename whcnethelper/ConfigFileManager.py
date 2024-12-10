import os
import json

global config_dir
config_dir = None


def get_default_config_dir():
	xdg_config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
	return os.path.join(xdg_config_home, 'whcnethelper')


def get_config_dir(args):
	if args.system_managed_config_dir:
		return '/etc/whcnethelper'
	elif args.config_dir:
		return args.config_dir
	else:
		return get_default_config_dir()


def create_directories(base_dir, dirs):
	created_dirs = []
	if not os.path.exists(base_dir):
		os.makedirs(base_dir)
		created_dirs.append(base_dir)
	for directory in dirs:
		dir_path = os.path.join(base_dir, directory)
		if not os.path.exists(dir_path):
			os.makedirs(dir_path, exist_ok=True)
			created_dirs.append(dir_path)
	return created_dirs


def cfgmgrMain(args):
	global config_dir
	config_dir = get_config_dir(args)

	configFile_path = os.path.join(config_dir, "config.json")
	if not os.path.exists(configFile_path):
		print("Where is your configuration file?")
		configFile_content = {}
		os.makedirs(config_dir, exist_ok=True)
		with open(configFile_path, 'w') as f:
			json.dump(configFile_content, f)
		raise FileNotFoundError(f"'config.json' is not found in {config_dir}. We help you created it. Please modify this file.")
	else:
		with open(configFile_path, 'r') as f:
			configFile_content = json.load(f)
			required_keys = {'username', 'password'}
			optional_keys = {'maxOnlineDevices', 'refreshInterval', 'captivePortalServer'}
			allowed_keys = required_keys | optional_keys
			unknown_keys = set(configFile_content.keys()) - allowed_keys
			missing_keys = required_keys - set(configFile_content.keys())

			if unknown_keys:
				raise ValueError(f"In your 'config.json' located in {config_dir}, the following unknown keys are present: {unknown_keys}")

			if missing_keys:
				raise ValueError(f"In your 'config.json' located in {config_dir}, the following required keys are missing: {missing_keys}")

	project_scripts_dir = os.path.join(config_dir, 'scripts.d')
	directories = [
		'pre-login',
		'post-login-success',
		'post-login-failure',
		'on-disconnect',
		'pre-logout',
		'post-logout'
	]

	missing_dirs = [d for d in directories if not os.path.exists(os.path.join(project_scripts_dir, d))]
	if missing_dirs:
		print("Missing directories detected:")
		for dir in missing_dirs:
			print(f" - {dir}")
		print("Creating missing directories...")

	created_dirs = create_directories(project_scripts_dir, directories)

	if created_dirs:
		print("")
		for dir in created_dirs:
			print(f"Created directory: {dir}")
		print("Directory structure has been set up.")
		print("Place your shell scripts into these directories. For more information, please see man:whcnethelper(5)")
		print("Script will exit as expected. Please restart the script.")
		exit(0)
	else:
		print("All required directories already exist.")

		# At this point, function can return the config file.
		return configFile_content
