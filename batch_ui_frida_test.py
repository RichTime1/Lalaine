from ui_frida_execute import signal_test
import time
import signal
import  datetime, time
import threading
import sys
import time
import frida
from install import *
import subprocess
import hexdump
import os, signal
import yaml
import shutil
import json
import tqdm.asyncio
import subprocess
import argparse

ROOT=""
## 读取yaml文件
def readyaml(file):
    if os.path.isfile(file):
        fr = open(file, 'r')
        yaml_info = yaml.safe_load(fr)
        fr.close()
        return yaml_info
    return None


##显示yaml文件
def display_info(data_list):
    for tmp in data_list:
        print (tmp)


def writeyaml(file, data):
    fr = open(file, 'w')
    yaml.dump(data, fr)
    fr.close()


# 自定义超时异常
class TimeoutError(Exception):
    def __init__(self, msg):
        super(TimeoutError, self).__init__()
        self.msg = msg
 
 
def time_out(interval, callback):
    def decorator(func):
        def handler(signum, frame):
            raise TimeoutError("run func timeout")
 
        def wrapper(*args, **kwargs):
            try:
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(interval)       # interval秒后向进程发送SIGALRM信号
                result = func(*args, **kwargs)
                signal.alarm(0)              # 函数在规定时间执行完后关闭alarm闹钟
                return result
            except TimeoutError as e:
                callback(e)
        return wrapper
    return decorator
 
 
def timeout_callback(e):
    print(e.msg)
 

def process(name):
	
	# Ask user for the name of process
	
	try:
		
		# iterating through each instance of the process
		for line in os.popen("ps ax | grep " + name + " | grep -v grep"):
			fields = line.split()
			
			# extracting Process ID from the output
			pid = fields[0]
			
			# terminating process
			os.kill(int(pid), signal.SIGKILL)
		print("Process Successfully terminated")
		
	except:
		print("Error Encountered while running script")



#280
@time_out(200, timeout_callback)
def test_one_app(bundleID,DEVICE_ID,SMOKE_PATH):
	try:
		signal_test(bundleID,ROOT,DEVICE_ID,SMOKE_PATH)
	except KeyboardInterrupt:
		print("KeyboardInterrupt")
		return

def clean_up():
	process("nosmoke")


def write_bundleID_crawler_config(bundleID,SMOKE_PATH):
	yaml_file =SMOKE_PATH+"demo/crawler.config.yml"

	yaml_info =readyaml(yaml_file)
	print(yaml_info)
	print(bundleID)
	yaml_info['desiredCapabilities']['bundleId']=bundleID
	print(bundleID)
	print(yaml_info)
	writeyaml(yaml_file, yaml_info)



def is_installed(bundleID):
	output = subprocess.run(["ideviceinstaller", "--list-apps"], capture_output=True)
	#print (output)
	#print(bundleID)
	if bundleID in str(output):
		return True
	else:
		return False
	



def test_one_batch(app_input_path,bundleID,ipa,DEVICE_ID,SMOKE_PATH):
	print("Install the app ...")
	if is_installed(bundleID):
		print(bundleID+" successfully installed")
	else:
		status=install(app_input_path+ipa)
		if status !=0:
			print("install failed!!!!")
			return False
		
	time.sleep(1)
	print("begin write to yaml file ...")
	write_bundleID_crawler_config(bundleID,SMOKE_PATH)
	
	time.sleep(1)
	test_one_app(bundleID,DEVICE_ID,SMOKE_PATH)
	clean_up()
	time.sleep(1)
	print("prepare dump app ...")
	#os.system("tidevice kill " + bundleID)
	#decrypted_app(bundleID)
	print("prepare uninstall app ...")
	#uninstall(bundleID)
	return True
	




def write_json(row, result_file):
  fp = open(result_file, 'a')
  fp.write(json.dumps(row)+'\n')
  fp.flush()
  fp.close()




def get_current_report(orignal_macaca_path):
	list_ = os.listdir(orignal_macaca_path)
	for i in range(0, len(list_)):
		path = os.path.join(orignal_macaca_path, list_[i])
		if os.path.isdir(path):
			return path



def read_log_file(log_file):
	f=open(log_file,"r")
	content=f.readlines()
	f.close()
	b_list=[]
	for c in content:
		#print(c.strip())

		line=json.loads(c.strip())
		b_id=line["bundleID"]
		b_list.append(b_id)
		#print("\n")
	return b_list




if __name__ == "__main__":

	#folder=sys.argv[1]
	#bundleID="ai.cloudmall.ios"
	#root="/Users/xiaoyue-admin/Documents/privacy_label/code/batch_dynamic_test"
	#ROOT=sys.argv[2]

	parser = argparse.ArgumentParser(description="Please specify the parameters")
	# parser.add_argument("-H", "--Help", help="Example: Help argument", required=False, default="")
	parser.add_argument("-d", "--dic", help="[Required] specify the repo directory, the default is current directory",
						required=True, default=".")
	parser.add_argument("-n", "--folder", help="[Required] specify which folder your test app in", required=True,
						default="0")
	parser.add_argument("-i", "--device", help="[Required] specify the device ID of your iOS",
						required=True, default="")
	parser.add_argument("-s", "--smoke", help="specify smoke installation path, the default is '/usr/local/lib/node_modules/nosmoke/'", required=False, default="/usr/local/lib/node_modules/nosmoke/")

	argument = parser.parse_args()
	status = False

	if argument.dic:
		print("You have used '-d' or '--dic' with argument: {0}".format(argument.dic))
		status = True
	if argument.folder:
		print("You have used '-n' or '--folder' with argument: {0}".format(argument.folder))
		status = True
	if argument.device:
		print("You have used '-i' or '--device' with argument: {0}".format(argument.device))
		status = True
	if argument.smoke:
		print("You have used '-s' or '--smoke' with argument: {0}".format(argument.smoke))
		status = True
	if not status:
		print("Maybe you want to use -d or -n or -m?")

	ROOT=argument.dic
	folder=argument.folder
	DEVICE_ID=argument.device
	SMOKE_PATH=argument.smoke


	app_input_path = ROOT+'/app/'+ str(folder)+"/"
	frida_output_path= ROOT+'/result/'+ str(folder)+"/frida_output/"
	log_file= ROOT+'/result/'+ str(folder) +'/log.txt'
	reports_path = ROOT+'/result/'+ str(folder)+"/reports/"
	error_log = ROOT+'/result/'+ str(folder) +'/error_log.txt'
	#determine app input folder is exsiting
	if not os.path.exists(app_input_path):
		print("no app input")
		sys.exit(1)


	#determine frida output folder is exsiting
	if not os.path.exists(frida_output_path):
		os.makedirs(frida_output_path)

	#determine macaca report folder is exsiting
	if not os.path.exists(reports_path):
		os.makedirs(reports_path)


	files = os.listdir(app_input_path)
	for ipa in files:
		if ipa==".DS_Store":
			continue
		new_record={}
		#print(ipa)
		start_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		bundleID=get_bundle_id(ipa)	
		ipa_name=ipa.split(".ipa")[0] + ".txt"
		print("begin testing "+bundleID)

		### based on frida output to check whether is app is been test
		#if os.path.exists(frida_output_path + ipa_name):
			#print("this ipa has been tested!!!")
			#continue

		### based on log file to check whether is app is been test
		if os.path.exists(log_file):
			b_list=read_log_file(log_file)
			if bundleID in b_list:
				pass
				##uncomment this if want to repeat testing
				#print("this ipa has been tested!!!")
				#continue


		flag=test_one_batch(app_input_path,bundleID,ipa,DEVICE_ID,SMOKE_PATH)
		# flag = True
		if flag:
			end_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

			##move frida out put to sepcific folder
			#ipa_name=ipa.split(".ipa")[0] + ".txt"
			src=ROOT+"/frida_tmp.txt"
			dst=frida_output_path + ipa_name
			shutil.move(src, dst)


			##move macaca report to sepeific folder
			orignal_macaca_path=ROOT+"/reports"
			src_screen_shoot=get_current_report(orignal_macaca_path)
			dst_screen_shoot=reports_path+ipa.split(".ipa")[0] + "/"
			try:
				print("src : " + src_screen_shoot)
				print("dst : " + dst_screen_shoot)
				shutil.move(src_screen_shoot, dst_screen_shoot)
				if os.path.exists(dst_screen_shoot + "ios.log"):
					os.remove(dst_screen_shoot + "ios.log")
			except:
				pass

			new_record["bundleID"]=bundleID
			new_record["start_time"]=start_time
			new_record["end_time"]=end_time
			new_record["ipa_path"]=app_input_path+ipa
			new_record["frida_path"]=frida_output_path + ipa_name
			write_json(new_record, log_file)

			time.sleep(3)
		else:
			with open(error_log, 'a+') as f:
				f.write(bundleID + " :: install failed...")

		wd_end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		with open("wd/startTimes/wd_test_time.txt", "a", encoding="utf-8") as f:
			f.writelines(str(start_time))
			f.writelines("\n")
			f.writelines(ipa)
			f.writelines("\n")
			f.writelines(str(wd_end_time))
			f.writelines("\n")
			f.writelines("----------------")
			f.writelines("\n")

		
