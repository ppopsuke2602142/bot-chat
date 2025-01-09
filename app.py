from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = '4FQh/agWm1UzEWeUSud+or4blbGIS423Y2vK0RveR4Ozlg9bb5JZosyxvsfMB9TsHFnjVMpfjOwO+mC66/6++yTJrj7sPrlsOo/4XxcgDcR4yffZY/nKFw8x+9WN8R24OWww3C6cxi//lMBzDkGdlgdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'cacdf50f6db26a04128efda01f19ae00'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Task List (เก็บข้อมูลในหน่วยความจำ)
task_list = [
    {"id": 1, "task": "download file", "done": False},
    {"id": 2, "task": "A1.5", "done": False},
    {"id": 3, "task": "A1.6", "done": False},
    {"id": 4, "task": "F1", "done": False},
    {"id": 5, "task": "F1.6", "done": False},
    {"id": 6, "task": "F1.8", "done": False},
    {"id": 7, "task": "F3", "done": False},
]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# ฟังก์ชันช่วยแปลง Task List เป็นข้อความ
def format_task_list():
    if not task_list:
        return "ไม่มีงานใน Task List"
    result = "รายการงาน:\n"
    for task in task_list:
        status = "✅" if task["done"] else "❌"
        result += f'{task["id"]}. {task["task"]} [{status}]\n'
    return result

# ฟังก์ชันแจ้งเตือนทุกวันจันทร์
def send_monday_reminder():
    try:
        message = "อย่าลืมโหลดไฟล์ Order 🚀"
        # ส่งข้อความไปยังผู้ใช้หรือกลุ่ม (ใช้ User ID หรือ Group ID)
        line_bot_api.broadcast(TextSendMessage(text=message))
        print(f"[{datetime.datetime.now()}] Reminder sent successfully.")
    except Exception as e:
        print(f"Error sending reminder: {e}")

# ตั้ง Scheduler สำหรับแจ้งเตือน
scheduler = BackgroundScheduler()
scheduler.add_job(send_monday_reminder, 'cron', day_of_week='mon', hour=9, minute=0)  # ทุกวันจันทร์ เวลา 9:00 น.
scheduler.start()

# นิยามฟังก์ชันตรวจสอบ Task
def check_all_tasks_completed():
    # ตรวจสอบว่า task_list ทุกงานมีสถานะ `done` เป็น True หรือไม่
    return all(task["done"] for task in task_list)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip().lower()

    if user_message == "list task":
        reply = format_task_list()
    elif user_message.startswith("done"):
        try:
            task_id = int(user_message.split()[1])
            for task in task_list:
                if task["id"] == task_id:
                    task["done"] = True
                    reply = f'งาน "{task["task"]}" เสร็จแล้ว! 🎉'
                    
                    # เรียกใช้ฟังก์ชันตรวจสอบสถานะ Task ทั้งหมด
                    if check_all_tasks_completed():
                        reply += "\n\n🎉 Order complete ✅"
                    break
            else:
                reply = f"ไม่พบงานที่มีหมายเลข {task_id}"
        except (IndexError, ValueError):
            reply = "โปรดระบุหมายเลขงานที่ต้องการทำเครื่องหมาย เช่น: done 1"
    else:
        reply = "คำสั่งที่ใช้ได้:\n- list task\n- add task <งาน>\n- done <หมายเลข>\n- delete task <หมายเลข>"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
