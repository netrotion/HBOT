from zlapi import ZaloAPI
from zlapi.models import *
import json
import time
import os
import queue
import requests
from datetime import datetime
from g4f.client import Client
from g4f.Provider import *
import math
from concurrent.futures import ThreadPoolExecutor

#useless code
__AUTHOR__ = ["Le Viet Hung", "28082006"]

#color code
red     = "\033[91m"
green   = "\033[92m"
yellow  = "\033[93;1m"
blue    = "\033[94m"
magenta = "\033[95m"
cyan    = "\033[96m"
white   = "\033[1;37m"
    
#archive message data
thread = ThreadPoolExecutor(max_workers=9999)
message_data = {}

class Hnglbot(ZaloAPI):#main class
    def __init__(self, phone, password, imei, session_cookies=None, user_agent=None, auto_login=True):
        super().__init__(phone, password, imei, session_cookies, user_agent, auto_login)
        dataset = main.fetch_client_data() #fetch data from config.json file
        self.imei = dataset["imei"] #set requiment params
        self.cookies = dataset["cookies"] #set requiment params
        self.phone = dataset["phone"] #set requiment params
        self.password = dataset["password"] #set requiment params
        self.dataset = dataset["config"] #set requiment params
        self.cloudid = dataset["cloudid"] #id chat from cloudID
        self.apikey = dataset["gptkey"] #chat GPT api key
        self.account_id = self.fetchAccountInfo()["profile"]["userId"] #account user id
        self.botmemory = [] #use to self bot sending (fixing duplicate response)
        self.warning_dataset = json.loads(open("warning.json", "r", encoding = "utf-8").read()) #lol understand urself
        self.gptclient = Client(
            api_key=self.apikey,
        ) #generate chat gpt client to .gpt feature

        self.monitor_mode = False
        self.gpt_mode = False
        
        base_path = os.getcwd().replace("\\", "/")
        #almost useless
        self.command = {
            #type = reply, raw message, picture, file
            ".gpton" : {
                "send_type" : "message",
                "mention" : False
            },
            ".monitoron" : {
                "send_type" : "message",
                "mention" : False
            },
            ".info" : {
                "send_type" : "message",
                "message" : "Bot name : HBOT\nAuthor : Lê Việt Hùng\nVersion : 1.0.0\nDecription : type \".help\" for more infomation\n",
                "mention" : False
            },
            ".help" : {
                "send_type" : "message",
                "message" : "Command signal : \".\"\n.monitor<on/off> : [requirement permission] -> Use for anti spam, etc...\n.gpt<on/off> : [requirement permission] -> Make conversation with chat GPT\n.tool : [User permission] -> Fetch infomation about hngltool\n.image <content> : [User permission] -> Create a image using AI, make sure .gpt feature is enable.\na",
                "mention" : False
            },
            ".tool" : {
                "send_type" : "message",
                "message" : "Filename : hngltool.py\nDecription : Some feature added in my python script\nVersion : 2.8.0\nFor python 3.11 : https://pornhub.com\nFor python 3.12 : https://pornhub.com\nFor python 3.13 : https://pornhub.com\n",
                "mention" : True,
            }
            
        }


    @staticmethod
    def input_function(text: str, range: tuple): #smart input function to use
        try:
            inpt = int(input(text))
            if range[0] <= inpt <= range[1]:
                return inpt
            raise IndexError
        except Exception as e:
            print(f"{red} Dữ liệu nhập không hợp lệ!, Exception : ", e)
            time.sleep(1)
            return Hnglbot.input_function(text, range)
            

    def fetch_group(self): #fetch , show and pickup group id to aimming
        data = self.fetchAllGroups()
        group_data_map = data["gridVerMap"]
        group_data_list = [i for i in group_data_map]
        group_dataset = {}
        print(f"{red}[ {white}Version {red}] {white}: {yellow}", data["version"])
        
        for i in range(len(group_data_list)):
            indx = str(i) if len(str(i)) == 2 else "0" + str(i)
            groupname = self.fetchGroupInfo(group_data_list[i])['gridInfoMap'][group_data_list[i]]['name']
            group_dataset[group_data_list[i]] = groupname
            print(f"{red}[ {white}{indx} {red}] : {yellow}{groupname} {red}| {cyan}{group_data_list[i]}")
        
        # print(f"{red}[ {white}{i + 1} {red}] : AIMING ALL")
        
        self.idmap = group_dataset
        self.aim_id = Hnglbot.input_function(
            f"{red}[ {white}+ {red}] {yellow}Choosing number {white}: {cyan}",
            (0, i + 1)
        )
        
        self.aim_id = group_data_list[self.aim_id]
        self.groupinfo = self.fetchGroupInfo(self.aim_id)
        return 
    
    def processor(self, dataset: str = "", params = None, message_object = None): #working with non-monitor action
        if len(self.botmemory) >= 2:
            self.botmemory.pop(0)
        
        if dataset["send_type"] == "file":
            path = dataset["path"]
            try:
                self.sendRemoteFile(
                    fileUrl = path.replace("/", "\\"),
                    thread_id = params["thread_id"],
                    thread_type = params["thread_type"],
                    fileName = path.split("/")[-1],
                    extension = path.split("/")[-1].split(".")[-1] 
                )
            except Exception as e:
                print(e)

        elif dataset["send_type"] == "image":
            
            if (self.gpt_mode) and (str(message_object["msgId"]) not in self.botmemory) and (message_object["idTo"] == self.aim_id) and (message_object["msgType"] == "webchat") and (len(dataset) == 1):
                try:
                    response = self.gptclient.images.generate(
                        model="sdxl",
                        prompt=params["message"].replace(".image", "", 1),
                    )
                except Exception as e:
                    blacklick_content = e
                    dataset["send_type"] = "message"
                    params["message"] = blacklick_content
                    return self.processor(dataset, params, message_object)

                image_url = response.data[0].url
                image_data = requests.get(image_url)
                filename = str(time.time()).replace(".", "")
                response = f"Here your image with requests \"{params['message'].replace('.image', '', 1)}\"",
                with open(f"dataset/media/{filename}.png", "wb") as file:
                    file.write(image_data.content)
                try:
                    sending = self.sendLocalImage(
                        imagePath = f"dataset/media/{filename}.png",
                        thread_id = self.aim_id,
                        message = Message(
                            text = response,
                            style = MultiMsgStyle([
                                MessageStyle(offset=0, length=len(response) + 10**3, style = "bold", auto_format=False),
                                MessageStyle(offset=0, length=len(response) + 10**3, style = "font", size="10", auto_format=False)
                            ])
                        ),
                        thread_type =ThreadType.GROUP,    
                    )
                except Exception as e:
                    print(e)
                os.remove(f"dataset/media/{filename}.png")
                self.botmemory.append(str(sending["msgId"]))

        elif dataset["send_type"] == "message":
            if (self.gpt_mode) and (str(message_object["msgId"]) not in self.botmemory) and (message_object["idTo"] == self.aim_id) and (message_object["msgType"] == "webchat") and (len(dataset) == 1):

                if True:
                    response = self.gptclient.chat.completions.create(
                        model="gpt-4o-mini",#"gpt-3.5-turbo",
                        messages=[{"role": "user", "content": params["message"]}],
                        api_key=self.apikey
                    )
                    response = response.choices[0].message.content
                    sending = self.replyMessage(
                        message = Message(
                            text = response,
                            style = MultiMsgStyle([
                                MessageStyle(offset=0, length=len(response), style = "bold", auto_format=False),
                                MessageStyle(offset=0, length=len(response), style = "font", size="10", auto_format=False)
                            ])
                        ),
                        replyMsg = message_object,
                        thread_id = self.aim_id,
                        thread_type = ThreadType.GROUP
                    )
                    self.botmemory.append(str(sending["msgId"]))
                

            if str(message_object["msgId"]) not in self.botmemory:
                if dataset["mention"]:
                    pass
                self.replyMessage(
                    message = Message(
                        text = dataset["message"],
                        style = MultiMsgStyle(self.create_message_style_v1(dataset["message"])),
                    ),
                    replyMsg = message_object,
                    thread_id = self.aim_id,
                    thread_type = ThreadType.GROUP,
                )

    def create_message_style_v1(self, text: str):# auto format / highlight text to send to group/user (version : 1) 
        """
        format : string1 : string2\n
        """
        lines = text.split("\n")
        lines.pop(-1)
        styles = []
        offset = 0
        for line in lines:
            parts = line.split(" : ")
            styles.append(MessageStyle(offset=offset, length=len(parts[0]), style="lineheader", auto_format=False))
            styles.append(MessageStyle(offset=offset, length=len(parts[0]), style="bold", auto_format=False))
            styles.append(MessageStyle(offset=offset, length=len(parts[0]), style="color", color="f7b503", auto_format=False))
            styles.append(MessageStyle(offset=offset + len(parts[0]) + 3, length=len(parts[1]), style="bold", auto_format=False))
            styles.append(MessageStyle(offset=offset + len(parts[0]) + 3, length=len(parts[1]), style="italic", auto_format=False))
            styles.append(MessageStyle(offset=offset + len(parts[0]) + 3, length=len(parts[1]), style="color", color="db342e", auto_format=False))
            offset += len(line) + 1
        styles.append(MessageStyle(offset=0, length=len(text), style="font", size="10", auto_format=False))
            
        return styles

    def features_monitor(self, message_object, dataset):# some action about monitor mode (archive message, undo action, anti spam,...)
        global message_data
        # print(message_data, message_object)
        target_id = dataset["author_id"]
        if target_id not in message_data:
            message_data[target_id] = {
                "name" : self.fetchUserInfo(target_id)["changed_profiles"][str(target_id)]["zaloName"],
                "content" : {}
            }
        print("archive")
        type = message_object["msgType"]
        timestamp = int(message_object["cliMsgId"])/1000

        #################### START ARCHIVE MESSAGE ########################
        if type == "webchat":
            message_data[target_id]["content"][dataset["mid"]] = {
                "type" : "message",
                "content" : message_object["content"],
                "timestamp" : timestamp,
                "cliMsgId" : message_object["cliMsgId"]
            }
        elif type == "chat.photo":
            message_data[target_id]["content"][dataset["mid"]] = {
                "type" : "photo",
                "title" : message_object["content"]["title"],
                "description" : message_object["content"]["descrtiption"],
                "content" : message_object["content"]["href"],
                "timestamp" : timestamp,
                "cliMsgId" : message_object["cliMsgId"]
            }
        elif type == "chat.video.msg":
            message_data[target_id]["content"][dataset["mid"]] = {
                "type" : "video",
                "title" : message_object["content"]["title"],
                "description" : message_object["content"]["descrtiption"],
                "content" : message_object["content"]["href"],
                "timestamp" : timestamp,
                "cliMsgId" : message_object["cliMsgId"]
            }
        elif type == "share.file":
            message_data[target_id]["content"][dataset["mid"]] = {
                "type" : "file",
                "title" : message_object["content"]["title"],
                "description" : message_object["content"]["descrtiption"],
                "content" : message_object["content"]["href"],
                "timestamp" : timestamp,
                "cliMsgId" : message_object["cliMsgId"]
            }
        elif type == "chat.voice":
            message_data[target_id]["content"][dataset["mid"]] = {
                "type" : "voice",
                "title" : message_object["content"]["title"],
                "description" : message_object["content"]["descrtiption"],
                "content" : json.loads(message_object["content"]["params"])["m4a"],
                "timestamp" : timestamp,
                "cliMsgId" : message_object["cliMsgId"]
            }
            
        #################### END ARCHIVE MESSAGE ########################

        message_data[target_id]["spamdata"] = {
            "status" : False,
            "mps" : math.inf,
        }#create anti spam data
        
        maxium = 5 #maxium message on one list
        rate = 5 #minium times average
        
        #anti spam
        if len(message_data[target_id]["content"]) > maxium: #check if total message reach to maxium
            try:
                time_list = [] #create time list to archive timestamp -> calculate message per second
                for id_chat in message_data[target_id]["content"]: #archive code
                    time_list.append(message_data[target_id]["content"][id_chat]["timestamp"])
                time_list = list(map(float, time_list)) 
                time_list = sorted(time_list, reverse = True) #sorted timestamp
                average = []
                for index in range(maxium - 1): #calculate
                    average.append(abs(time_list[index] - time_list[index+1]))
                average = sum(average) / len(average) #average of second

                if average <= rate: #detected spam
                    for id_chat in message_data[target_id]["content"]: #deleted spam message
                        self.deleteGroupMsg(
                            msgId       = id_chat,
                            groupId     = self.aim_id,
                            ownerId     = message_object["uidFrom"],
                            clientMsgId = message_data[target_id]["content"][id_chat]["cliMsgId"],
                        )

                    #set flag to spam
                    message_data[target_id]["spamdata"]["status"] = True
                    message_data[target_id]["spamdata"]["mps"] = average
                    
                    #make log
                    returnText = f"User : {message_data[target_id]['name']}\nWarning : Spam detected\nMps : {round(average, 2)}\n"

                    #sending log
                    self.sendMessage(
                        message= Message(
                            text= returnText,
                            style=MultiMsgStyle(self.create_message_style_v1(returnText)),
                        ),
                        thread_id = self.aim_id,
                        thread_type= ThreadType.GROUP,
                    ) 

                    message_data[target_id]["content"] = {}
                    message_data[target_id]["spamdata"]["status"] = False
                    message_data[target_id]["spamdata"]["mps"] = average

                    if target_id not in self.warning_dataset: #warning user (plus the count)
                        self.warning_dataset[target_id] = {
                            "count" : 1,
                        }

                    else:
                        self.warning_dataset[target_id]["count"] += 1
                    #save data for reruning
                    open("warning.json", "w", encoding = "utf-8").write(json.dumps(self.warning_dataset))
            
            except Exception as e: #debug lol
                print(e)

        #undo recived
        if type == "chat.undo":
            try:
                dt_object = datetime.fromtimestamp(int(message_object["cliMsgId"])/1000)
                if message_object["idTo"] != "0":
                    save_memory_id = "globalMsgId"
                else:
                    save_memory_id = "cliMsgId"
                undo_timestamp = dt_object.strftime("%d/%m/%Y | %H:%M:%S")
                undo_content = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["content"]
                send_type = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["type"]
                from_user = message_data[target_id]["name"]
                from_group = self.idmap[str(message_object["idTo"])]

                send_text = {
                    "Title" : "MONITOR UNDO MESSAGE",
                    "Date" : undo_timestamp,
                    "From user" : from_user,
                    "From group" : from_group,
                    "Action" : "Undo",
                    "Type" : send_type,
                }

                if send_type == "message":
                    send_text["Content"] = undo_content
                elif send_type == "photo":
                    send_text["Photo"] = undo_content
                    send_text["Caption"] = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["title"]
                    send_text["Description"] = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["description"]
                elif send_type == "video":
                    send_text["Video"] = undo_content
                    send_text["Caption"] = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["title"]
                    send_text["Description"] = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["description"]
                elif send_type == "file":
                    send_text["File"] = undo_content
                    send_text["Caption"] = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["title"]
                    send_text["Description"] = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["description"]
                elif send_type == "voice":
                    send_text["Voice"] = undo_content
                    send_text["Caption"] = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["title"]
                    send_text["Description"] = message_data[target_id]["content"][str(message_object["content"][save_memory_id])]["description"]
                
                
                trueText = ""
                for i in send_text:
                    if i == "title":
                        trueText += send_text[i] + "\n"
                        continue
                    trueText += f"{i} : {send_text[i]}\n"
                
                try:
                    message_data[target_id]["content"].pop(str(message_object["content"]["globalMsgId"]))
                except:
                    pass

                if message_object["idTo"] != self.cloudid:
                    style = self.create_message_style_v1(trueText)
                    self.sendMessage(
                        message= Message(
                            text=trueText,
                            style=MultiMsgStyle(style),
                        ),
                        thread_id = self.aim_id,
                        thread_type= ThreadType.GROUP,
                    )    
                    self.sendMessage(
                        message= Message(
                            text=trueText,
                            style=MultiMsgStyle(style),
                        ),
                        thread_id = self.cloudid,
                        thread_type= ThreadType.USER
                    )    

            except Exception as e:
                print(e)
        

    def features(self, object = None, dataset: dict = {}):
        message = str(dataset["message"]) 

        if self.gpt_mode and message == ".gptoff":
            self.gpt_mode = False
            self.sendMessage(
                message = Message(
                    text="GPT mode : off",
                    style=MultiMsgStyle(self.create_message_style_v1("GPT mode : off\n"))
                ),
                thread_id = self.aim_id,
                thread_type = ThreadType.GROUP                
            )
            return
        if not self.gpt_mode and message == ".gpton":
            try:
                self.gpt_mode = True
                sending = self.sendMessage(
                    message = Message(
                        text="GPT mode : on",
                        style=MultiMsgStyle(self.create_message_style_v1("GPT mode : on\n"))
                    ),
                    thread_id = self.aim_id,
                    thread_type = ThreadType.GROUP                
                )
                self.botmemory.append(str(sending["msgId"]))
            except Exception as e:
                print(e)
            return
        
        if not self.monitor_mode and message == ".monitoron":
            try:
                self.monitor_mode = True
                sending = self.sendMessage(
                    message = Message(
                        text="Monitor mode : on",
                        style=MultiMsgStyle(self.create_message_style_v1("Monitor mode : on\n"))
                    ),
                    thread_id = self.cloudid,
                    thread_type = ThreadType.USER                
                )
            except Exception as e:
                print(e)
            return
        
        if self.monitor_mode and message == ".monitoroff":
            try:
                self.monitor_mode = False
                sending = self.sendMessage(
                    message = Message(
                        text="Monitor mode : off",
                        style=MultiMsgStyle(self.create_message_style_v1("Monitor mode : off\n"))
                    ),
                    thread_id = self.cloudid,
                    thread_type = ThreadType.USER
                )
            except Exception as e:
                print(e)
            return
            
        
        if self.monitor_mode:
            self.features_monitor(message_object=object, dataset=dataset)
        
        if (message in self.command):
            return self.processor(self.command[message], dataset, object)
        
        if self.gpt_mode:
            # .image cat
            print(object)
            if message[:6] == ".image":
                try:
                    response = "Đang tạo ảnh theo yêu cầu, vui lòng chờ..."
                    reply = self.replyMessage(
                        message = Message(
                            text = response,
                            style = MultiMsgStyle(
                                [
                                    MessageStyle(offset=0, length=len(response), style = "bold", auto_format=False),
                                    MessageStyle(offset=0, length=len(response), style = "font", size="10", auto_format=False)
                                ]
                            )
                        ),
                        replyMsg = object,
                        thread_id = self.aim_id,
                        thread_type = ThreadType.GROUP,
                        ttl = 10000,
                    )
                except Exception as e:
                    print("[ Error in function \"feature\", in .image code] : ", e)
                return self.processor({"send_type":"image"}, dataset, object)
            self.processor({"send_type":"message"}, dataset, object)
        


    def onEvent(self, event_data, event_type):
        print(event_data, event_type)
        pass
    
    def onHandle(self, mid, author_id, message, message_object, thread_id, thread_type):
        if author_id == self.account_id:
            return
        
        if not self.monitor_mode:
            self.markAsDelivered(mid, message_object.cliMsgId, author_id, thread_id, thread_type, message_object.msgType)
            self.markAsRead(mid, message_object.cliMsgId, author_id, thread_id, thread_type, message_object.msgType)
        
        message_from_id = message_object["idTo"]
        if (message_from_id != self.aim_id) and (not self.monitor_mode): #nếu tin nhắn không nằm trong nhóm đang aim và monitor mode chưa được bật: cho cút
            return
        
        return self.features(
            object = message_object,
            dataset = {
                "thread_id" : thread_id,
                "thread_type" : thread_type,
                "mid" : mid,
                "author_id" : author_id,
                "message" : message
            }
        )

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        thread.submit(
            self.onHandle, mid, author_id, message, message_object, thread_id, thread_type 
        )

    def listen_group(self):
        os.system("cls") if os.name == "nt" else os.system("clear")
        if self.aim_id != "MONITOR MODE":
            print(f"{red}[ {cyan}LISTENING {red}] {white}| {red}[ {yellow}ID {white}: {green}{self.aim_id} {red}] {white}| {red}[ {yellow}NAME {white}: {green}{self.groupinfo['gridInfoMap'][self.aim_id]['name']} {red}]")
        else:
            print(f"{red}[ {cyan}LISTENING {red}] {white}| {red}[ {yellow}ID {white}: {green}{self.aim_id} {red}] {white}| {red}[ {yellow}NAME {white}: {green}MONITOR MODE {red}]")
        
        self.listen(
            thread = self.dataset["thread"],
            type = self.dataset["type"],
            run_forever = self.dataset["runforever"],
        )

class main:
    def __init__(self):
        dataset = main.fetch_client_data() #fetch data from config.json file
        self.imei = dataset["imei"] #set requiment params
        self.cookies = dataset["cookies"] #set requiment params
        self.phone = dataset["phone"] #set requiment params
        self.password = dataset["password"] #set requiment params

        self.botclient = Hnglbot(
            phone=self.phone,
            password=self.password,
            imei=self.imei,
            session_cookies=self.cookies,
        ) #generate bot session (important)
        
        self.botclient.fetch_group()
        self.botclient.listen_group()

    @staticmethod
    def fetch_client_data(): #easy to understand
        return json.loads(open("config.json", "r", encoding="utf-8").read())
    

if __name__ == "__main__": 
    os.system("cls") if os.name == "nt" else os.system("clear")
    try:
        main()
    except Exception as e:
        print(f"{red}[ {white}ERROR {red}] {white}: {red}{e}!{white}")