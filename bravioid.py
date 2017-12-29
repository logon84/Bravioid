#!/usr/bin/python3 
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf

import json
import os
import sys
import ast
import socket
import requests
import time
import configparser
import xml.etree.ElementTree as ET
import tempfile
from pathlib import Path

config = configparser.ConfigParser(delimiters=(':'))
config.optionxform = lambda option: option
tv_ip = ''
cookie = ''
cmd_names = ();
cmd_codes = ();
url_auth = ['http://', '@@_IP_@@', '/sony/accessControl'];
url_info = ['http://', '@@_IP_@@', '/sony/system'];
url_ircc = ['http://', '@@_IP_@@', '/sony/IRCC']
json_auth = '{"id":8, "method":"actRegister", "version":"1.0", "params":[{ "clientid":"Bravioid","nickname":"Bravioid"},[{"clientid":"Bravioid","value":"yes","nickname":"Bravioid","function":"WOL"}]]}'
json_info = '{"method":"getRemoteControllerInfo","params":[],"id":10,"version":"1.0"}'
xml_ircc = ['<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:X_SendIRCC xmlns:u="urn:schemas-sony-com:service:IRCC:1"><IRCCCode>', '@@_cmd_@@', '</IRCCCode></u:X_SendIRCC></s:Body></s:Envelope>']
headers_ircc = {'content-type': 'text/xml', 'Cookie': '@@_cookie_@@', 'SOAPAction': '"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC"'}
arguments = {}

class GUI:
	def resource_path(self, relative_path): #Win EXE related. Access data when bravioid.exe decompresses. If in dev, get local files
		if hasattr(sys, '_MEIPASS'):
			return os.path.join(sys._MEIPASS, relative_path)
		return os.path.join(os.path.abspath("."), relative_path)
	
	def on_window_main_delete_event(self, widget, event):
		Gtk.main_quit()
		return False

	def on_window_IP_delete_event(self, widget, event):
		Gtk.main_quit()
		return False

	def on_window_PIN_delete_event(self, widget, event):
		Gtk.main_quit()
		return False

	def on_imagemenuitem_quit_activate(self, widget):
		Gtk.main_quit()
		return False

	def on_imagemenuitem_about_activate(self, widget):
		window_about = self.builder.get_object("window_about")
		window_about.show_all()
		return False

	def on_window_about_delete_event(self, widget, event):
		widget.hide()
		return True

	def on_popup1_delete_event(self, widget, event):
		return False

	def on_button_popup_clicked(self, *args):
		popup =  self.builder.get_object("popup1")
		popup.hide()

	def __init__(self):
		self.builder = Gtk.Builder()
		self.builder.add_from_file(self.resource_path("bravioid.glade"))
		self.builder.connect_signals(self)          

	def main(self):
		last_cat = ''
		liststore_family = self.builder.get_object('liststore_family')
		liststore_methods = self.builder.get_object('liststore_methods')
		with open("bravia.api", 'r') as apifile:
			for line in apifile:
				row = ast.literal_eval(line)
				liststore_methods.append(row)
				if last_cat != row [0]:
					last_cat = row [0]
					liststore_family.append([row[0]])
			apifile.close()
		window = self.builder.get_object("window_main")
		window.show_all()
		Gtk.main()

	def pairTV(self):
		window_IP = self.builder.get_object("window_IP")
		window_IP.show_all()
		Gtk.main()

	def on_button_IRRC_clicked(self, *args):
		pressed = Gtk.Buildable.get_name(*args)
		x = pro.send_IRCC_command(pressed.replace("button_", ""))
		statusbar = self.builder.get_object('statusbar1')
		cont = statusbar.get_context_id("statusbar1")
		statusbar.push(cont, pressed.replace("button_", "") + ' [' + str (x) + ']')

	def on_button_sendRAW_clicked(self, *args):
		entry = self.builder.get_object('entry1')
		txt = entry.get_text()
		for comm in txt.split('&'):
			x = pro.send_IRCC_command(comm)
			time_sleep(2)
		statusbar = self.builder.get_object('statusbar1')
		cont = statusbar.get_context_id("statusbar1")
		statusbar.push(cont, entry.get_text() + ' [' + str (x) + ']')

	def on_button_APIsend_clicked(self, *args):
		global arguments
		message = self.builder.get_object("label_reply")
		combobox_API_method = self.builder.get_object('combobox_API_method')
		model_API_method = combobox_API_method.get_model()
		active_API_method = combobox_API_method.get_active()
		url = 'http://' + tv_ip + '/sony/' + model_API_method[active_API_method][0]
		original_data = model_API_method[active_API_method][2]
		tmp = original_data.split ('\"params\":[')
		data_part0 = tmp[0] + '\"params\":['
		tmp = tmp[1].split (']')
		data_part2 = ']' + tmp[1]
		if '_no_name_' in str(arguments):
			data_part1 = '\"' + arguments['_no_name_'] + '\"'
		else:
			data_part1 = str(arguments)
		data = data_part0 + data_part1 + data_part2	
		try:
			r = requests.post(url, data=data, headers={'Cookie': cookie}, timeout=2.000)
			resp = json.dumps(json.loads(r.text), indent=4, sort_keys=True)
		except:
			resp = "Can't connect. If the TV is switched OFF, try swithching it ON first"
		message.set_text (resp)
		statusbar = self.builder.get_object('statusbar1')
		cont = statusbar.get_context_id("statusbar1")
		statusbar.push(cont, model_API_method[active_API_method][1] + ' [' + str(r.status_code) + ']')

	def on_combobox_API_type_changed(self, widget):
		model_API_type = widget.get_model()
		active_API_type = widget.get_active()
		if active_API_type >= 0: #if there's a selected option in combobox_API_type, generate the next combo list using filter
			methods = self.builder.get_object('liststore_methods')
			famfilter = methods.filter_new()
			famfilter.set_visible_func(self.family_filter, model_API_type[active_API_type][0])
			famfilter.refilter()
			combobox_API_method = self.builder.get_object('combobox_API_method')
			combobox_API_method.set_model(famfilter)
			combobox_API_method.set_sensitive(True)
			combobox_API_method.set_active(0)
			button = self.builder.get_object('button_APIsend')
			button.set_sensitive(True)

	def on_combobox_API_method_changed(self, widget):
		global arguments
		combobox_API_parameters = self.builder.get_object('combobox_API_params')
		liststore_params = self.builder.get_object('liststore_params')
		liststore_params.clear()
		entry = self.builder.get_object('entry_param')
		label_value = self.builder.get_object('label_API_param_value')
		button_API_set = self.builder.get_object('button_API_set')
		entry.set_visible(False)
		entry.set_sensitive(False)
		entry.set_no_show_all(True)
		label_value.set_visible(False)
		label_value.set_no_show_all(True)
		button_API_set.set_visible(False)
		button_API_set.set_no_show_all(True)
		arguments = {}
		model_API_method = widget.get_model()
		active_API_method = widget.get_active()
		data = model_API_method[active_API_method][2]
		tmp = data.split ('\"params\":[')
		data_part0 = tmp[0] + '\"params\":['
		tmp = tmp[1].split (']')
		data_part1 = tmp[0]
		data_part2 = ']' + tmp[1] #data = data_part0 + data_part1 + data_part2
		if (len(data_part1) > 0): #if selected method needs params, create the list for the new combo and show it
			if '{' in data_part1: #process name:value arguments
				param_part = ast.literal_eval(data_part1)
				param_part_keys = list(param_part.keys())
				for x in param_part_keys:
					tmp = [x, param_part[x]]
					liststore_params.append(tmp)
					arguments [x] = ''
			else: #process 'only-value' type param
				liststore_params.append(['_no_name_', data_part1.replace('\"', '')])
				arguments ['_no_name_'] = ''
			combobox_API_parameters.set_visible(True)
			combobox_API_parameters.set_sensitive(True)
			combobox_API_parameters.set_no_show_all(False)
		else:	#selected method doesn't need params, return original data and hide combo params
			arguments = ''
			combobox_API_parameters.set_visible(False)
			combobox_API_parameters.set_sensitive(False)
			combobox_API_parameters.set_no_show_all(True)

	def on_combobox_API_params_changed(self, widget):
		global arguments
		model_API_parameters = widget.get_model()
		active_API_param = widget.get_active()
		liststore_params = self.builder.get_object('liststore_params')
		if active_API_param >= 0:
			paramname = liststore_params[active_API_param][0]
			paramtype = liststore_params[active_API_param][1]
			entry = self.builder.get_object('entry_param')
			entry.set_placeholder_text(paramtype)
			entry.set_text('')
			label_value = self.builder.get_object('label_API_param_value')
			label_value.set_text('(' + arguments[paramname] + ')')
			button_API_set = self.builder.get_object('button_API_set')
			label_value.set_visible(True)
			label_value.set_no_show_all(False)
			entry.set_visible(True)
			entry.set_sensitive(True)
			entry.set_no_show_all(False)
			button_API_set.set_visible(True)
			button_API_set.set_no_show_all(False)

	def on_button_API_set_clicked(self, widget):
		global arguments
		entry = self.builder.get_object('entry_param')
		label_value = self.builder.get_object('label_API_param_value')
		combobox_API_parameters = self.builder.get_object('combobox_API_params')
		model_API_parameters = combobox_API_parameters.get_model()
		active_API_param = combobox_API_parameters.get_active()
		arguments[model_API_parameters[active_API_param][0]] = entry.get_text()
		label_value.set_text('(' + entry.get_text() + ')' )
		
	def on_button_DIAL_refresh_clicked(self, widget):
		url = 'http://' + tv_ip + '/DIAL/sony/applist'
		r = requests.get(url, headers={'Cookie': cookie}, timeout=3.000) #get applist
		if r.status_code == 200:
			file_apps = tempfile.TemporaryFile()
			file_apps.write(bytes(r.text,'utf-8'))
			file_apps.seek(0)
			root = ET.fromstring(file_apps.read())
			file_apps.close()
			liststore_apps = self.builder.get_object('liststore_apps')
			liststore_apps.clear()
			for child in root.iter('app'): #download every icon app and store id + name + icon row
				r = requests.get(child.find('icon_url').text, headers={'Cookie': cookie}, timeout=3.000)
				icon = GdkPixbuf.PixbufLoader.new()
				icon.set_size(30, 30)
				icon.write(r.content)
				icon.close()
				icon = icon.get_pixbuf()
				liststore_apps.append([child.find('id').text, child.find('name').text, icon])
			sorted_model = Gtk.TreeModelSort(model=liststore_apps)
			sorted_model.set_sort_column_id(1, Gtk.SortType.ASCENDING)
			combobox_DIAL_apps = self.builder.get_object('combobox_DIAL_apps')
			combobox_DIAL_apps.set_model(sorted_model)	
			button_DIAL_status = self.builder.get_object('button_DIAL_status')
			button_DIAL_run = self.builder.get_object('button_DIAL_run')
			button_DIAL_stop = self.builder.get_object('button_DIAL_stop')
			combobox_DIAL_apps.set_visible('True')
			combobox_DIAL_apps.set_no_show_all('False')
			combobox_DIAL_apps.set_sensitive('True')
			button_DIAL_status.set_visible('True')
			button_DIAL_status.set_no_show_all('False')
			button_DIAL_status.set_sensitive('True')
			button_DIAL_run.set_visible('True')
			button_DIAL_run.set_no_show_all('False')
			button_DIAL_run.set_sensitive('True')
			button_DIAL_stop.set_visible('True')
			button_DIAL_stop.set_no_show_all('False')
			button_DIAL_stop.set_sensitive('True')

	def on_button_DIAL_status_clicked(self, widget):
		label_DIAL_info = self.builder.get_object('label_DIAL_info')
		combobox_DIAL_apps = self.builder.get_object('combobox_DIAL_apps')
		model_DIAL_apps = combobox_DIAL_apps.get_model()
		active_DIAL_app = combobox_DIAL_apps.get_active()
		package = model_DIAL_apps[active_DIAL_app][0]
		url = 'http://' + tv_ip + '/DIAL/apps/' + package
		headers = {'Origin':'package:' + package, 'Host':tv_ip, 'Cookie': cookie }
		r = requests.get(url, headers=headers, timeout=4.000)
		label_DIAL_info.set_text(r.text)

	def on_button_DIAL_run_clicked(self, widget):
		label_DIAL_info = self.builder.get_object('label_DIAL_info')
		combobox_DIAL_apps = self.builder.get_object('combobox_DIAL_apps')
		model_DIAL_apps = combobox_DIAL_apps.get_model()
		active_DIAL_app = combobox_DIAL_apps.get_active()
		package = model_DIAL_apps[active_DIAL_app][0]
		url = 'http://' + tv_ip + '/DIAL/apps/' + package
		headers = {'Origin':'package:' + package, 'Host':tv_ip, 'Cookie': cookie }
		r = requests.post(url, headers=headers, timeout=4.000)
		label_DIAL_info.set_text(r.text)

	def on_button_DIAL_stop_clicked(self, widget):
		url = 'http://' + tv_ip + '/sony/appControl'
		headers = {'Cookie': cookie }
		r = requests.post(url, data ='{"method":"terminateApps","params":[],"id":1,"version":"1.0"}', headers=headers, timeout=4.000)
		label_DIAL_info = self.builder.get_object('label_DIAL_info')
		label_DIAL_info.set_text('All apps stopped')
				

	def family_filter(self, model, iter, data): #filter for generating api comboboxes filtered by destination url
		if data == model[iter][0]:
			return True
		else:
			return False

	def validate_ip(s): #routine to check if input text is a correct ip address
		a = s.split('.')
		if len(a) != 4: #is there four strings dot separated?
			return False
		for x in a:
			if not x.isdigit(): #is every string a number?
				return False
			i = int(x)
			if i < 0 or i > 255: #is every number between 0 and 255?
				return False
		return True

	def on_button_setip_clicked(self, *args):
		global tv_ip
		global cookie
		global url_auth
		global json_auth
		entry2 = self.builder.get_object('entry2')
		message = self.builder.get_object("label2")
		popup =  self.builder.get_object("popup1")
		if GUI.validate_ip(entry2.get_text()):
				url_auth [1] = entry2.get_text()
				try:
					r = requests.post(url_auth [0] + url_auth [1] + url_auth [2], data=json_auth, timeout=2.000)
					if r.status_code == 401:
						tv_ip = entry2.get_text()
						window_IP =  self.builder.get_object("window_IP")
						window_IP.hide()
						window_PIN =  self.builder.get_object("window_PIN")
						window_PIN.show_all()
					elif r.status_code == 200:
						if "Turned off" in r.text:
							message.set_text ('TV is switched OFF, please turn it ON')
							popup.show_all()
						if ":[]" in r.text:
							message.set_text ('Seems that this computer is already paired with TV. Please, unregister it on TV')
							popup.show_all()
					else:	#there's an http server at the other side, but not a TV
						message.set_text ('No TV Found -' + r.status_code)
						popup.show_all()
				except:	#No reponse exception, no TV on the other side
					message.set_text ('No TV Found - Err')
					popup.show_all()
		else:
				message.set_text ('Invalid IP adress!')
				popup.show_all()
		return True


	def on_button_setpin_clicked(self, *args):
		global tv_ip
		global cookie
		global url_auth
		global json_auth
		global cmd_names
		global cmd_codes
		API_families = ['accessControl', 'appControl', 'audio', 'avContent', 'browser', 'cec', 'encryption', 'guide', 'recording', 'system', 'videoScreen']
		data_col_std = '{"method":"@@_setmethod_@@","params":[@@_setparams_@@],"id":1,"version":"@@_setversion_@@"}'
		entry3 = self.builder.get_object('entry3')
		r = requests.post(url_auth [0] + tv_ip + url_auth [2], data=json_auth, auth=('Bravioid', entry3.get_text()), timeout=2.000)
		if r.status_code == 200:#Succesfully registered
			cookie = "auth=" + r.cookies ['auth']
			r = requests.post(url_info [0] + tv_ip + url_info [2], data=json_info, timeout=2.000)
			remote_data = json.loads(r.text)
			for i in range (0, len (remote_data["result"][1])):
				cmd_names = cmd_names + tuple([remote_data["result"][1][i]["name"]])
				cmd_codes = cmd_codes + tuple([remote_data["result"][1][i]["value"]])
		config['DEFAULT'] = {'TV_ip': tv_ip,'Cookie': cookie,'IRCCnames': cmd_names,'IRCCcodes': cmd_codes}
		with open('bravia.cfg', 'w') as configfile:
			config.write(configfile)
		liststore_family = self.builder.get_object('liststore_family')
		liststore_family.clear()
		liststore_methods = self.builder.get_object('liststore_methods')
		liststore_methods.clear()
		file_api = open('bravia.api', 'w')
		for fam in API_families: #ask for methods on every category
			row = [fam]
			liststore_family.append(row)
			r = requests.post('http://192.168.1.5/sony/' + fam, data='{"method":"getMethodTypes","params":[""],"id":1,"version":"1.0"}', headers='', timeout = 2.000)
			json_response = r.json()
			for x in range (0, len(json_response["results"])): #parse every method for its name, arguments and version
				name_col = json_response["results"][x][0] + ' ' + json_response["results"][x][3]
				try: #does it need params for calling?
					tmp = json_response["results"][x][1]
					argums = tmp[0]
					if not '{' in argums:
						argums = '\"' + argums + '\"'
				except: #method doesn,t need input params
					argums = ''
				data_col = data_col_std.replace('@@_setmethod_@@', json_response["results"][x][0])
				data_col = data_col.replace('@@_setparams_@@', argums)
				data_col = data_col.replace('@@_setversion_@@', json_response["results"][x][3])
				row = [fam, name_col, data_col]
				liststore_methods.append(row)
				file_api.write(str(row) + '\n')
		file_api.close()
		window_PIN = self.builder.get_object("window_PIN")
		window_PIN.hide()
		window = self.builder.get_object("window_main")
		window.show_all()

class pro:    
	def send_IRCC_command( str ):
		global xml_ircc
		global url_ircc
		global headers_ircc
		if "==" not in str:
			cmd = cmd_codes[cmd_names.index(str)]
		else:
			cmd = str
		headers_ircc['Cookie'] = cookie 
		r = requests.post(url_ircc [0] + tv_ip + url_ircc [2], data=xml_ircc [0] + cmd + xml_ircc [2], headers=headers_ircc, timeout=2.000)
		return r.status_code


if __name__ == "__main__":
	app = GUI()
	cfg_file = Path("bravia.cfg")
	if cfg_file.is_file():
		config.read('bravia.cfg')
		tv_ip = config.get('DEFAULT', 'TV_ip')
		cookie = config.get('DEFAULT', 'Cookie')
		cmd_names = ast.literal_eval(config.get('DEFAULT', 'IRCCnames'))
		cmd_codes = ast.literal_eval(config.get('DEFAULT', 'IRCCcodes'))
		app.main()
	else:
		app.pairTV()

