# src/bot/handlers/dm-task-fsm.py
"""FSM handlers for task operations in DM. No timeout - user controls via /cancel."""
import importlib
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from zoneinfo import ZoneInfo
from src.core.config import settings

TIMEZONE = ZoneInfo(settings.TIMEZONE)
dm_task_fsm_router = Router(name="dm_task_fsm")

# FSM STATES
class NewTaskFSM(StatesGroup):
    title, description, deadline, confirm = State(), State(), State(), State()

class EditTaskFSM(StatesGroup):
    select_field, edit_value, confirm = State(), State(), State()

class BulkTaskFSM(StatesGroup):
    input_tasks, confirm = State(), State()

# KEYBOARDS
def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Xac nhan", callback_data=f"dm_confirm_{action}"),
        InlineKeyboardButton(text="Huy", callback_data="dm_cancel")
    ]])

def get_skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Bo qua", callback_data="dm_skip")]
    ])

def get_edit_field_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tieu de", callback_data="dm_edit_title"),
         InlineKeyboardButton(text="Deadline", callback_data="dm_edit_deadline")],
        [InlineKeyboardButton(text="Huy", callback_data="dm_cancel")]
    ])

def _parse_deadline(text: str):
    for fmt in ["%d/%m %H:%M", "%d/%m/%Y %H:%M"]:
        try:
            dt = datetime.strptime(text.strip(), fmt)
            if "%Y" not in fmt:
                dt = dt.replace(year=datetime.now().year)
            return dt.replace(tzinfo=TIMEZONE)
        except ValueError:
            continue
    return None

# CANCEL HANDLERS
@dm_task_fsm_router.callback_query(F.data == "dm_cancel")
async def cancel_dm_fsm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Da huy.")
    await callback.answer()

@dm_task_fsm_router.message(F.text == "/cancel", F.chat.type == "private")
async def cmd_cancel_dm(message: Message, state: FSMContext):
    if await state.get_state():
        await state.clear()
        await message.answer("Da huy thao tac.")
    else:
        await message.answer("Khong co thao tac nao dang cho.")

# NEW TASK HANDLERS
@dm_task_fsm_router.message(NewTaskFSM.title, F.chat.type == "private")
async def process_newtask_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 3:
        return await message.answer("Tieu de phai co it nhat 3 ky tu.")
    if len(title) > 255:
        return await message.answer("Tieu de qua dai (toi da 255 ky tu).")
    await state.update_data(title=title)
    await state.set_state(NewTaskFSM.description)
    await message.answer("<b>Buoc 2/3:</b> Nhap mo ta (hoac bam Bo qua):",
                         reply_markup=get_skip_keyboard(), parse_mode="HTML")

@dm_task_fsm_router.callback_query(NewTaskFSM.description, F.data == "dm_skip")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description=None)
    await state.set_state(NewTaskFSM.deadline)
    await callback.message.edit_text(
        "<b>Buoc 3/3:</b> Nhap deadline:\nDinh dang: DD/MM HH:MM\nVi du: 25/12 17:00", parse_mode="HTML")
    await callback.answer()

@dm_task_fsm_router.message(NewTaskFSM.description, F.chat.type == "private")
async def process_newtask_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(NewTaskFSM.deadline)
    await message.answer("<b>Buoc 3/3:</b> Nhap deadline:\nDinh dang: DD/MM HH:MM\nVi du: 25/12 17:00", parse_mode="HTML")

@dm_task_fsm_router.message(NewTaskFSM.deadline, F.chat.type == "private")
async def process_newtask_deadline(message: Message, state: FSMContext):
    due_date = _parse_deadline(message.text)
    if not due_date:
        return await message.answer("Dinh dang khong hop le. Dung: DD/MM HH:MM")
    if due_date <= datetime.now(TIMEZONE):
        return await message.answer("Deadline phai o tuong lai.")
    await state.update_data(due_date=due_date.isoformat())
    await state.set_state(NewTaskFSM.confirm)
    data = await state.get_data()
    deadline_str = due_date.strftime("%d/%m/%Y %H:%M")
    await message.answer(
        f"<b>Xac nhan tao task:</b>\n\n<b>Tieu de:</b> {data['title']}\n"
        f"<b>Mo ta:</b> {data.get('description') or 'Khong co'}\n<b>Deadline:</b> {deadline_str}",
        reply_markup=get_confirm_keyboard("newtask"), parse_mode="HTML")

@dm_task_fsm_router.callback_query(NewTaskFSM.confirm, F.data == "dm_confirm_newtask")
async def confirm_newtask(callback: CallbackQuery, state: FSMContext, bot: Bot, session):
    gts = importlib.import_module("src.services.group-task-service")
    data = await state.get_data()
    service = gts.GroupTaskService(session)
    due_date = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
    try:
        task = await service.create_group_task(
            group_id=data["source_group_id"], title=data["title"],
            assignee_id=data["creator_id"], assigned_by_id=data["creator_id"],
            description=data.get("description"), due_date=due_date)
        await session.commit()
        await callback.message.edit_text(f"Task da tao!\n<b>ID:</b> {task.id}\n<b>{task.title}</b>", parse_mode="HTML")
        await _notify_source_group(bot, data["source_group_id"], "newtask", task, callback.from_user)
        await callback.answer("Task da tao!")
    except Exception as e:
        await session.rollback()
        await callback.message.edit_text(f"Loi: {e}")
        await callback.answer()
    await state.clear()

# EDIT TASK HANDLERS
@dm_task_fsm_router.callback_query(EditTaskFSM.select_field, F.data.startswith("dm_edit_"))
async def process_edit_field_selection(callback: CallbackQuery, state: FSMContext):
    field = callback.data.replace("dm_edit_", "")
    await state.update_data(edit_field=field)
    await state.set_state(EditTaskFSM.edit_value)
    msg = "Nhap tieu de moi:" if field == "title" else "Nhap deadline moi:\nDinh dang: DD/MM HH:MM"
    await callback.message.edit_text(msg)
    await callback.answer()

@dm_task_fsm_router.message(EditTaskFSM.edit_value, F.chat.type == "private")
async def process_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("edit_field")
    if field == "title":
        title = message.text.strip()
        if len(title) < 3:
            return await message.answer("Tieu de phai co it nhat 3 ky tu.")
        await state.update_data(new_title=title)
        confirm_text = f"<b>Xac nhan sua tieu de:</b>\n{title}"
    else:
        due_date = _parse_deadline(message.text)
        if not due_date or due_date <= datetime.now(TIMEZONE):
            return await message.answer("Deadline khong hop le hoac khong o tuong lai.")
        await state.update_data(new_deadline=due_date.isoformat())
        confirm_text = f"<b>Xac nhan sua deadline:</b>\n{due_date.strftime('%d/%m/%Y %H:%M')}"
    await state.set_state(EditTaskFSM.confirm)
    await message.answer(confirm_text, reply_markup=get_confirm_keyboard("edittask"), parse_mode="HTML")

@dm_task_fsm_router.callback_query(EditTaskFSM.confirm, F.data == "dm_confirm_edittask")
async def confirm_edittask(callback: CallbackQuery, state: FSMContext, bot: Bot, session):
    gts = importlib.import_module("src.services.group-task-service")
    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await callback.message.edit_text("Loi: Khong tim thay task ID.")
        await state.clear()
        return await callback.answer()
    try:
        service = gts.GroupTaskService(session)
        task = await service.get_task(task_id)
        if not task:
            await callback.message.edit_text("Task khong ton tai.")
            await state.clear()
            return await callback.answer()
        if data.get("edit_field") == "title":
            task.title = data["new_title"]
        else:
            task.due_date = datetime.fromisoformat(data["new_deadline"])
        await session.commit()
        await callback.message.edit_text(f"Task da cap nhat!\n<b>ID:</b> {task.id}\n<b>{task.title}</b>", parse_mode="HTML")
        await _notify_source_group(bot, data["source_group_id"], "edittask", task, callback.from_user)
        await callback.answer("Task da cap nhat!")
    except Exception as e:
        await session.rollback()
        await callback.message.edit_text(f"Loi: {e}")
        await callback.answer()
    await state.clear()

# BULK TASK HANDLERS
@dm_task_fsm_router.message(BulkTaskFSM.input_tasks, F.chat.type == "private")
async def process_bulk_input(message: Message, state: FSMContext):
    lines = [l.strip() for l in message.text.strip().split("\n") if l.strip() and len(l.strip()) >= 3]
    if not lines:
        return await message.answer("Nhap it nhat 1 task (moi task >= 3 ky tu).")
    await state.update_data(bulk_tasks=lines)
    await state.set_state(BulkTaskFSM.confirm)
    task_list = "\n".join([f"  {i+1}. {t}" for i, t in enumerate(lines)])
    await message.answer(f"<b>Xac nhan tao {len(lines)} task:</b>\n\n{task_list}",
                         reply_markup=get_confirm_keyboard("bulktask"), parse_mode="HTML")

@dm_task_fsm_router.callback_query(BulkTaskFSM.confirm, F.data == "dm_confirm_bulktask")
async def confirm_bulktask(callback: CallbackQuery, state: FSMContext, bot: Bot, session):
    gts = importlib.import_module("src.services.group-task-service")
    data = await state.get_data()
    service = gts.GroupTaskService(session)
    tasks = data.get("bulk_tasks", [])
    try:
        for title in tasks:
            await service.create_group_task(
                group_id=data["source_group_id"], title=title,
                assignee_id=data["creator_id"], assigned_by_id=data["creator_id"])
        await session.commit()
        await callback.message.edit_text(f"Da tao {len(tasks)} task!")
        await bot.send_message(data["source_group_id"],
            f"<b>{callback.from_user.mention_html()}</b> da tao {len(tasks)} task moi.", parse_mode="HTML")
        await callback.answer(f"Da tao {len(tasks)} task!")
    except Exception as e:
        await session.rollback()
        await callback.message.edit_text(f"Loi: {e}")
        await callback.answer()
    await state.clear()

# GROUP NOTIFICATION
async def _notify_source_group(bot: Bot, group_id: int, action: str, task, user):
    action_text = {"newtask": "tao", "edittask": "cap nhat"}
    try:
        await bot.send_message(group_id,
            f"Task da duoc {action_text.get(action, 'xu ly')}!\n\n<b>{task.title}</b>\nBoi: {user.mention_html()}",
            parse_mode="HTML")
    except Exception:
        pass
