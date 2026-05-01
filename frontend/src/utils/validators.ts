/**
 * 表单验证工具
 * 提供常用的验证器和表单验证组合器
 */

export type ValidatorFunction = (value: any) => string | null

export interface ValidatorConfig {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  customValidator?: ValidatorFunction
  message?: string
}

export interface ValidationRule {
  validator: ValidatorFunction
  message?: string
}

export interface ValidationResult {
  valid: boolean
  errors: string[]
}

/**
 * 基础验证器
 */
export class Validators {
  /**
   * 必填验证
   */
  static required(errorMessage?: string): ValidatorFunction {
    return (value: any): string | null => {
      if (value === null || value === undefined || value === '') {
        return errorMessage || '此字段为必填项'
      }
      if (typeof value === 'string' && value.trim() === '') {
        return errorMessage || '此字段为必填项'
      }
      return null
    }
  }

  /**
   * 最小长度验证
   */
  static minLength(min: number, errorMessage?: string): ValidatorFunction {
    return (value: any): string | null => {
      if (!value) return null
      if (typeof value !== 'string') {
        return '值必须是字符串'
      }
      if (value.length < min) {
        return errorMessage || `最少需要 ${min} 个字符`
      }
      return null
    }
  }

  /**
   * 最大长度验证
   */
  static maxLength(max: number, errorMessage?: string): ValidatorFunction {
    return (value: any): string | null => {
      if (!value) return null
      if (typeof value !== 'string') {
        return '值必须是字符串'
      }
      if (value.length > max) {
        return errorMessage || `最多允许 ${max} 个字符`
      }
      return null
    }
  }

  /**
   * 邮箱验证
   */
  static email(errorMessage?: string): ValidatorFunction {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return (value: any): string | null => {
      if (!value) return null
      if (typeof value !== 'string') {
        return '值必须是字符串'
      }
      if (!emailRegex.test(value)) {
        return errorMessage || '邮箱格式不正确'
      }
      return null
    }
  }

  /**
   * 手机号验证（中国）
   */
  static phone(errorMessage?: string): ValidatorFunction {
    const phoneRegex = /^1[3-9]\d{9}$/
    return (value: any): string | null => {
      if (!value) return null
      if (typeof value !== 'string') {
        return '值必须是字符串'
      }
      if (!phoneRegex.test(value)) {
        return errorMessage || '手机号格式不正确'
      }
      return null
    }
  }

  /**
   * URL验证
   */
  static url(errorMessage?: string): ValidatorFunction {
    try {
      const urlRegex = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/
      return (value: any): string | null => {
        if (!value) return null
        if (typeof value !== 'string') {
          return '值必须是字符串'
        }
        if (!urlRegex.test(value)) {
          return errorMessage || 'URL格式不正确'
        }
        return null
      }
    } catch {
      // Fallback for environments where URL constructor is not available
      const urlRegex = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/
      return (value: any): string | null => {
        if (!value) return null
        if (!urlRegex.test(value)) {
          return errorMessage || 'URL格式不正确'
        }
        return null
      }
    }
  }

  /**
   * 数字验证
   */
  static number(errorMessage?: string): ValidatorFunction {
    return (value: any): string | null => {
      if (!value) return null
      if (typeof value !== 'number' && typeof value !== 'string') {
        return '值必须是数字'
      }
      if (isNaN(Number(value))) {
        return errorMessage || '请输入有效数字'
      }
      return null
    }
  }

  /**
   * 整数验证
   */
  static integer(errorMessage?: string): ValidatorFunction {
    return (value: any): string | null => {
      if (value === '' || value === null || value === undefined) return null
      const num = Number(value)
      if (isNaN(num) || !Number.isInteger(num)) {
        return errorMessage || '请输入整数'
      }
      return null
    }
  }

  /**
   * 最小值验证
   */
  static min(min: number, errorMessage?: string): ValidatorFunction {
    return (value: any): string | null => {
      if (value === '' || value === null || value === undefined) return null
      const num = Number(value)
      if (isNaN(num) || num < min) {
        return errorMessage || `值不能小于 ${min}`
      }
      return null
    }
  }

  /**
   * 最大值验证
   */
  static max(max: number, errorMessage?: string): ValidatorFunction {
    return (value: any): string | null => {
      if (value === '' || value === null || value === undefined) return null
      const num = Number(value)
      if (isNaN(num) || num > max) {
        return errorMessage || `值不能大于 ${max}`
      }
      return null
    }
  }

  /**
   * 正则表达式验证
   */
  static pattern(regex: RegExp, errorMessage?: string): ValidatorFunction {
    return (value: any): string | null => {
      if (!value) return null
      if (typeof value !== 'string') {
        return '值必须是字符串'
      }
      if (!regex.test(value)) {
        return errorMessage || '格式不正确'
      }
      return null
    }
  }

  /**
   * 密码强度验证
   */
  static password(minLength = 6, errorMessage?: string): ValidatorFunction {
    return (value: any): string | null => {
      if (!value) return null
      if (typeof value !== 'string') {
        return '密码必须是字符串'
      }
      if (value.length < minLength) {
        return errorMessage || `密码长度至少为 ${minLength} 位`
      }
      return null
    }
  }

  /**
   * 密码确认验证
   */
  static confirmPassword(passwordField: string, errorMessage?: string): ValidatorFunction {
    return (value: any, formData?: any): string | null => {
      if (!value) return null
      if (formData && formData[passwordField] !== value) {
        return errorMessage || '两次密码不一致'
      }
      return null
    }
  }

  /**
   * 自定义验证器
   */
  static custom(validator: ValidatorFunction): ValidatorFunction {
    return validator
  }

  /**
   * 组合多个验证器（所有验证器都必须通过）
   */
  static compose(...validators: ValidatorFunction[]): ValidatorFunction {
    return (value: any, formData?: any): string | null => {
      for (const validator of validators) {
        const error = validator(value, formData)
        if (error) {
          return error
        }
      }
      return null
    }
  }
}

/**
 * 表单验证器类
 */
export class FormValidator {
  private rules: Map<string, ValidatorFunction[]> = new Map()
  private formData: any = {}
  private errors: Map<string, string[]> = new Map()

  /**
   * 添加验证规则
   */
  addRule(field: string, validators: ValidatorFunction | ValidatorFunction[]): void {
    const fieldValidators = Array.isArray(validators) ? validators : [validators]
    if (!this.rules.has(field)) {
      this.rules.set(field, [])
    }
    this.rules.get(field)!.push(...fieldValidators)
  }

  /**
   * 批量添加验证规则
   */
  addRules(field: string, validators: ValidatorFunction | ValidatorFunction[]): void {
    return this.addRule(field, validators)
  }

  /**
   * 设置规则配置（便捷方法）
   */
  setRules(field: string, config: ValidatorConfig): void {
    const validators: ValidatorFunction[] = []

    if (config.required) {
      validators.push(Validators.required(config.message))
    }

    if (config.minLength) {
      validators.push(Validators.minLength(config.minLength, config.message))
    }

    if (config.maxLength) {
      validators.push(Validators.maxLength(config.maxLength, config.message))
    }

    if (config.pattern) {
      validators.push(Validators.pattern(config.pattern, config.message))
    }

    if (config.customValidator) {
      validators.push(config.customValidator)
    }

    this.addRule(field, validators)
  }

  /**
   * 验证单个字段
   */
  validateField(field: string): boolean {
    const validators = this.rules.get(field)
    if (!validators) {
      return true
    }

    const value = this.formData[field]
    const fieldErrors: string[] = []

    for (const validator of validators) {
      const error = validator(value, this.formData)
      if (error) {
        fieldErrors.push(error)
      }
    }

    if (fieldErrors.length > 0) {
      this.errors.set(field, fieldErrors)
      return false
    } else {
      this.errors.delete(field)
      return true
    }
  }

  /**
   * 验证所有字段
   */
  validateAll(): ValidationResult {
    this.errors.clear()

    for (const field of this.rules.keys()) {
      this.validateField(field)
    }

    return this.getValidationResult()
  }

  /**
   * 获取验证结果
   */
  getValidationResult(): ValidationResult {
    const allErrors: string[] = []
    for (const errors of this.errors.values()) {
      allErrors.push(...errors)
    }

    return {
      valid: allErrors.length === 0,
      errors: allErrors,
    }
  }

  /**
   * 获取字段错误
   */
  getFieldErrors(field: string): string[] {
    return this.errors.get(field) || []
  }

  /**
   * 获取第一个字段错误
   */
  getFirstFieldError(field: string): string | null {
    const errors = this.getFieldErrors(field)
    return errors.length > 0 ? errors[0] : null
  }

  /**
   * 检查字段是否有错误
   */
  hasFieldError(field: string): boolean {
    return this.errors.has(field) && this.errors.get(field)!.length > 0
  }

  /**
   * 清除字段错误
   */
  clearFieldError(field: string): void {
    this.errors.delete(field)
  }

  /**
   * 清除所有错误
   */
  clearAllErrors(): void {
    this.errors.clear()
  }

  /**
   * 更新表单数据
   */
  setFormData(data: any): void {
    this.formData = data
  }

  /**
   * 更新单个字段值
   */
  setFieldValue(field: string, value: any): void {
    this.formData[field] = value
  }

  /**
   * 获取表单数据
   */
  getFormData(): any {
    return this.formData
  }

  /**
   * 重置验证器
   */
  reset(): void {
    this.rules.clear()
    this.errors.clear()
    this.formData = {}
  }
}

/**
 * 快捷创建表单验证器
 */
export function createValidator(): FormValidator {
  return new FormValidator()
}

/**
 * 预定义的验证规则集
 */
export const CommonValidationRules = {
  // 用户名
  username: Validators.compose(
    Validators.required('用户名不能为空'),
    Validators.minLength(3, '用户名至少3个字符'),
    Validators.maxLength(20, '用户名最多20个字符'),
    Validators.pattern(/^[a-zA-Z0-9_]+$/, '用户名只能包含字母、数字和下划线')
  ),

  // 邮箱
  email: Validators.compose(
    Validators.required('邮箱不能为空'),
    Validators.email()
  ),

  // 密码
  password: Validators.compose(
    Validators.required('密码不能为空'),
    Validators.password(6, '密码至少6位字符')
  ),

  // 手机号
  phone: Validators.compose(
    Validators.required('手机号不能为空'),
    Validators.phone()
  ),

  // 标题
  title: Validators.compose(
    Validators.required('标题不能为空'),
    Validators.minLength(2, '标题至少2个字符'),
    Validators.maxLength(100, '标题最多100个字符')
  ),
}

export default Validators
