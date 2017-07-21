from StringIO import StringIO
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from bs4 import BeautifulSoup as BS
import base64
import requests
import re
import json
import time
from threading import Thread
import Queue
import random
import traceback
SIZES=["8.5","9","9.5","10.5","11","11.5","12"]
#SIZES=["12"]
MAXHARVEST=20*(len(SIZES))
print "Total harvesting {0} sessions".format(MAXHARVEST)
HARVESTQUEUE=Queue.Queue()
class KicksStore:
	def __init__(self,config=None,timeout=30):
		if config==None:
			self.config=json.loads(open("kicksconfig.json","r").read())
		else:
			self.config=config
		self.timeout=timeout
		self.updateconfig()
	def updateconfig(self):
		self.emailaddress=self.config["email"]
		self.firstname=self.config["first_name"]
		self.lastname=self.config["last_name"]
		self.address1=self.config["address1"]
		self.address2=self.config["address2"]
		self.city=self.config["city"]
		self.countrycode=self.config["countrycode"]
		self.country=self.config["country"]
		self.province=self.config["state"]
		self.zipcode=self.config["zipcode"]
		self.phone=self.config["phone"]
		self.cardnumber=self.config["ccnumber"]
		self.cardowner=self.config["ccowner"]
		self.cardexpiry=self.config["cardexpiry"]
		self.cardccv=self.config["cardccv"]
	@staticmethod
	def gettoken():
		while True:
			print "Getting token"
			session=requests.session()
			session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"})
			try:
				d=session.get("https://kicksstore.eu/buty-nike-kobe-ad-nxt-882049-600.html",timeout=30)
				d=BS(d.text)
				token=d.find("input",{"name":"_token"})["value"]
				return token
			except Exception as e:
				print e
				continue
	def addtocart(self,hdata,pid,size):
		session=hdata["session"]
		retries=0
		token=hdata["tokens"].pop()
		while True:
			if retries>=10:
				raise Exception("Maximum retries for add to cart reached")
			try:
				print "Adding to cart {0} of size {1}".format(pid,size)
				d=session.post("https://kicksstore.eu/basket/add/{0}".format(pid),data={"_token":token,"size":size},timeout=self.timeout,allow_redirects=False)
				d.raise_for_status()
				print "Successfully added to cart"
				break
			except Exception as e:
				print repr(e)
				retries+=1
	def fastcheckout(self,hdata):
		debugid=random.randint(1,1000000)
		token=hdata["tokens"].pop()
		session=hdata["session"]
		retries=0
		while True:
			if retries>=10:
				raise Exception("Maximum retries for order confirm reached")
			try:
				print "Confirming order"
				d=session.post("https://kicksstore.eu/order/confirm",data={"_token":token},timeout=self.timeout)
				d.raise_for_status()
				print "Order confirmed, going to payment"
				break
			except Exception as e:
				print repr(e)
				retries+=1
		x=StringIO('-----BEGIN PUBLIC KEY-----\r\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCy/5rF+Y9jiZdYvZICOCg+C/OtHt4EqVX9L1QE\r\npnk92vDrZbCXb2wZGPJkUpfM2bpMITL0IASTyss/5/+S8YR2De+E9yzebuv6VGhV7cwnCPffdOxj\r\neL1hPEzcRx+1c20RnnubqOH6JaGx10qgaSS1DYxaCl1UurVtK5mwMDGv5wIDAQAB\r\n-----END PUBLIC KEY-----')
		y=RSA.importKey(x)
		z=PKCS1_v1_5.new(y)
		w=z.encrypt((self.cardnumber+'|'+self.cardexpiry+'|'+self.cardccv+'|'+"https://kicksstore.eu").encode('ascii'))
		carddata=base64.b64encode(w)
		debugh=open("{0}paymentpage.html".format(debugid),'w')
		debugh.write(d.text.encode('utf-8'))
		debugh.close()
		v=BS(d.text)
		price=v.find("input",{"name":"price"})
		orderid=v.find("input",{"name":"orderid"})
		retries=0
		while True:
			if retries>=10:
				raise Exception("Maximum retries for payment submit reached")
			try:
				print "Submitting payment request"
				d=session.post("https://kicksstore.eu/payment/tpaycard/pay",data={"carddata":carddata,"orderid":orderid,"price":price,"client[name]":self.cardowner,"client[email]":self.emailaddress},timeout=self.timeout)
				debugh=open("{0}paymentdone.html".format(debugid),'w')
				debugh.write(d.text.encode('utf-8'))
				debugh.close()
				break
			except Exception as e:
				print e
				retries+=1
				continue
		try:
			d.raise_for_status()
			print "Payment successful"
		except Exception as e:
			print e
			print "Payment failed"
	def halfcheckout(self):
		token=KicksStore.gettoken()
		session=requests.session()
		session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"})
		hdata={"session":session,"tokens":[token]}
		self.addtocart(hdata,"87902","12.5")
		data={"_token":KicksStore.gettoken(),"addressValue[firstname]":self.firstname,"addressValue[lastname]":self.lastname,"addressValue[address]":self.address1,"addressValue[postcode]":self.zipcode,"addressValue[city]":self.city,"addressValue[Country_id]":self.countrycode,"addressValue[phone]":self.phone,"phone_country":"US","addressValue[States_id]":self.province,"email":self.emailaddress,"isRegistered":0,"unregistered":1,"comment":"","agree":1,"invoiceValue_select":"","invoiceValue[company]":"","invoiceValue[NIP]":"","invoiceValue[address]":self.address1,"invoiceValue[postcode]":self.zipcode,"invoiceValue[city]":self.city,"invoiceValue[Country_id]":self.countrycode,"Send":"Continue"}
		v=session.get("https://kicksstore.eu/order/anonymous")
		d=session.post("https://kicksstore.eu/order",data=data,timeout=self.timeout)
		d.raise_for_status()
		token=KicksStore.gettoken()
		data={"_token":token,"Delivery_form_id":"8_1","Payment_id":6,"InPost_machineName":"","InPost_machineAddress":"","Payment_type_id":""}
		d=session.post("https://kicksstore.eu/order/delivery",data=data,timeout=self.timeout)
		d.raise_for_status()
		if d.url!="https://kicksstore.eu/order/confirm":
			raise Exception(d.url)
		d=session.get("https://kicksstore.eu/basket")
		delurl=re.search("https:\/\/kicksstore.eu\/basket\/delete\/[^\"]*",d.text).group(0)
		print "Deleting element from basket"
		print delurl
		session.get(delurl,timeout=self.timeout)
		for i in range(0,3):
			hdata["tokens"].append(KicksStore.gettoken())
		return hdata
HANDLER=KicksStore()
def harvest():
	while True:
		if HARVESTQUEUE.qsize()>MAXHARVEST:
			return
		try:
			v=HANDLER.halfcheckout()
			HARVESTQUEUE.put(v)
			print "Total harvested sessions : {0}".format(HARVESTQUEUE.qsize())
		except Exception as e:
			print e
			print "Failed to harvest"
def checkout(pid,size):
	try:
		v=HARVESTQUEUE.get()
	except:
		print "No more harvested sessions"
		return
	try:
		HANDLER.addtocart(v,pid,size)
	except Exception as e:
		print e
		print "Failed to add to cart"
		return
	try:
		HANDLER.fastcheckout(v)
	except Exception as e:
		traceback.print_exc()
		print "Failed to checkout"
def monitor():
	sess=requests.session()
	sess.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"})
	while True:
		try:
			d=sess.get("https://kicksstore.eu/products/jordan-space-jam/keyword,jordan%20space%20jam")
			d=BS(d.text)
			products=d.find_all("a",{"class":"product_a"})
			prices=[]
			for p in products:
				price=p.find("span",{"data-currency":"USD"})
				if price!=None:
					prices.append(price.text)
					if "220" in price.text:
						pid=p.find("img")["src"].split("/")[-2]
						for i in range(0,20):
							for z in SIZES:
								Thread(target=checkout,args=(pid,z)).start()
						return
			print "Found products with prices {0}".format(str(prices))
		except Exception as e:
			print e
		print "Not found the product yet"
		time.sleep(.5)
def main():
	for i in range(0,20):
		Thread(target=harvest).start()
	monitor()
if __name__=="__main__":
	main()
