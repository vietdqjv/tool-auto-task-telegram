# Design Guidelines - Telegram Bot Interface

## Bot Identity

### Name & Description
- **Bot Name**: Task Automation Bot
- **Username**: `@task_auto_bot` (customize when creating)
- **Description**: Multi-purpose automation tool for task scheduling, reminders, and API integrations

### Bot Profile
- Use a simple, recognizable icon (robot/automation theme)
- Keep bio under 120 characters

## Message Formatting

### Text Styles
```
*bold* - Important info, headers
_italic_ - Emphasis, notes
`code` - Commands, values, IDs
```pre``` - Code blocks, logs
```

### Emoji Usage (sparingly)
- Success/Done
- Error/Failed
- Warning
- Info/Tip
- Task/Todo
- Schedule/Time
- Settings

## Command Structure

### Naming Convention
- Use lowercase, no underscores: `/start`, `/help`, `/newtask`
- Keep commands short (max 15 chars)
- Use intuitive names: `/list`, `/add`, `/delete`

### Core Commands
| Command | Description |
|---------|-------------|
| `/start` | Welcome + quick guide |
| `/help` | Command list + usage |
| `/tasks` | List all tasks |
| `/add` | Create new task |
| `/delete` | Remove task |
| `/remind` | Set reminder |
| `/status` | Bot status |
| `/settings` | User preferences |

## Keyboard Layouts

### Inline Keyboards
- Max 3 buttons per row
- Use short labels (1-3 words)
- Include cancel/back option
- Pattern: `[Action] [Cancel]`

### Reply Keyboards
- Use for frequent actions
- Max 2 rows x 3 columns
- Always include `/cancel` option

## Message Templates

### Welcome Message
```
Task Automation Bot

Commands:
/tasks - View tasks
/add - Create task
/remind - Set reminder
/help - All commands

Type /add to get started!
```

### Success Response
```
Task created successfully!

Title: {title}
Due: {due_date}
ID: `{task_id}`

Use /tasks to view all tasks.
```

### Error Response
```
Unable to process request.

Reason: {error_message}

Try again or use /help for assistance.
```

### Confirmation Prompt
```
Delete task "{title}"?

This action cannot be undone.

[Yes, Delete] [Cancel]
```

## Conversation Flow

### Multi-step Forms
1. Ask one question at a time
2. Show progress: "Step 1/3"
3. Allow `/cancel` at any point
4. Confirm before final action

### State Handling
- Timeout after 5 min inactivity
- Clear message when timeout
- Auto-cancel incomplete forms

## Response Times

### Feedback
- Show "typing..." for operations >1s
- Immediate acknowledgment for long tasks
- Progress updates for batch operations

### Messages
- Keep responses under 300 chars when possible
- Use inline buttons instead of long text
- Paginate lists (max 10 items)

## Accessibility

### Text
- Use clear, simple language
- Avoid jargon
- Support both text commands and buttons

### Localization Ready
- Externalize all strings
- Use placeholders for dynamic content
- Support Vietnamese and English
