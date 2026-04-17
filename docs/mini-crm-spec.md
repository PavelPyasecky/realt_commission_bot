# Mini CRM for Realtor - Technical Specification

## 1. Objective

Add a super-minimal CRM module to the existing Telegram bot so a realtor can:

- create leads manually inside the bot
- auto-create a lead from a forwarded Telegram message
- edit a lead directly inside the bot
- change lead status using buttons
- set a reminder for the next call using buttons
- receive reminder notifications in Telegram and resolve them in one tap

The CRM must stay minimal, fast, and clean. The current commission calculator must remain available and unchanged.

## 2. Product Constraints

Current project constraints:

- the application is a Telegram bot, not a web app
- there is no database yet
- there is no persisted CRM state yet
- there are no callback/button-based flows yet

Because of Telegram platform limitations, silent lead creation from inline mode in a client chat is not the primary flow. The MVP must use forwarded-message capture and in-bot management.

## 3. Product Principles

- one screen = one main action
- all routine actions are button-first
- no deep navigation
- no overloaded text blocks
- no kanban, analytics, or advanced CRM objects in MVP
- one active reminder per lead
- overdue and today reminders are always surfaced first

## 4. MVP Scope

### Included

- main CRM menu inside the bot
- manual lead creation inside the bot
- auto lead creation from a forwarded message
- lead list
- lead card
- lead editing inside the bot
- status changes via buttons
- one active reminder per lead
- today and overdue reminder views
- reminder notifications with quick actions
- archive and restore lead actions

### Excluded

- web panel
- multi-user team support
- notes history feed
- tags
- kanban board
- analytics and dashboards
- telephony integration
- export/import
- multiple reminders per lead
- complex date-time picker

## 5. Core User Scenarios

### Scenario A - Auto-create lead from forwarded message

1. Realtor opens the bot
2. Realtor taps `CRM`
3. Realtor taps `Add from Forwarded Message`
4. Bot asks the realtor to forward a client message
5. Realtor forwards a message from a Telegram user
6. Bot auto-creates a lead draft from the forwarded message
7. Bot returns a compact lead card with action buttons
8. Realtor optionally adjusts type, source, status, or reminder

This flow must not send anything to the client chat. All activity stays inside the realtor-bot conversation.

### Scenario B - Manual lead creation inside the bot

1. Realtor opens `CRM`
2. Taps `Add Lead`
3. Enters or selects required fields
4. Saves the lead
5. Immediately sets the first reminder via buttons

### Scenario C - Edit lead inside the bot

1. Realtor opens a lead card
2. Taps `Edit`
3. Chooses which field to update
4. Changes the value
5. Returns to the updated lead card

### Scenario D - Reminder handling

1. Bot sends reminder notification when the scheduled time arrives
2. Realtor taps one action:
   - `Call Done`
   - `+1 hour`
   - `Tomorrow`
   - `Change Status`
   - `Open Lead`

## 6. Main Navigation

## Main Menu

Buttons:

- `Commission Calculator`
- `CRM`

## CRM Menu

Buttons:

- `Add Lead`
- `Add from Forwarded Message`
- `Today`
- `All Leads`
- `Archived`
- `Back`

## 7. Lead Data Model

## Required Fields

- `id`
- `name`
- `phone`
- `telegram_user_id`
- `telegram_username`
- `telegram_display_name`
- `lead_type`
- `source`
- `status`
- `next_call_at`
- `last_contact_at`
- `created_at`
- `updated_at`
- `is_archived`

## Optional / Derived Fields

- `capture_method` - `manual` or `forwarded_message`
- `forwarded_from_message_date`
- `last_reminder_sent_at`

## 8. Lead Types

Buttons:

- `Buyer`
- `Seller`
- `Tenant`
- `Landlord`
- `Investor`
- `Unknown`

## 9. Lead Sources

Buttons:

- `Telegram`
- `Referral`
- `Ads`
- `Website`
- `Repeat`
- `Other`

## 10. Lead Statuses

Buttons:

- `New`
- `Contacted`
- `Meeting Planned`
- `Negotiation`
- `Won`
- `Lost`
- `Paused`

This status set is intentionally short so the realtor can update a lead in one or two taps.

## 11. Reminder Rules

- only one active reminder per lead
- reminder is the next required contact action
- reminder can be changed or removed from the lead card
- overdue reminders must appear before today reminders

## Reminder Presets

Buttons:

- `In 1 hour`
- `Today 18:00`
- `Tomorrow 10:00`
- `In 3 days`
- `Next week`
- `Remove reminder`

## 12. Lead Auto-Creation from Forwarded Message

### Goal

Create a lead in one action without exposing CRM activity to the client.

### Trigger

The realtor forwards a message from a client to the bot after tapping `Add from Forwarded Message`.

### Bot Behavior

When a forwarded message is received, the bot must:

1. validate that the message contains forward metadata or sender information usable for lead creation
2. create a lead immediately
3. prefill the lead from available Telegram data
4. mark `source = Telegram`
5. mark `status = New`
6. mark `capture_method = forwarded_message`
7. return the created lead card with quick action buttons

### Auto-Filled Fields

- `telegram_user_id` if available
- `telegram_username` if available
- `telegram_display_name`
- `source = Telegram`
- `status = New`
- `created_at`
- `capture_method = forwarded_message`

### Name Resolution

Priority:

1. forwarded Telegram display name
2. username
3. generated fallback name, for example `Telegram Lead #124`

### Phone Resolution

Phone is not guaranteed from a forwarded Telegram message.

If phone is missing:

- create the lead anyway
- show button `Add Phone`
- do not block creation

### Duplicate Detection

Before creating a new lead, the bot must check:

- `telegram_user_id`
- then `telegram_username`
- then normalized `name + source` fallback

If a probable duplicate exists, the bot must show:

- `Open Existing`
- `Create Anyway`
- `Cancel`

### Failure Cases

If forwarded data is insufficient for safe lead creation:

- bot creates a draft lead with generated title
- bot offers:
  - `Add Name`
  - `Add Phone`
  - `Archive`

## 13. Manual Lead Creation Inside the Bot

### Goal

Allow the realtor to create a lead fully inside the bot without leaving Telegram.

### Flow

1. tap `Add Lead`
2. select lead type
3. select source
4. enter name
5. enter phone or tap `Skip`
6. choose first reminder preset or tap `No reminder`
7. save

### Validation

- name is required
- phone is optional
- source is required
- status defaults to `New`

### Save Result

After save, show lead card with:

- `Set Reminder`
- `Change Status`
- `Edit`
- `Archive`
- `Back to CRM`

## 14. Lead Editing Inside the Bot

### Goal

Allow direct maintenance of a lead record inside the bot without opening external tools.

### Editable Fields

- `name`
- `phone`
- `lead_type`
- `source`
- `status`
- `next_call_at`

### Edit Entry Point

From the lead card:

- `Edit`

### Edit Menu Buttons

- `Name`
- `Phone`
- `Type`
- `Source`
- `Status`
- `Reminder`
- `Back`

### Editing Rules

- button fields use button selectors
- free-text fields use a short input step
- after each change the bot returns to the refreshed lead card
- no separate save screen for single-field edits

## 15. Lead Card

The lead card must show only essential data:

- Name
- Phone
- Type
- Source
- Status
- Next call
- Last contact

### Lead Card Buttons

- `Set Reminder`
- `Change Status`
- `Mark Called`
- `Edit`
- `Archive`
- `Back`

## 16. Today Screen

### Content Order

1. overdue leads
2. today leads

### List Item Format

- `Anna Petrova - Contacted - Today 17:00`
- `Ivan - New - Overdue`

### Per-Item Actions

- `Done`
- `Snooze`
- `Status`
- `Open`

## 17. Reminder Notification

### Notification Format

Message content:

- `Call reminder`
- lead name
- phone
- current status
- scheduled time

### Reminder Actions

- `Call Done`
- `+1 hour`
- `Tomorrow`
- `Change Status`
- `Open Lead`

## 18. Button Map

## CRM Root

- `crm:menu`
- `crm:add`
- `crm:add_forwarded`
- `crm:today`
- `crm:list`
- `crm:archived`

## Lead Actions

- `lead:open:{lead_id}`
- `lead:edit:{lead_id}`
- `lead:archive:{lead_id}`
- `lead:restore:{lead_id}`
- `lead:status:{lead_id}`
- `lead:mark_called:{lead_id}`
- `lead:reminder:{lead_id}`

## Reminder Actions

- `reminder:set:{lead_id}:{preset}`
- `reminder:done:{lead_id}`
- `reminder:snooze:{lead_id}:{preset}`
- `reminder:remove:{lead_id}`

## Field Editing

- `edit:name:{lead_id}`
- `edit:phone:{lead_id}`
- `edit:type:{lead_id}:{value}`
- `edit:source:{lead_id}:{value}`
- `edit:status:{lead_id}:{value}`

## 19. Technical Implementation

## Storage

Use SQLite for MVP.

Reason:

- minimal operational overhead
- no external service dependency
- enough for a single-bot CRM MVP

## Suggested Tables

### `leads`

- `id` INTEGER PRIMARY KEY
- `name` TEXT NOT NULL
- `phone` TEXT NULL
- `telegram_user_id` TEXT NULL
- `telegram_username` TEXT NULL
- `telegram_display_name` TEXT NULL
- `lead_type` TEXT NOT NULL
- `source` TEXT NOT NULL
- `status` TEXT NOT NULL
- `next_call_at` DATETIME NULL
- `last_contact_at` DATETIME NULL
- `capture_method` TEXT NOT NULL
- `is_archived` INTEGER NOT NULL DEFAULT 0
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

### `lead_reminders`

- `id` INTEGER PRIMARY KEY
- `lead_id` INTEGER NOT NULL
- `scheduled_at` DATETIME NOT NULL
- `is_active` INTEGER NOT NULL DEFAULT 1
- `sent_at` DATETIME NULL
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

Constraint:

- max one active reminder per lead

## Suggested Python Structure

- `handlers/calculator.py`
- `handlers/crm.py`
- `handlers/reminders.py`
- `services/lead_service.py`
- `services/reminder_service.py`
- `repositories/lead_repository.py`
- `repositories/reminder_repository.py`
- `keyboards/crm.py`
- `models/lead.py`

## Telegram Integration

Required additions:

- `CallbackQueryHandler`
- lightweight in-bot state via `context.user_data`
- scheduled reminder jobs

Avoid a heavy conversation tree. Use short state steps plus callback-driven navigation.

## 20. Acceptance Criteria

The feature is accepted when:

1. a forwarded client message can create a lead from inside the bot
2. the client chat receives no CRM-visible side effect
3. a manual lead can be created inside the bot
4. a lead can be edited inside the bot
5. status can be changed in no more than 2 taps
6. a reminder can be set in no more than 2 taps
7. reminder notification includes direct action buttons
8. today and overdue screens work correctly
9. only one active reminder exists per lead
10. the existing commission calculator still works

## 21. Non-Goals for This Iteration

- full CRM replacement
- advanced segmentation
- AI lead scoring
- automatic parsing of property requirements
- team collaboration and permissions
- invisible inline lead creation in client chat

## 22. Final Product Decision

The MVP must use two lead-entry methods:

1. auto-create from forwarded message
2. manual create inside the bot

The MVP must also support direct in-bot lead editing.

This keeps the product fast, realistic for Telegram, and aligned with the current architecture of the project.
