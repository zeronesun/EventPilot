/**
 * EventPilot Pinia Stores - Unified Export
 * All state management modules are exported from here
 */

export { useAuthStore } from './auth';
export { useEventsStore } from './events';
export { useTasksStore } from './tasks';
export { useProfilesStore } from './profiles';
export { useWebSocketStore } from './websocket';
export { useNotificationsStore } from './notifications';

// Export types for convenience
export type { Event } from './events';
