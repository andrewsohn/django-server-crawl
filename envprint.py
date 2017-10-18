import logging

class EnvPrint():
	env = None

	def log_info(obj, mode="info"):
		if EnvPrint.env == "pro" or EnvPrint.env == "dev":
			if mode == "warning":
				logging.warning(obj)
			elif mode == "debug":
				logging.debug(obj)
			elif mode == "error":
				logging.error(obj)
			elif mode == "critical":
				logging.critical(obj)
			else:	
				logging.info(obj)

		else:
			if mode == "pprint":
				pprint(obj)
			else:
				print(obj)