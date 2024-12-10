import datetime
import time


start_time = None


def initialize_module():
	global start_time
	start_time = time.monotonic()


def get_dmesg_timestamp():
	global start_time
	if start_time is None:
		raise Exception("Module not initialized. Call 'initialize_module' before logging.")
	elapsed_time = time.monotonic() - start_time
	return f"{elapsed_time:.6f}"


def get_current_time():
	return datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")


def info(message):
	dmesg_time = get_dmesg_timestamp()
	current_time = get_current_time()
	log_entry = f"[{dmesg_time} {current_time} I] {message}"
	print(log_entry)


def warn(message):
	dmesg_time = get_dmesg_timestamp()
	current_time = get_current_time()
	log_entry = f"[{dmesg_time} {current_time} W] {message}"
	print(log_entry)


def error(message):
	dmesg_time = get_dmesg_timestamp()
	current_time = get_current_time()
	log_entry = f"[{dmesg_time} {current_time} E] {message}"
	print(log_entry)
