import { ref, computed } from 'vue';
import { useAuthStore } from '@/store';
import { securityConfig } from '@/utils/security';

// 角色定义
export const Roles = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  OPERATOR: 'operator',
  VIEWER: 'viewer',
  GUEST: 'guest'
} as const;

// 权限定义
export const Permissions = {
  // 活动管理
  VIEW_EVENTS: 'view_events',
  CREATE_EVENT: 'create_event',
  EDIT_EVENT: 'edit_event',
  DELETE_EVENT: 'delete_event',
  MANAGE_PARTICIPANTS: 'manage_participants',
  
  // 任务管理
  VIEW_TASKS: 'view_tasks',
  CREATE_TASK: 'create_task',
  EDIT_TASK: 'edit_task',
  DELETE_TASK: 'delete_task',
  ASSIGN_TASK: 'assign_task',
  
  // 文件管理
  VIEW_FILES: 'view_files',
  UPLOAD_FILE: 'upload_file',
  DELETE_FILE: 'delete_file',
  
  // 系统管理
  VIEW_USERS: 'view_users',
  MANAGE_USERS: 'manage_users',
  VIEW_ROLES: 'view_roles',
  MANAGE_ROLES: 'manage_roles',
  MANAGE_SYSTEM: 'manage_system',
  
  // 审计日志
  VIEW_AUDIT_LOG: 'view_audit_log'
} as const;

// 角色权限映射（简化版，与后端保持一致）
const ROLE_PERMISSIONS = {
  [Roles.ADMIN]: new Set<string>(), // 管理员拥有所有权限
  [Roles.MANAGER]: new Set([
    Permissions.VIEW_EVENTS,
    Permissions.CREATE_EVENT,
    Permissions.EDIT_EVENT,
    Permissions.VIEW_TASKS,
    Permissions.CREATE_TASK,
    Permissions.EDIT_TASK,
    Permissions.ASSIGN_TASK,
    Permissions.VIEW_FILES,
    Permissions.UPLOAD_FILE,
    Permissions.VIEW_USERS,
    Permissions.VIEW_ROLES,
    Permissions.VIEW_AUDIT_LOG
  ]),
  [Roles.OPERATOR]: new Set([
    Permissions.VIEW_EVENTS,
    Permissions.VIEW_TASKS,
    Permissions.CREATE_TASK,
    Permissions.EDIT_TASK,
    Permissions.VIEW_FILES,
    Permissions.UPLOAD_FILE,
    Permissions.VIEW_USERS
  ]),
  [Roles.VIEWER]: new Set([
    Permissions.VIEW_EVENTS,
    Permissions.VIEW_TASKS,
    Permissions.VIEW_FILES
  ]),
  [Roles.GUEST]: new Set([
    Permissions.VIEW_EVENTS
  ])
};

export function useAuthorization() {
  const authStore = useAuthStore();
  const currentRoles = ref<string[]>(authStore.user?.roles || [Roles.GUEST]);
  const allPermissions = computed(() => {
    const permissions = new Set<string>();
    
    for (const role of currentRoles.value) {
      const rolePerms = ROLE_PERMISSIONS[role as keyof typeof ROLE_PERMISSIONS];
      if (rolePerms) {
        rolePerms.forEach(perm => permissions.add(perm));
      }
    }
    
    // admin拥有所有权限
    if (currentRoles.value.includes(Roles.ADMIN)) {
      Object.values(Permissions).forEach(perm => permissions.add(perm));
    }
    
    return permissions;
  });
  
  /**
   * 检查用户是否拥有指定权限
   */
  const hasPermission = (permission: string): boolean => {
    if (currentRoles.value.includes(Roles.ADMIN)) {
      return true;
    }
    
    return allPermissions.value.has(permission);
  };
  
  /**
   * 检查用户是否拥有任意一个指定权限
   */
  const hasAnyPermission = (permissions: string[]): boolean => {
    if (currentRoles.value.includes(Roles.ADMIN)) {
      return true;
    }
    
    return permissions.some(perm => allPermissions.value.has(perm));
  };
  
  /**
   * 检查用户是否拥有所有指定权限
   */
  const hasAllPermissions = (permissions: string[]): boolean => {
    if (currentRoles.value.includes(Roles.ADMIN)) {
      return true;
    }
    
    return permissions.every(perm => allPermissions.value.has(perm));
  };
  
  /**
   * 检查用户是否拥有指定角色
   */
  const hasRole = (role: string): boolean => {
    return currentRoles.value.includes(role);
  };
  
  /**
   * 检查用户是否拥有指定角色或更高级别
   */
  const hasRoleOrHigher = (minRole: string): boolean => {
    const roleHierarchy = {
      [Roles.GUEST]: 1,
      [Roles.VIEWER]: 2,
      [Roles.OPERATOR]: 3,
      [Roles.MANAGER]: 4,
      [Roles.ADMIN]: 5
    };
    
    const minLevel = roleHierarchy[minRole as keyof typeof roleHierarchy] || 0;
    
    return currentRoles.value.some(role => {
      const level = roleHierarchy[role as keyof typeof roleHierarchy] || 0;
      return level >= minLevel;
    });
  };
  
  /**
   * 检查是否可以执行指定操作
   */
  const can = (action: string, resourceType?: string): boolean => {
    // 简化版检查，实际可以根据资源ID进行更细粒度的检查
    if (currentRoles.value.includes(Roles.ADMIN)) {
      return true;
    }
    
    const permission = resourceType 
      ? `${action}_${resourceType}` 
      : action;
    
    return allPermissions.value.has(permission);
  };
  
  /**
   * 获取用户所有角色
   */
  const getRoles = (): string[] => {
    return [...currentRoles.value];
  };
  
  /**
   * 检查是否是管理员
   */
  const isAdmin = computed(() => hasRole(Roles.ADMIN));
  
  /**
   * 检查是否是经理
   */
  const isManager = computed(() => hasRole(Roles.MANAGER));
  
  /**
   * 检查是否是操作员
   */
  const isOperator = computed(() => hasRole(Roles.OPERATOR));
  
  /**
   * 检查是否是查看者
   */
  const isViewer = computed(() => hasRole(Roles.VIEWER));
  
  /**
   * 检查是否是访客
   */
  const isGuest = computed(() => hasRole(Roles.GUEST));
  
  /**
   * 过滤可访问的菜单项
   */
  const filterMenu = (menuItems: any[]): any[] => {
    return menuItems.filter(item => {
      if (!item.permission) {
        return true;
      }
      
      if (typeof item.permission === 'string') {
        return hasPermission(item.permission);
      }
      
      if (Array.isArray(item.permission)) {
        return hasAnyPermission(item.permission);
      }
      
      return false;
    });
  };
  
  /**
   * 过滤可显示的操作按钮
   */
  const filterActions = (actions: any[]): any[] => {
    return actions.filter(action => {
      if (!action.permission) {
        return true;
      }
      
      return hasPermission(action.permission);
    });
  };
  
  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasRoleOrHigher,
    can,
    getRoles,
    isAdmin,
    isManager,
    isOperator,
    isViewer,
    isGuest,
    allPermissions,
    currentRoles,
    filterMenu,
    filterActions
  };
}

// Vue指令
export const permissionDirective = {
  mounted(el: HTMLElement, binding: any) {
    const { value } = binding;
    
    if (value && !checkPermission(value)) {
      // 移除元素
      el.parentNode?.removeChild(el);
    }
  },
  updated(el: HTMLElement, binding: any) {
    const { value } = binding;
    
    if (value && !checkPermission(value)) {
      el.parentNode?.removeChild(el);
    }
  }
};

function checkPermission(value: string | string[]): boolean {
  const { hasPermission, hasAnyPermission } = useAuthorization();
  
  if (typeof value === 'string') {
    return hasPermission(value);
  }
  
  if (Array.isArray(value)) {
    return hasAnyPermission(value);
  }
  
  return false;
}

export default useAuthorization;