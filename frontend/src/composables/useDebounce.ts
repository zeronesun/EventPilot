import { ref, watch, type Ref } from 'vue';

interface UseDebounceOptions {
  delay?: number;
  immediate?: boolean;
  onTrigger?: () => void;
}

/**
 * 防抖Composable
 * 延迟执行函数，直到指定时间内没有再次调用
 */
export function useDebounce<T>(source: Ref<T> | T, delay: number = 300): Ref<T> {
  const debouncedValue: Ref<T> = ref(source as T) as Ref<T>;
  let timeout: NodeJS.Timeout | null = null;

  if (typeof source === 'object' && 'value' in source) {
    watch(
      source,
      (newValue: T) => {
        if (timeout) {
          clearTimeout(timeout);
        }

        timeout = setTimeout(() => {
          debouncedValue.value = newValue;
          timeout = null;
        }, delay);
      },
      { immediate: true }
    );
  } else {
    debouncedValue.value = source as T;
  }

  return debouncedValue;
}

/**
 * 防抖函数Composable
 * 返回一个防抖函数，可以用于事件处理
 */
export function useDebounceFn<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300,
  options: UseDebounceOptions = {}
): {
  debouncedFn: T;
  cancel: () => void;
  flush: () => void;
  pending: () => boolean;
} {
  const { immediate = false, onTrigger } = options;
  let timeout: NodeJS.Timeout | null = null;
  let lastArgs: any[] = [];
  let lastThis: any = null;
  let result: any = null;

  const debouncedFn = function (this: any, ...args: Parameters<T>): ReturnType<T> {
    lastArgs = args;
    lastThis = this;

    if (timeout) {
      clearTimeout(timeout);
    }

    if (immediate && !timeout) {
      result = fn.apply(this, args);
      if (onTrigger) {
        onTrigger();
      }
    }

    timeout = setTimeout(() => {
      if (!immediate) {
        result = fn.apply(lastThis, lastArgs);
        if (onTrigger) {
          onTrigger();
        }
      }
      timeout = null;
    }, delay);

    return result;
  } as T;

  /**
   * 取消待执行的防抖调用
   */
  const cancel = (): void => {
    if (timeout) {
      clearTimeout(timeout);
      timeout = null;
    }
  };

  /**
   * 立即执行防抖函数
   */
  const flush = (): void => {
    if (timeout) {
      clearTimeout(timeout);
      result = fn.apply(lastThis, lastArgs);
      if (onTrigger) {
        onTrigger();
      }
      timeout = null;
    }
  };

  /**
   * 检查是否有待执行的调用
   */
  const pending = (): boolean => {
    return timeout !== null;
  };

  return {
    debouncedFn,
    cancel,
    flush,
    pending,
  };
}

/**
 * 节流Composable
 * 限制函数执行频率，确保在指定时间内最多执行一次
 */
export function useThrottle<T>(source: Ref<T> | T, interval: number = 300): Ref<T> {
  const throttledValue: Ref<T> = ref(source as T) as Ref<T>;
  let lastTime = 0;
  let timeout: NodeJS.Timeout | null = null;

  if (typeof source === 'object' && 'value' in source) {
    watch(
      source,
      (newValue: T) => {
        const now = Date.now();
        const remaining = interval - (now - lastTime);

        if (remaining <= 0) {
          lastTime = now;
          throttledValue.value = newValue;
        } else if (timeout) {
          clearTimeout(timeout);
          timeout = setTimeout(() => {
            lastTime = Date.now();
            throttledValue.value = newValue;
            timeout = null;
          }, remaining);
        }
      },
      { immediate: true }
    );
  } else {
    throttledValue.value = source as T;
  }

  return throttledValue;
}

/**
 * 节流函数Composable
 * 返回一个节流函数，可以用于事件处理
 */
export function useThrottleFn<T extends (...args: any[]) => any>(
  fn: T,
  interval: number = 300
): {
  throttledFn: T;
  cancel: () => void;
  pending: () => boolean;
} {
  let timeout: NodeJS.Timeout | null = null;
  let lastArgs: any[] = [];
  let lastThis: any = null;
  let result: any = null;

  const throttledFn = function (this: any, ...args: Parameters<T>): ReturnType<T> {
    if (timeout) {
      lastArgs = args;
      lastThis = this;
      return result;
    }

    result = fn.apply(this, args);

    timeout = setTimeout(() => {
      if (lastArgs.length > 0) {
        result = fn.apply(lastThis, lastArgs);
        lastArgs = [];
        lastThis = null;
      }
      timeout = null;
    }, interval);

    return result;
  } as T;

  /**
   * 取消待执行的节流调用
   */
  const cancel = (): void => {
    if (timeout) {
      clearTimeout(timeout);
      timeout = null;
      lastArgs = [];
      lastThis = null;
    }
  };

  /**
   * 检查是否有待执行的调用
   */
  const pending = (): boolean => {
    return timeout !== null;
  };

  return {
    throttledFn,
    cancel,
    pending,
  };
}

/**
 * 搜索防抖Composable
 * 专门用于搜索输入的防抖
 */
export function useSearchDebounce(
  initialQuery: string = '',
  delay: number = 400
): {
  query: Ref<string>;
  debouncedQuery: Ref<string>;
  isSearching: Ref<boolean>;
  search: (value: string) => void;
  clear: () => void;
} {
  const query = ref(initialQuery);
  const debouncedQuery = ref(initialQuery);
  const isSearching = ref(false);

  const { debouncedFn, cancel, pending } = useDebounceFn(
    (value: string) => {
      debouncedQuery.value = value;
      isSearching.value = false;
    },
    delay,
    {
      onTrigger: () => {
        if (!pending()) {
          isSearching.value = true;
        }
      },
    }
  );

  /**
   * 执行搜索
   */
  const search = (value: string): void => {
    query.value = value;
    if (value !== debouncedQuery.value) {
      isSearching.value = true;
      debouncedFn(value);
    }
  };

  /**
   * 清除搜索
   */
  const clear = (): void => {
    cancel();
    query.value = '';
    debouncedQuery.value = '';
    isSearching.value = false;
  };

  return {
    query,
    debouncedQuery,
    isSearching,
    search,
    clear,
  };
}

/**
 * 防抖搜索Hook示例
 *
 * @example
 * const { debouncedQuery, search, isSearching, clear } = useSearchDebounce();
 *
 * watch(debouncedQuery, (newQuery) => {
 *   if (newQuery) {
 *     performSearch(newQuery);
 *   }
 * });
 *
 * // 在模板中使用
 * <input
 *   v-model="query"
 *   @input="search(query)"
 *   placeholder="搜索..."
 * />
 */

export default useDebounce;
