# Smart Intent App - Project Structure

## Overview
A Streamlit-based application with an intelligent intent-based routing system, advanced analytics, caching, and performance monitoring.

## Architecture

### Core Components

#### 1. **Smart Intent Router** (`app.py`)
- **Intent Enum**: Defines all available modes (CHAT, BUILDER, FIXER, etc.)
- **IntentConfig**: Dataclass for intent configuration
- **SmartIntentRouter**: Main routing engine with:
  - Intent detection and validation
  - Permission checking (auth & admin)
  - Performance monitoring
  - Analytics tracking
  - Cache management

#### 2. **Services** (`services/`)

##### `logger.py`
- Centralized logging with file and console handlers
- Daily log rotation
- Structured logging format

##### `analytics.py`
- Event tracking system
- Persistence to JSON Lines format
- Statistics aggregation
- Intent-specific metrics

##### `cache.py`
- In-memory caching with TTL
- LRU eviction policy
- Cache statistics

##### `performance.py`
- Execution time tracking
- Memory usage monitoring
- CPU tracking
- Performance summaries

##### `state.py`
- Session state initialization
- User authentication state
- UI state management

#### 3. **Components** (`components/`)

##### `sidebar.py`
- Intent selection radio buttons
- User info display
- Settings toggles (Debug, Analytics)
- Quick actions (Refresh, Logout)

##### `header.py`
- App title and branding
- Current mode display
- Timestamp

##### `performance_monitor.py`
- Performance metrics dashboard
- Detailed component metrics
- Analytics summary view

#### 4. **Configuration** (`config/`)

##### `ui.py`
- Streamlit page configuration
- Custom CSS styling

##### `settings.py`
- Environment-based settings
- Configuration dataclass

##### `intent_config.yaml`
- Intent definitions
- Feature flags per intent
- Cache configuration

## Data Flow
