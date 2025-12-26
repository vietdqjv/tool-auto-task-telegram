# Project Roadmap

## Overview
This document outlines the strategic direction, key milestones, and planned features for the Telegram Bot project. It serves as a high-level guide for all stakeholders.

## Current Status
- **Overall Project Status**: In Progress
- **Last Updated**: 2025-12-26

## Major Releases & Milestones

### Q4 2025 - Initial Release & Core Features (Target: December 2025)
- **Status**: Completed
- **Key Features**:
    - Telegram Bot Infrastructure
    - Basic Task Management
    - Group Task Management
    - BYOK Model Support
    - SSH/PTY Support
    - WebSocket Communication

## Feature Development Tracking

### Group Task Management for Telegram Bot
- **Status**: Completed (2025-12-25)
- **Description**: Admin assign tasks to group members with reminders, deadlines, and completion workflow.
- **Phases**:
    - Phase 01 (Foundation): Completed on 2025-12-25
    - Phase 02 (Services): Completed on 2025-12-25
    - Phase 03 (Scheduler): Completed on 2025-12-25
    - Phase 04 (Bot UI): Completed on 2025-12-25
    - Phase 05 (Handlers): Completed on 2025-12-25

### Group Chaos Hybrid Solution
- **Status**: In Progress
- **Description**: Fix bot confusion in groups via reply patterns, DM deep-linking FSM, and rate limiting.
- **Phases**:
    - Phase 1 - Reply Pattern Refactor: Completed on 2025-12-26

## Changelog
- **2025-12-26**: Phase 1 of Group Chaos Hybrid Solution completed: Reply Pattern Refactor.
- **2025-12-25**: Group Task Management feature completed and deployed.
    - Added database foundation and configuration for group tasks.
    - Implemented `working-hours.py` and `group-task-service.py`.
    - Developed `group-task-reminder.py` for recurring reminders, overdue detection, and cleanup.
    - Designed `group-task-keyboards.py` and `group-task-fsm.py` for bot UI.
    - Added Rate Limiting Bypass for admin users and `/assign` command for group task creation.
    - Integrated `group-tasks.py` handlers for all group task commands.
