from fastapi import FastAPI, Request, HTTPException

@app.post("/callback")
async def new_day_call():
    pass
    
@app.post("/callback")
async def callback(request: Request):
    body = await request.json()
    events = body.get('events', [])

    for event in events:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            text = event['message']['text']
            reply_token = event['replyToken']
            group_id = event['source'].get('groupId')

            if not group_id:
                await reply_message(reply_token, "請在群組中使用指令喔！")
                continue

            todos = load_todos()
            todos.setdefault(group_id, [])

            if text.startswith('/add '):
                task = text[5:].strip()
                todos[group_id].append(task)
                save_todos(todos)
                await reply_message(reply_token, f"已新增待辦事項：{task}")

            elif text == '/list':
                if not todos[group_id]:
                    await reply_message(reply_token, "目前沒有待辦事項。")
                else:
                    todo_list = '\n'.join([f"{idx+1}. {item}" for idx, item in enumerate(todos[group_id])])
                    await reply_message(reply_token, f"目前待辦事項：\n{todo_list}")

            elif text.startswith('/delete '):
                try:
                    idx = int(text.split(' ')[1]) - 1
                    if 0 <= idx < len(todos[group_id]):
                        removed = todos[group_id].pop(idx)
                        save_todos(todos)
                        await reply_message(reply_token, f"已刪除：{removed}")
                    else:
                        await reply_message(reply_token, "無效的編號！")
                except:
                    await reply_message(reply_token, "格式錯誤！使用：/delete 編號")
            else:
                await reply_message(reply_token, "指令不明！可用指令：/add 事項, /list, /delete 編號")

    return {"status": "ok"}